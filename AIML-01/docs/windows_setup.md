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

The project dependencies are pinned in `requirements.txt`. The three runtime images use `requirements-api.txt`, `requirements-dashboard.txt`, and `requirements-jobs.txt`, each containing exact pins selected from the main file; `requirements-serving.txt` is the standalone serving environment. Do not install the system Python packages into the project environment.

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

## One-click demo and optional Minikube

For the primary demo path, after the data/artifact prerequisites in `README.md` have been generated, double-click `START_DEMO.bat`. It opens Compose and the dashboard; `CHECK_DEMO.bat` verifies health and `STOP_DEMO.bat` stops containers without deleting images or volumes. Follow [VERIFY_ONCE.md](VERIFY_ONCE.md) for the expected result and failure logs.

To start the base services manually from the WSL repository root:

```bash
docker compose -f docker/docker-compose.yml up -d
```

Minikube manifests are available for a static-checked deployment, but Minikube runtime is **UNVERIFIED**. Docker Compose is the intended demo path; its runtime also needs the one-time check in `docs/VERIFY_ONCE.md`. To exercise Minikube, first confirm Docker Desktop works from WSL2, then follow `docs/k8s.md`. The cluster start command is:

```bash
minikube start --memory=5120 --cpus=3 --driver=docker
```

From the repository root, the Kubernetes targets are `make k8s-build`, `make k8s-up`, `make k8s-status`, `make k8s-demo`, and `make k8s-down`. `make k8s-up` does not start the producer Job; run `make k8s-demo` separately when you want to replay transactions. The build uses host Docker followed by `minikube image load` for Minikube's containerd store.
