#!/bin/sh
# Run a backup at ~/.zshrc.bak
cat ~/.zshrc > ~/.zshrc.bak
# Load it in and source
cat .zshrc >> ~/.zshrc
echo 'Installed into zshrc. Reload shell or run "source .zshrc"'
