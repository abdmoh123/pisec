#!/usr/bin/env bash
set -euo pipefail

mkdir -p ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts

# Trust the sub-directories
mise trust client
mise trust server
mise trust camera

# Install all the mise dev tools and SDKs
cd client && mise install && cd -
cd server && mise install && cd -
cd camera && mise install && cd -
