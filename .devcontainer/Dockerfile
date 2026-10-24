# syntax=docker/dockerfile:1

FROM docker.io/fedora:44

# Add copr repos
RUN <<EOF
dnf copr enable dejan/lazygit -y
EOF

# Install github cli (with git)
RUN <<EOF
dnf install -y git git-lfs dnf5-plugins
dnf config-manager addrepo --from-repofile=https://cli.github.com/packages/rpm/gh-cli.repo
dnf install gh -y --repo gh-cli
EOF

# Installs essentials
RUN dnf install -y sudo ripgrep fd-find wget stow fzf zoxide

# Installs dev related apps
RUN dnf install -y lazygit neovim delta jq

# Set up a non-root dev user with sudo access
ARG USERNAME=dev
ARG USER_UID=1000
ARG USER_GID=1000
RUN groupadd --gid ${USER_GID} ${USERNAME} \
  && useradd --uid ${USER_UID} --gid ${USER_GID} -m -s /bin/bash ${USERNAME} \
  && echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} \
  && chmod 0440 /etc/sudoers.d/${USERNAME}

USER ${USERNAME}
