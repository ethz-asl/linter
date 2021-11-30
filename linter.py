#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Disable pylint invalid module name complaint.
# pylint : disable = C0103
""" Pre-commit script for invoking linters and auto-formatters."""

import datetime
import imp
import os
import re
import subprocess
import distutils
import sys

from io import StringIO 
import pylint.lint
import yaml

# Linter config.
DEFAULT_CONFIG = {
    # Enable code checks and formatting by default.
    'use_clangformat': True,
    'use_cpplint': True,
    'use_yapf': True,
    'use_pylint': True,
    # Block commits that don't pass by default
    'block_commits': True,
    # Check all staged files by default.
    'whitelist': [],
    # Prevents pylint from printing the config XX times.
    'filter_pylint_stderr': True
}

CLANG_FORMAT_DIFF_EXECUTABLE_VERSIONS = [
    "clang-format-diff", "clang-format-diff-6.0", "clang-format-diff-5.0",
    "clang-format-diff-4.0", "clang-format-diff-3.9", "clang-format-diff-3.8"
]

CLANG_FORMAT_EXECUTABLE_VERSIONS = [
    "clang-format", "clang-format-6.0", "clang-format-5.0", "clang-format-4.0",
    "clang-format-3.9", "clang-format-3.8"
]

YAPF_FORMAT_EXECUTABLE = "yapf"

# Files containing these in name or path will not be checked by get_all_files()
ALL_FILES_BLACKLISTED_NAMES = ['cmake-build-debug', '3rd_party', 'third_party']

CPP_SUFFIXES = ['.cpp', '.cc', '.cu', '.cuh', '.h', '.hpp', '.hxx']


def get_user_confirmation(default=False):
    """Requests confirmation string from user"""
    sys.stdin = open('/dev/tty')
    while True:
        resp = input()
        try:
            if resp == '':
                return default
            elif distutils.util.strtobool(resp):
                return True
            else:
                return False
        except ValueError:
            print('{} is not a valid response.'.format(resp))
            print('Please answer with y(es) or n(o)')


def read_linter_config(filename):
    """Parses yaml config file."""

    config = DEFAULT_CONFIG
    with open(filename, 'r') as ymlfile:
        parsed_config = yaml.load(ymlfile)
    for key in config.keys():
        if key in parsed_config.keys():
            config[key] = parsed_config[key]
    return config


def run_command_in_folder(command, folder):
    """Run a bash command in a specific folder."""
    run_command = subprocess.Popen(command,
                                   shell=True,
                                   cwd=folder,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE)
    stdout, _ = run_command.communicate()
    command_output = stdout.decode("utf-8").rstrip()
    return command_output


def get_number_of_commits(some_folder_in_root_repo='./'):
    command = (
        "git shortlog -s -n --all --author=\"$(git config " +
        "--get user.email)\" | grep -o '[0-9]\+' |  " +  # pylint: disable=W1401
        "awk '{s+=$1} END {print s}'")
    num_commits = run_command_in_folder(command, some_folder_in_root_repo)
    if not num_commits:
        num_commits = "0"
    return num_commits


def get_staged_files(some_folder_in_root_repo='./'):
    """Get all staged files from git."""
    output = run_command_in_folder("git diff --staged --name-only",
                                   some_folder_in_root_repo)
    if not output:
        return []
    else:
        return output.split("\n")


def get_unstaged_files(some_folder_in_root_repo='./'):
    """Get all unstaged files from git."""
    output = run_command_in_folder("git diff --name-only",
                                   some_folder_in_root_repo)
    return output.split("\n")


def get_all_files(repo_root):
    """Get all files from in this repo."""
    output = []

    for root, _, files in os.walk(repo_root):
        for f in files:
            if f.lower().endswith(tuple(CPP_SUFFIXES + ['.py'])):
                full_name = os.path.join(root, f)[len(repo_root) + 1:]
                if not any(n in full_name
                           for n in ALL_FILES_BLACKLISTED_NAMES):
                    output.append(full_name)

    return output


def check_cpp_lint(staged_files, cpplint_file, ascii_art, repo_root):
    """Runs Google's cpplint on all C++ files staged for commit,
    return success and number of errors"""
    cpplint = imp.load_source('cpplint', cpplint_file)
    cpplint._cpplint_state.SetFilters('-legal/copyright,-build/c++17')  # pylint: disable=W0212

    # Prevent cpplint from writing to stdout directly, instead
    # the errors will be stored in pplint.output as (line, message) tuples.
    cpplint.print_stdout = False

    total_error_count = 0
    for changed_file in staged_files:
        if not os.path.isfile(changed_file):
            continue
        if changed_file.lower().endswith(tuple(CPP_SUFFIXES)):
            # Search iteratively for the root of the catkin package.
            package_root = ''
            search_dir = os.path.dirname(os.path.abspath(changed_file))
            found_package_root = False
            MAX_DEPTH_OF_FILES = 100
            for _ in range(1, MAX_DEPTH_OF_FILES):
                if os.path.isfile(search_dir + '/package.xml'):
                    package_root = search_dir
                    found_package_root = True
                    break
                # Stop if the root of the git repo is reached.
                if os.path.isdir(search_dir + '/.git'):
                    break
                search_dir = os.path.dirname(search_dir)
            assert found_package_root, ("Could not find the root of the "
                                        "catkin package that contains: "
                                        "{}".format(changed_file))

            # Get relative path to repository root.
            if os.path.isfile(os.path.join(repo_root, '.git')):
                # Repo is a submodule, look for parent git repository containing
                # this submodule.
                search_path = repo_root
                found_to_level_git_repo = False
                for _ in range(10):
                    search_path = os.path.dirname(repo_root)
                    if os.path.isdir(os.path.join(search_path, '.git')):
                        found_to_level_git_repo = True
                        break

                assert found_to_level_git_repo
                repo_root = search_path

            common_prefix = os.path.commonprefix(
                [os.path.abspath(repo_root),
                 os.path.abspath(package_root)])
            package_root = os.path.relpath(package_root, common_prefix)

            # The package root needs to be relative to the (top-level) repo
            # root. Otherwise the header guard logic will fail!
            cpplint._root = package_root + '/include'  # pylint: disable=W0212

            # Reset error count and messages:
            cpplint.output = []
            cpplint._cpplint_state.ResetErrorCounts()  # pylint: disable=W0212
            v_level = cpplint._cpplint_state.verbose_level  # pylint: disable=W0212

            cpplint.ProcessFile(changed_file, v_level)

            error_count = cpplint._cpplint_state.error_count  # pylint: disable=W0212
            if error_count > 0:
                total_error_count += error_count

                print("-" * 80)
                name_to_print = changed_file
                if name_to_print[:len(repo_root)] == repo_root:
                    name_to_print = changed_file[len(repo_root) + 1:]

                print("Found {} errors in : {}".format(error_count,
                                                       name_to_print))
                print("-" * 80)
                for line in cpplint.output:
                    assert len(line) == 2
                    print("line {: >4}:\t {}".format(line[0], line[1]))

    if total_error_count > 0:
        print("=" * 80)
        print("Found {} cpplint errors".format(total_error_count))
        print("=" * 80)

        if total_error_count > 50:
            print(ascii_art.AsciiArt.cthulhu)
        elif total_error_count > 20:
            print(ascii_art.AsciiArt.tiger)
        return False, total_error_count
    else:
        return True, 0


def check_modified_after_staging(staged_files):
    """Checks if one of the staged files was modified after staging."""
    files_changed = get_unstaged_files()
    files_changed = filter(None, files_changed)

    staged_files_changed = 0

    staged_files_changed_list = []

    is_first = True
    for changed_file in files_changed:
        if changed_file in staged_files:

            if is_first:
                print("=" * 80)
                is_first = False

            print("\'{}\' was modified after staging".format(changed_file))
            staged_files_changed_list.append(changed_file)
            staged_files_changed += 1

    if staged_files_changed > 0:
        print("-" * 80)
        print("Found {} files that have been changed after staging".format(
            staged_files_changed))
        print("=" * 80)

    return staged_files_changed_list


def check_commit_against_master(repo_root):
    """Check if the current commit is intended to for the master branch."""
    current_branch = run_command_in_folder(
        "git branch | grep \"*\" | sed \"s/* //\"", repo_root)
    print("\nCurrent_branch: {}\n".format(current_branch))
    return current_branch == "master"


def check_if_merge_commit(repo_root):
    """Check if the current commit is a merge commit."""
    merge_msg_file_path = repo_root + "/.git/MERGE_MSG"
    return os.path.isfile(merge_msg_file_path)


def find_clang_format_diff_executable():
    for executable in CLANG_FORMAT_DIFF_EXECUTABLE_VERSIONS:
        if subprocess.call("type " + executable,
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE) == 0:
            return executable

    print("ERROR: clang-format-diff is not installed!")
    exit(1)


def find_clang_format_executable():
    for executable in CLANG_FORMAT_EXECUTABLE_VERSIONS:
        if subprocess.call("type " + executable,
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE) == 0:
            return executable

    print("ERROR: clang-format is not installed!")
    exit(1)


def run_clang_format(repo_root, staged_files, list_of_changed_staged_files):
    """Runs clang format on all cpp files staged for commit."""

    clang_format_path = ("/tmp/" +
                         os.path.basename(os.path.normpath(repo_root)) + "_" +
                         datetime.datetime.now().isoformat() + ".clang.patch")

    clang_format_diff_executable = find_clang_format_diff_executable()

    run_command_in_folder(
        "git diff -U0 --cached | " + clang_format_diff_executable +
        " -style=file -p1 > " + clang_format_path, repo_root)

    if not os.stat(clang_format_path).st_size == 0:
        if list_of_changed_staged_files:
            print("=" * 80)
            print("Cannot format your code, because some files are \n"
                  "only partially staged! Format your code or try \n"
                  "stashing your unstaged changes...")
            print("=" * 80)
            exit(1)

        run_command_in_folder("git apply -p0 " + clang_format_path, repo_root)
        run_command_in_folder("git add " + ' '.join(staged_files), repo_root)

        print("=" * 80)
        print("Formatted staged C++ files with clang-format.\n" +
              "Patch: {}".format(clang_format_path))
        print("=" * 80)
    return True


def run_clang_format_on_all(repo_root, files):
    """Runs clang format on all cpp files in repo."""

    clang_format_executable = find_clang_format_executable()
    counter = 0
    formatted_counter = 0
    for f in files:
        f_long = os.path.join(repo_root, f)
        if not os.path.isfile(f_long):
            continue
        if f.lower().endswith(tuple(CPP_SUFFIXES)):
            counter = counter + 1
            stat = os.stat(f_long)
            run_command_in_folder(clang_format_executable + " -i " + f,
                                  repo_root)
            if os.stat(f_long) != stat:
                if formatted_counter == 0:
                    print("=" * 80)
                    print("Formatted C++ files with clang-format:")

                print("-> " + f)
                formatted_counter = formatted_counter + 1

    if formatted_counter > 0:
        print("Formatted %i of %i checked C++ files in this repo." %
              (formatted_counter, counter))
    else:
        print("=" * 80)
        print("All %i checked C++ files in this repo are in agreement with "
              "clang-format." % counter)
    return formatted_counter


def run_yapf_format(repo_root, staged_files, list_of_changed_staged_files):
    """Runs yapf format on all python files staged for commit."""

    first_file_formatted = True
    for staged_file in staged_files:
        if not os.path.isfile(staged_file):
            continue
        if staged_file.endswith((".py")):
            # Check if the file needs formatting by applying the formatting and
            # store the results into a patch file.
            yapf_format_path = ("/tmp/" +
                                os.path.basename(os.path.normpath(repo_root)) +
                                "_" + datetime.datetime.now().isoformat() +
                                ".yapf.patch")
            task = (YAPF_FORMAT_EXECUTABLE + " --style pep8 -d " +
                    staged_file + " > " + yapf_format_path)
            run_command_in_folder(task, repo_root)

            if not os.stat(yapf_format_path).st_size == 0:
                if first_file_formatted:
                    print("=" * 80)
                    print("Formatted staged python files with autopep8:")
                    first_file_formatted = False

                print("-> " + staged_file)

                if staged_file in list_of_changed_staged_files:
                    print("Cannot format your code, because this file is \n"
                          "only partially staged! Format your code or try \n"
                          "stashing your unstaged changes...")
                    print("=" * 80)
                    exit(1)
                else:
                    run_command_in_folder("git apply -p0 " + yapf_format_path,
                                          repo_root)
                    run_command_in_folder("git add " + staged_file, repo_root)

    if not first_file_formatted:
        print("=" * 80)
    return True


def run_yapf_format_on_all(repo_root, files):
    """Runs yapf format on all python files."""

    # Check if the file needs formatting by applying the formatting and
    # store the results into a patch file.
    yapf_format_path = ("/tmp/" +
                        os.path.basename(os.path.normpath(repo_root)) + "_" +
                        datetime.datetime.now().isoformat() + ".yapf.patch")

    counter = 0
    formatted_counter = 0
    for f in files:
        if not os.path.isfile(os.path.join(repo_root, f)):
            continue
        if f.endswith((".py")):
            counter = counter + 1
            task = (YAPF_FORMAT_EXECUTABLE + " --style pep8 -d " + f + " > " +
                    yapf_format_path)
            run_command_in_folder(task, repo_root)

            if not os.stat(yapf_format_path).st_size == 0:
                if formatted_counter == 0:
                    print("=" * 80)
                    print("Formatted python files with autopep8:")

                print("-> " + f)
                run_command_in_folder("git apply -p0 " + yapf_format_path,
                                      repo_root)
                formatted_counter = formatted_counter + 1

    if formatted_counter > 0:
        print("Formatted %i of %i checked python files in this repo." %
              (formatted_counter, counter))
    else:
        print("=" * 80)
        print("All %i checked python files in this repo are in agreement with "
              "autopep8." % counter)
    return formatted_counter


def check_python_lint(repo_root,
                      staged_files,
                      pylint_file,
                      filter_pylint_stderr=False):
    """Runs pylint on all python scripts staged for commit.
    Return success and number of errors."""
    class TextReporterBuffer(object):
        """Stores the output produced by the pylint TextReporter."""
        def __init__(self):
            """init"""
            self.content = []

        def write(self, input_str):
            """write"""
            self.content.append(input_str)

        def read(self):
            """read"""
            return self.content

    if filter_pylint_stderr:
        print("Running pylint...")

    # Parse each pylint output line individually and searches
    # for errors in the code.
    pylint_errors = []
    for changed_file in staged_files:
        if not os.path.isfile(changed_file):
            continue
        if re.search(r'\.py$', changed_file):
            name_to_print = changed_file
            if name_to_print[:len(repo_root)] == repo_root:
                name_to_print = changed_file[len(repo_root) + 1:]
            pylint_output = TextReporterBuffer()
            pylint_args = [
                "--rcfile=" + pylint_file, "-rn",
                repo_root + "/" + name_to_print
            ]

            # Prevent pylint from printing the config XX times
            prev_stderr = sys.stderr
            if filter_pylint_stderr:
                stderr_buffer = StringIO()
                sys.stderr = stderr_buffer

            # Run the linter
            from pylint.reporters.text import TextReporter
            pylint.lint.Run(pylint_args,
                            reporter=TextReporter(pylint_output),
                            exit=False)

            # Reset stderr and print filtered warnings.
            sys.stderr = prev_stderr
            if filter_pylint_stderr:
                warnings = stderr_buffer.getvalue().splitlines()
                for warning in warnings:
                    if warning[:18] != 'Using config file ':
                        sys.stderr.write(warning)
                        sys.stderr.flush()

            errors = []
            for output_line in pylint_output.read():
                if re.search(r'^(E|C|W):', output_line):
                    errors.append(output_line)
                    pylint_errors.append(output_line)

            if errors:
                print("-" * 80)
                print("Found {} errors in : {}".format(len(errors),
                                                       name_to_print))
                print("-" * 80)
                print("\n".join(errors))

    if pylint_errors:
        print("=" * 80)
        print("Found {} pylint errors".format(len(pylint_errors)))
        print("=" * 80)
        return False, len(pylint_errors)
    else:
        return True, 0


def get_whitelisted_files(repo_root, files, whitelist):
    whitelisted = []

    for file_name in files:
        for entry in whitelist:
            # Add trailing slash if its a directory and no slash is already
            # there.
            if os.path.isdir(repo_root + '/' + entry):
                entry = os.path.join(os.path.normpath(entry), '')

            # Check if the file itself or its parent directory is in the
            # whitelist.
            if (file_name == entry
                    or os.path.commonprefix([file_name, entry]) == entry):
                whitelisted.append(file_name)
                break

    return whitelisted


def linter_check(repo_root, linter_subfolder):
    """ Main pre-commit function for calling code checking script. """

    # Read linter config file.
    linter_config_file = repo_root + '/.linterconfig.yaml'
    print("=" * 80)
    if os.path.isfile(repo_root + '/.linterconfig.yaml'):
        print("Found repo linter config: {}".format(linter_config_file))
        linter_config = read_linter_config(linter_config_file)
    else:
        print("Using default linter config.")
        linter_config = DEFAULT_CONFIG

    cpplint_file = os.path.join(linter_subfolder, "cpplint.py")
    ascii_art_file = os.path.join(linter_subfolder, "ascii_art.py")

    if os.path.isfile(os.path.join(repo_root, ".pylintrc")):
        pylintrc_file = os.path.join(repo_root, ".pylintrc")
    else:
        pylintrc_file = os.path.join(linter_subfolder, "pylint.rc")

    print("Found linter subfolder: {}".format(linter_subfolder))
    print("Found ascii art file at: {}".format(ascii_art_file))
    print("Found cpplint file at: {}".format(cpplint_file))
    print("Found pylint config file at: {}".format(pylintrc_file))

    # Run checks
    staged_files = get_staged_files()

    if not staged_files:
        print("\n")
        print("=" * 80)
        print("No files staged...")
        print("=" * 80)
        exit(1)

    if linter_config['whitelist']:
        whitelisted_files = get_whitelisted_files(repo_root, staged_files,
                                                  linter_config['whitelist'])
    else:
        whitelisted_files = staged_files

    # Load ascii art.
    ascii_art = imp.load_source('ascii_art', ascii_art_file)

    if check_commit_against_master(repo_root):
        print(ascii_art.AsciiArt.grumpy_cat)
        exit(1)

    if not check_if_merge_commit(repo_root):
        # Do not allow commiting files that were modified after staging. This
        # avoids problems such as forgetting to stage fixes of cpplint
        # complaints.
        list_of_changed_staged_files = check_modified_after_staging(
            whitelisted_files)

        if linter_config['use_clangformat']:
            run_clang_format(repo_root, whitelisted_files,
                             list_of_changed_staged_files)

        if linter_config['use_yapf']:
            run_yapf_format(repo_root, whitelisted_files,
                            list_of_changed_staged_files)

        # Use Google's C++ linter to check for compliance with Google style
        # guide.
        if linter_config['use_cpplint']:
            cpp_lint_success, _ = check_cpp_lint(whitelisted_files,
                                                 cpplint_file, ascii_art,
                                                 repo_root)
        else:
            cpp_lint_success = True

        # Use pylint to check for compliance with Tensorflow python
        # style guide.
        if linter_config['use_pylint']:
            filter_pylint_stderr = False
            if 'filter_pylint_stderr' in linter_config:
                filter_pylint_stderr = linter_config['filter_pylint_stderr']
            pylint_success, _ = check_python_lint(repo_root, whitelisted_files,
                                                  pylintrc_file,
                                                  filter_pylint_stderr)
        else:
            pylint_success = True

        if not (cpp_lint_success and pylint_success):
            print("=" * 80)
            print("Commit not up to standards!")
            print("Please address the linter errors above.")
            print("=" * 80)
            if linter_config['block_commits']:
                exit(1)

            else:
                print("However, you may commit anyway, if you must.")
                print(
                    "All of these linter errors must be resolved before merge."
                )
                print("Would you like to commit anyway? yN")

                if get_user_confirmation():
                    print(ascii_art.AsciiArt.yoda)

                else:
                    exit(1)
        else:
            commit_number = get_number_of_commits(repo_root)
            lucky_commit = (int(commit_number) % 42 == 0)

            # Pretty printing for the commit number
            commit_number_text = str(commit_number)
            if commit_number_text[-1:] == "1" \
                    and commit_number_text[-2:] != "11":
                commit_number_text = commit_number_text + "st"
            elif commit_number_text[-1:] == "2" \
                    and commit_number_text[-2:] != "12":
                commit_number_text = commit_number_text + "nd"
            elif commit_number_text[-1:] == "3" \
                    and commit_number_text[-2:] != "13":
                commit_number_text = commit_number_text + "rd"
            else:
                commit_number_text = commit_number_text + "th"

            if lucky_commit:
                print(ascii_art.AsciiArt.story)

                print("=" * 80)
                print("Commit accepted, well done! This is your %s commit!" %
                      commit_number_text)
                print("This is a lucky commit! " +
                      "Please enjoy this free sheep story.")
                print("=" * 80)
            else:
                print(ascii_art.AsciiArt.commit_success)

                print("=" * 80)
                print("Commit accepted, well done! This is your %s commit!" %
                      commit_number_text)
                print("=" * 80)
    else:
        print(ascii_art.AsciiArt.homer_woohoo)


def linter_check_all(repo_root, linter_subfolder):
    """ Run linter check on all files in repo. """

    # Read linter config file.
    linter_config_file = repo_root + '/.linterconfig.yaml'
    print("=" * 80)
    if os.path.isfile(repo_root + '/.linterconfig.yaml'):
        print("Found repo linter config: {}".format(linter_config_file))
        linter_config = read_linter_config(linter_config_file)
    else:
        print("Using default linter config.")
        linter_config = DEFAULT_CONFIG

    cpplint_file = os.path.join(linter_subfolder, "cpplint.py")
    ascii_art_file = os.path.join(linter_subfolder, "ascii_art.py")

    if os.path.isfile(os.path.join(repo_root, ".pylintrc")):
        pylintrc_file = os.path.join(repo_root, ".pylintrc")
    else:
        pylintrc_file = os.path.join(linter_subfolder, "pylint.rc")

    print("Found linter subfolder: {}".format(linter_subfolder))
    print("Found ascii art file at: {}".format(ascii_art_file))
    print("Found cpplint file at: {}".format(cpplint_file))
    print("Found pylint config file at: {}".format(pylintrc_file))

    # Run checks
    files = get_all_files(repo_root)

    # Load ascii art.
    ascii_art = imp.load_source('ascii_art', ascii_art_file)

    cpp_formatted = 0
    if linter_config['use_clangformat']:
        cpp_formatted = run_clang_format_on_all(repo_root, files)

    py_formatted = 0
    if linter_config['use_yapf']:
        py_formatted = run_yapf_format_on_all(repo_root, files)

    # Otherwise the linter os.isfile fails when calling the linters.
    files = [os.path.join(repo_root, f) for f in files]

    # Use Google's C++ linter to check for compliance with Google style
    # guide.
    cpp_errors = 0
    if linter_config['use_cpplint']:
        print("=" * 80)
        cpp_lint_success, cpp_errors = check_cpp_lint(files, cpplint_file,
                                                      ascii_art, repo_root)
        if cpp_errors == 0:
            print("Found 0 cpplint errors.")
            print("=" * 80)
    else:
        cpp_lint_success = True

    # Use pylint to check for comimpliance with Tensofrflow python
    # style guide.
    py_errors = 0
    if linter_config['use_pylint']:
        filter_pylint_stderr = False
        if 'filter_pylint_stderr' in linter_config:
            filter_pylint_stderr = linter_config['filter_pylint_stderr']
        pylint_success, py_errors = check_python_lint(repo_root, files,
                                                      pylintrc_file,
                                                      filter_pylint_stderr)
        if py_errors == 0:
            print("=" * 80)
            print("Found 0 pylint errors.")
            print("=" * 80)
    else:
        pylint_success = True

    # Summary
    if cpp_lint_success and pylint_success:
        print(ascii_art.AsciiArt.commit_success)
        print("=" * 80)

    n_py = len([f for f in files if f.lower().endswith('.py')])
    n_cpp = 0
    if linter_config['use_cpplint']:
        n_cpp = len(files) - n_py
    if not linter_config['use_pylint']:
        n_py = 0

    print("Summary:   %s C++ files checked."
          "               %s python files checked.\n"
          "           %s C++ files reformatted."
          "           %s python files reformatted.\n"
          "           %s C++ linter errors found."
          "         %s python linter errors found." %
          (str(n_cpp).ljust(3), str(n_py).ljust(3),
           str(cpp_formatted).ljust(3), str(py_formatted).ljust(3),
           str(cpp_errors).ljust(3), str(py_errors).ljust(3)))
    print("=" * 80)

    if not (cpp_lint_success and pylint_success):
        print("Code not up to standards!")
        print("Please address the linter errors above.")
    else:
        print("Code is up to standards, well done!")
    print("=" * 80)
