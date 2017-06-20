# ASL linter

This repo contains a generic (C++, python) linter and auto formatter package that can be included into your repository as a submodule:
```bash
cd $YOUR_REPO
git add submodule git@github.com:ethz-asl/linter.git
./linter/init-git-hooks.py
```

You can add the linter submodule in a subfolder of your repo, e.g.:
```bash
mkdir $YOUR_REPO/dev_tools
cd  $YOUR_REPO/dev_tools
git add submodule git@github.com:ethz-asl/linter.git
./linter/init-git-hooks.py
```

The following git hooks are installed:
 * cpp files:
   * clang-formatter
   * cpplint
 * python files:
   * pep8 formatter
   * pylint

TODOs:
 - [ ] Add clang formatter
 - [ ] Add yapf/pep formatter for python
 - [x] Don't format merge commit changes
 - [x] Make generic and/or provide environment variables to adapt to repo
 - [ ] Repos-specific style
 - [ ] Add to repos and test it:
   - [ ] maplab
   - [ ] voxblox
   - [ ] turtlebot_navigation
   - [ ] refill
