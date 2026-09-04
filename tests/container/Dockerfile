FROM mcr.microsoft.com/devcontainers/javascript-node:1-22-bookworm@sha256:0d29e5fdc64f8397cd502223e0c4679f1e60877ca0fd2db4f2e2e0028e4271af

COPY accept /usr/local/bin/codex-room-container-accept
RUN chmod 0755 /usr/local/bin/codex-room-container-accept

ENTRYPOINT ["/usr/local/bin/codex-room-container-accept"]
