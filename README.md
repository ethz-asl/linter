# linter

This repo contains a (C++, python) linter and auto formatter package that can be conveniently installed into your repositories using git hooks. It provides the following git hooks:
 * **General**
   * Prevent commits to master.
 * **C++** files:
 *
   * **clang-format** Formats your code based on your `.clang-format` preferences.
   * **cpplint** Checks your C++ code for style errors and warnings.

 * **Python** files:

      * **yapf** Formats your python code.
      * **pylint** Checks your Python code for style errors and warnings.


## Dependencies

 * **pylint**
   * macOS:
     ```
     pip install pylint
     ```
 * **yapf**
   * Ubuntu / macOS: `pip install yapf`
 * **clang-format**
   * Compatible with `clang-format-3.8 - 6.0`
   * Ubuntu: `sudo apt install clang-format-${VERSION}`
   * macOS:
     ```
     brew install clang-format
     ln -s /usr/local/share/clang/clang-format-diff.py /usr/local/bin/clang-format-diff
     ```


## Installation

```bash
git clone git@github.com:ethz-asl/linter.git
cd linter
echo ". $(realpath setup_linter.sh)" >> ~/.bashrc  # Or the matching file for
                                                   # your shell.
bash
```

Then you can install the linter in your repository:
```bash
cd $YOUR_REPO
init_linter_git_hooks
```

## Uninstallation
To remove the linter from your git repository again, run the following:
```bash
cd $YOUR_REPO
init_linter_git_hooks --remove
```

## Linter configuration

**General**

To configure the linter, add a file named `.linterconfig.yaml` in your repository root. An example file is given under [`linterconfig.yaml_example`](https://github.com/ethz-asl/linter/blob/master/linterconfig.yaml_example).

**C++**

clang-format can be configured by defining a project-specific C++ format by adding a file `.clang-format` to your projects root folder. Example file:

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

**Python**

Currently there it is not possible to configure the python formatter on a per-repository basis. The linter can be configured on a per-repository bais by adding a `.pylintrc` file to your repositorie's root folder.



## Disable Linter Functionalities for a Specific Line

 * **C++ Linter (`cpplint`):**
   ```cpp
   void your_awful_function(int & result) // NOLINT
   ```
 * **C++ Formatting (`clang-format`):**
   ```cpp
   // clang-format off
   ...
   // clang-format on   
   ```
 * **Python Linter (`pylint`)**

   For whole file:
   ```python
   #!/usr/bin/env python
   # pylint: disable=C0103,E1101
   ...
   ```
   For a line:
   ```Python
   your_awful_function('-legal/copyright,-build/c++11')  # pylint: disable=W0212
   ```
   The full list of pylint warnings and errors can be found [here](http://pylint-messages.wikidot.com/all-messages)

 * **Python Formatting (`yapf`)**
   ```python
   # yapf: disable
   ...
   # yapf: enable
   ```


## ASCII-Art Sources

 * [www.asciiart.eu](https://www.asciiart.eu)
 * [www.retrojunkie.com (accessed through web.archive.org)](https://web.archive.org/web/20150831003349/http://www.retrojunkie.com:80/asciiart/)
