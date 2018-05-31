#!/usr/bin/env python

from __future__ import print_function

import os
import subprocess
import sys


def run_command_in_folder(command, folder):
    """Run a bash command in a specific folder."""
    run_command = subprocess.Popen(command,
                                   shell=True,
                                   cwd=folder,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE)
    stdout, _ = run_command.communicate()
    command_output = stdout.rstrip()
    return command_output


def get_git_repo_root(some_folder_in_root_repo='./'):
    """Get the root folder of the current git repository."""
    return run_command_in_folder('git rev-parse --show-toplevel',
                                 some_folder_in_root_repo)


def get_linter_folder(root_repo_folder):
    """Find the folder where this linter is stored."""
    try:
        return os.environ['LINTER_PATH']
    except KeyError:
        print("Cannot find linter because the environment variable "
              "LINTER_PATH doesn't exist.")
        sys.exit(1)


def main():
    # Get git root folder.
    repo_root = get_git_repo_root()

    # Get linter subfolder
    linter_folder = get_linter_folder(repo_root)

    # Append linter folder to the path so that we can import the linter module.
    linter_folder = os.path.join(repo_root, linter_folder)
    sys.path.append(linter_folder)

    import linter

    linter.linter_check(repo_root, linter_folder)


if __name__ == "__main__":
    main()
