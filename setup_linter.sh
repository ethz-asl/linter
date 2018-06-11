if [ ! -z $ZSH_NAME ] ; then
  LINTER_PATH="$( cd "$( dirname "$0" )" && pwd )"
elif [ ! -z $BASH ] ; then
  LINTER_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
else
  echo "Linter: Unsupported shell! Only bash and zsh supported at the moment!"
fi
export LINTER_PATH

export PATH="$PATH:$LINTER_PATH/bin"
