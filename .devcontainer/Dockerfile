FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm
USER root
# This project uses npm, not Yarn. The inherited Yarn apt source has a stale
# signing key and prevents the Docker feature from running apt-get update.
# Remove only that unused source; never disable apt signature verification.
RUN python -c "from pathlib import Path; [Path('/etc/apt/sources.list.d', name).unlink(missing_ok=True) for name in ('yarn.list', 'yarn.sources')]"
