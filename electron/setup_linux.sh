#!/bin/bash

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "This is not Linux. Exiting script..."
    exit 1
fi

read -r -p "This application needs nodejs to build the front end components. Do you want to install it now? (Y/n)?" node_answer
node_answer=${node_answer:-Y}
if [[ $node_answer == [Yy] ]]; then
  echo "Installing nodejs 24"

  # Download and install nvm:
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash

  # in lieu of restarting the shell
  \. "$HOME/.nvm/nvm.sh"

  # Download and install Node.js:
  nvm install 24
fi

echo "Downloading dependencies"
npm install