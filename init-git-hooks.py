#!/usr/bin/env python
# Disable pylint filename and missing module member complaints.
# pylint: disable=C0103,E1101
""" Initializes git hooks for current project folder. """

import commands
import requests
import shutil
import subprocess

cpplint_url = 'https://raw.githubusercontent.com/google/styleguide/cf4071cf5de83c006b08bf8f62e1450d17a9ce07/cpplint/cpplint.py'
pylint_url = 'https://raw.githubusercontent.com/vinitkumar/googlecl/6dc04b489dba709c53d2f4944473709617506589/googlecl-pylint.rc'


def download_file_from_url(url, file_path):
  request = requests.get(url, verify=False, stream=True)
  request.raw.decode_content = True
  with open(file_path, 'w') as downloaded_file:
    shutil.copyfileobj(request.raw, downloaded_file)


def main():
  """ Download cpplint.py and pylint.py and installs the git hooks"""

  # Download linter files.
  download_file_from_url(cpplint_url, "cpplint.py")
  download_file_from_url(pylint_url, "pylint.rc")

  # Get git root folder of parent repository.
  get_repo_call = subprocess.Popen(['git rev-parse --show-toplevel'],
                                   cwd='../', stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
  repo_root, return_code = get_repo_call.comunicate()
  assert return_code == 0

  print("Found parent git repo root folder: {}".format(repo_root))

  # Copy git hooks.
  cp_params = repo_root + "/linter/pre-commit " + repo_root + "/.git/hooks/"
  assert subprocess.call("cp " + cp_params, shell=True) == 0


if __name__ == "__main__":
  main()
