#!/usr/bin/env python
""" Simple git pre-commit script for executing some linters. """

import commands
import imp
import re
import pylint.lint


def check_cpp_lint(repo_root, staged_files):
  """Runs Google's cpplint on all C++ files staged for commit,"""
  cpplint = imp.load_source('cpplint', repo_root + "/devtools/cpplint.py")
  for changed_file in staged_files:
    if re.search(r'\.cc$', changed_file):
      changed_file = repo_root + "/" + changed_file
      cpplint.ProcessFile(changed_file, 0)
    elif re.search(r'\.h$', changed_file):
      # Change global _root variable for desired behaviour of
      # cpplint's header guard. Without this change the header include
      # guard would have to look like: INCLUDE_REFILL_SUBPATH_HEADER_H_.
      # We want it to look like: REFILL_SUBPATH_HEADER_H_
      cpplint._root = "include"  # pylint: disable=W0212
      changed_file = repo_root + "/" + changed_file
      cpplint.ProcessFile(changed_file, 0)
      cpplint._root = None  # pylint: disable=W0212

  if cpplint._cpplint_state.error_count:  # pylint: disable=W0212
    print 'Aborting commit: cpplint is unhappy.'
    exit(cpplint._cpplint_state.error_count)  # pylint: disable=W0212


def check_modified_after_staging(staged_files):
  """Checks if one of the staged files was modified after staging."""
  _, unstaged_changes = commands.getstatusoutput('git diff --name-only')
  files_changed = unstaged_changes.split("\n")
  files_changed = filter(None, files_changed)

  staged_files_changed = 0

  for changed_file in files_changed:
    if changed_file in staged_files:
      print changed_file + " modified after staging"
      staged_files_changed = 1

  if staged_files_changed:
    print "Aborting commit: Staged files modified after staging."
    exit(1)


def check_python_lint(repo_root, staged_files):
  """Runs pylint on all python scripts staged for commit."""

  # Dummy class for pylint related IO.
  class WritableObject(object):
    "dummy output stream for pylint"

    def __init__(self):
      self.content = []

    def write(self, input_str):
      "dummy write"
      self.content.append(input_str)

    def read(self):
      "dummy read"
      return self.content

  # Parse each pylint output line individualy and searches
  # for errors in the code.
  pylint_errors = []
  for changed_file in staged_files:
    if re.search(r'\.py$', changed_file):

      print "Running pylint on " + repo_root + "/" + changed_file
      pylint_output = WritableObject()
      pylint_args = ["--rcfile=" + repo_root + "/devtools/pylint.rc",
                     "-rn",
                     repo_root + "/" + changed_file]
      from pylint.reporters.text import TextReporter
      pylint.lint.Run(pylint_args,
                      reporter=TextReporter(pylint_output),
                      exit=False)

      for output_line in pylint_output.read():
        if re.search(r'^(E|C|W):', output_line):
          print changed_file + ": " + output_line
          pylint_errors.append(output_line)

  if len(pylint_errors) > 0:
    print "Pylint found errors. Terminating."
    exit(len(pylint_errors))


def main():
  """ Checks for staged files and executes cpplint on them. """
  _, output = commands.getstatusoutput('git diff --staged --name-only')

  _, repo_root = commands.getstatusoutput('git rev-parse --show-toplevel')

  staged_files = output.split("\n")

  # Do not allow commiting files that were modified after staging. This
  # avoids problems such as forgetting to stage fixes of cpplint complaints.
  check_modified_after_staging(staged_files)

  # Use Google's C++ linter to check for compliance with Google style guide.
  check_cpp_lint(repo_root, staged_files)

  # Use pylint to check for comimpliance with Tensofrflow python style guide.
  check_python_lint(repo_root, staged_files)


if __name__ == "__main__":
  main()
