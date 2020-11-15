#!/usr/bin/env bash

set -euo pipefail

###############################
# General

message="Installing prerequisites.

Cf. 
- https://docs.knora.org/04-publishing-deployment/getting-started/
- https://github.com/dasch-swiss/knora-api"

echo $message

###############################
# Homebrew

echo "Check and update homebrew"
if [[ -z "$(brew --version)" ]] ; then
  echo "Brew needs to be installed"
fi
brew --version
brew update

###############################
# Git

echo "Check git"
if [[ -z "$(git --version)" ]] ; then
  echo "Git needs to be installed"
  brew install git
fi
git --version

###############################
# Bazelisk

echo "Check and update Bazelisk"        
if [[ -z "$(brew leaves | grep bazelisk)" ]]; then
  echo "Installing bazelisk"
  brew install bazelisk
fi
brew upgrade bazelisk
bazelisk version

###############################
# expect

echo "Install expect"
brew install expect

###############################
# sbt

echo "Install sbt"
brew install sbt
  
###############################
# AdoptOpenJDK 11

echo "Switch to JAVA 11 (AdoptOpenJDK)"
# brew tap AdoptOpenJDK/openjdk
# brew cask install AdoptOpenJDK/openjdk/adoptopenjdk11
export JAVA_HOME=`/usr/libexec/java_home -v 11`
java -version
     
###############################
# Docker

# see https://github.com/actions/virtual-environments/issues/1143#issuecomment-652264388
# see https://github.com/play-with-go/play-with-go/blob/main/_scripts/macCISetup.sh

echo "Install and set up Docker"
          
# Install Docker
brew cask install docker

# Allow the app to run without confirmation
xattr -d -r com.apple.quarantine /Applications/Docker.app

# preemptively do docker.app's setup to avoid any gui prompts
sudo /bin/cp /Applications/Docker.app/Contents/Library/LaunchServices/com.docker.vmnetd /Library/PrivilegedHelperTools
sudo /bin/cp /Applications/Docker.app/Contents/Resources/com.docker.vmnetd.plist /Library/LaunchDaemons/
sudo /bin/chmod 544 /Library/PrivilegedHelperTools/com.docker.vmnetd
sudo /bin/chmod 644 /Library/LaunchDaemons/com.docker.vmnetd.plist
sudo /bin/launchctl load /Library/LaunchDaemons/com.docker.vmnetd.plist

# Run
[[ $(uname) == 'Darwin' ]] || { echo "This function only runs on macOS." >&2; exit 2; }
echo "-- Starting Docker.app, if necessary..."
open -g -a /Applications/Docker.app || exit

# Wait for the server to start up, if applicable.
i=0
while ! docker system info &>/dev/null; do
  (( i++ == 0 )) && printf %s '-- Waiting for Docker to finish starting up...' || printf '.'
  sleep 1
done
(( i )) && printf '\n'

echo "-- Docker is ready."
docker version
