# WSL2 development setup

This setup guide applies to the current repository, including the Phase 8 Compose and Minikube deployment files. Kubernetes deployment is implemented as manifests and Makefile targets, but its runtime remains unverified until a user runs the commands in `docs/k8s.md`.

Run project commands from Ubuntu in WSL2, with the repository under the Linux home directory (for example, `~/fraud-platform`), not under `/mnt/c`. Install Python 3.11 through uv so the system Python version does not affect the project environment.

## Windows setup

Install Docker Desktop and enable **Use the WSL 2 based engine**. Under **Settings → Resources → WSL Integration**, enable the Ubuntu distribution. Create `%UserProfile%\.wslconfig` in Windows with suitable resource limits, for example:

```ini
[wsl2]
memory=10GB
processors=4
```

Apply changes from PowerShell with `wsl --shutdown`, then reopen Ubuntu. Adjust memory and processor counts to the host machine.

## Ubuntu setup

Install uv using its official installation method, then in the Ubuntu terminal run:

```bash
cd ~/fraud-platform
uv python install 3.11
make setup
.venv/bin/python --version
```

`make setup` creates `.venv` with Python 3.11 and installs the pinned requirements. The Makefile uses uv's `unsafe-best-match` index strategy so packages such as `requests` remain available alongside the PyTorch CPU wheel index.

Check Docker Desktop integration:

```bash
docker version
docker compose version
```

If the Docker socket reports a group permission error, check `id` and the socket's group. Add the current WSL user to the `docker` group only if that group exists and is required by the installed integration:

```bash
sudo usermod -aG docker "$USER"
```

Close all Ubuntu shells and reopen the distribution for group membership to take effect. Docker Desktop WSL integration normally manages the socket; do not install a second Docker daemon inside Ubuntu unless intentionally configuring one.

## Optional local services

From the repository root:

```bash
docker compose -f docker/docker-compose.yml up -d
```

Minikube deployment is available when you want to exercise the Kubernetes manifests. First confirm Docker Desktop works from WSL2, then follow the full build, deploy, readiness and cleanup sequence in `docs/k8s.md`. The basic cluster start command is:

```bash
minikube start --memory=5120 --cpus=3 --driver=docker
```

From the repository root, the deployment targets are `make k8s-build`, `make k8s-up`, `make k8s-status`, `make k8s-demo`, and `make k8s-down`. The manifests are statically checked; this is not a claim that the current environment has run a Minikube deployment.
