# linter

This repo contains a (C++, python (experimental)) linter and auto formatter package that can be included into your repository as a submodule. It provides the following git hooks:
 * **General**
   * Prevent commits to master.
 * **C++** files:
   * **clang-format** Formats your code based on your .clang-format preferences.
   * **cpplint** Checks your C++ code for style errors and warnings.
   
 * **Python** files:

      * **yapf** Formats your python code.
      * **pylint** Checks your Python code for style errors and warnings.
     

## Dependencies

 * **yapf**
   * Ubuntu / macOS: `pip install yapf`
 * **clang-format**
   * Ubuntu: `sudo apt install clang-format-3.8`
   * macOS: 
     ```
     brew install clang-format
     ln -s /usr/local/share/clang/clang-format-diff.py /usr/local/bin/clang-format-diff-3.8
     ```


## Installation

### Installation via submodule
This requires the linter to be a submodule of the repository that should be checked.

```bash
cd $YOUR_REPO
git submodule add git@github.com:ethz-asl/linter.git
./linter/init-git-hooks.py
```

You can also add the linter submodule in a subfolder of your repo, e.g.:
```bash
mkdir $YOUR_REPO/dev_tools
git submodule add git@github.com:ethz-asl/linter.git dev_tools/linter
./dev_tools/linter/init-git-hooks.py
```

### Installation via catkin
If ROS/Catkin is available, the linter can also be installed and the same linter version can be used from multiple repositories.
```bash
export CATKIN_WS="~/catkin_ws"
cd $CATKIN_WS/src
git clone git@github.com:ethz-asl/linter.git
catkin build linter
source $CATKIN_WS/devel/setup.bash
rosrun linter init-git-hooks.py
```

### Configuration
Define the project-specific C++ format by adding a file `.clang-format` to your projects root folder. Example:

```
---
Language: Cpp
BasedOnStyle: Google
DerivePointerAlignment: false
PointerAlignment: Left
ColumnLimit: 80
AllowShortFunctionsOnASingleLine: Empty
AllowShortIfStatementsOnASingleLine: false
AllowShortLoopsOnASingleLine: false
AlignAfterOpenBracket: AlwaysBreak
IncludeCategories:
  - Regex:           '^<.*'
    Priority:        1
  - Regex:           '.*'
    Priority:        2
...
```

#### ASCII-Art Sources

 * [www.retrojunkie.com (accessed through web.archive.org)](https://web.archive.org/web/20150831003349/http://www.retrojunkie.com:80/asciiart/)
