# Devcontainer helpers (Requires devcontainer-cli and docker-like program)
#
# Usage:
#   make up                   # create, setup and start the container
#   make enter                # enter the created container
#   make rebuild              # recreate container from scratch, then enter
#   make down                 # stop and remove the container
#
# Override on the command line if needed, e.g.:
#   make dev DOTFILES=https://github.com/you/dotfiles

CONFIG      := .devcontainer/devcontainer.json
DOCKER_PATH ?= /usr/bin/docker
SHELL_CMD   ?= bash
DOTFILES    ?=

# SSH agent socket mount (only if an agent is running on the host).
# On macOS with Docker Desktop, use /run/host-services/ssh-auth.sock instead.
SSH_SOCK := $(SSH_AUTH_SOCK)

DC_ARGS := --workspace-folder . --config $(CONFIG) --docker-path $(DOCKER_PATH)
UP_ARGS := $(DC_ARGS)

# Pass through gitconfig if available
HOST_GITCONFIG := $(firstword $(wildcard $(HOME)/.gitconfig $(HOME)/.config/git/config))
ifneq ($(HOST_GITCONFIG),)
UP_ARGS += --mount "type=bind,source=$(HOST_GITCONFIG),target=/home/dev/.gitconfig"
endif

ifneq ($(DOTFILES),)
UP_ARGS += --dotfiles-repository $(DOTFILES) --dotfiles-install-command install.sh
endif

.PHONY: up enter rebuild down

up:
	devcontainer up $(UP_ARGS)

enter:
	devcontainer exec $(DC_ARGS) $(SHELL_CMD)

rebuild:
	devcontainer up $(UP_ARGS) --remove-existing-container --build-no-cache

down:
	$(DOCKER_PATH) rm -f $$($(DOCKER_PATH) ps -aq --filter label=devcontainer.local_folder=$(CURDIR) --filter label=devcontainer.config_file=$(CURDIR)/$(CONFIG))
