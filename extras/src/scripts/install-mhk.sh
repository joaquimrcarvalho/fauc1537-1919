#!/bin/bash
# Installing MHK locally
# You need Docker
#
test_os() {
  _mac=$(docker version | grep -c darwin)
  _windows=$(docker version | grep -c windows)
  _linux=$(docker version | grep -c linux)
  if [ "$_mac" != "0" ]; then
    echo "mac"
    return
  fi
  if [ "$_windows" != "0" ]; then
    if [ ! -f /c/Windows/System32/BitLockerWizard.exe ]; then
      echo "windows-home"
    else
      echo "windows"
    fi
    return
  fi
  if [ "$_linux" != "0" ]; then
    echo "linux"
    return
  fi
  echo "unknown"
  return
}
echo "Installing MHK."
echo "Current system is" $(test_os)
if [ -x "$(command -v docker)" ]; then
    echo "Docker detected"
    # command
else
    echo "No Docker install detected"
    echo "1. Go to https://www.docker.com/products/docker-desktop"
    echo "2. Install Docker desktop"
    echo "3. Run this script again"
    # command
fi
printf "Confirm to install MHK (y/N): "
read -r answer
if [ "$answer" != "Y" ] && [ "$answer" != "y" ]; then
  echo "Install cancelled"
  exit 1
fi
mkdir -p mhk-home && cd mhk-home && docker run -v ${PWD}:/mhk-home -it joaquimrcarvalho/mhk-manager mhk-install && sh app/manager init


