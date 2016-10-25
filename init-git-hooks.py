#!/usr/bin/env python
# Disable pylint filename and missing module member complaints.
# pylint: disable=C0103,E1101
""" Initializes git hooks for refill project. """

import commands
import subprocess

def main():
    """ Copies pre-commit script to git hooks folder. """
    _, repo_root = commands.getstatusoutput('git rev-parse --show-toplevel')
    cp_params = repo_root + "/devtools/pre-commit " + repo_root + "/.git/hooks/"
    subprocess.call("cp " + cp_params, shell=True)

if __name__ == "__main__":
    main()
