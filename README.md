# ASL linter

This repo will serve as a generic (C++, python) linter package that can be included into your repository.
It will install git hooks that will run clang-format and the cpplinter/pylinter.

TODOs:

 - [ ] Add clang formatter
 - [ ] Add yapf formatter for python
 - [ ] Don't format merge commit changes
 - [ ] Make generic and/or provide environment variables to adapt to repo
 - [ ] Add to repos and test it:
   - [ ] maplab
   - [ ] voxblox
   - [ ] turtlebot_navigation
   - [ ] refill
