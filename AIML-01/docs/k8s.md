# Kubernetes manifests (static-only)

The repository includes Minikube manifests. They are statically parsed and checked by `tests/test_phase_8_infra.py` and `tests/test_demo_setup.py`, but **NOT runtime-verified**. The verified project path is intended to be Docker Compose; Compose runtime is also **UNVERIFIED here** until the user follows [VERIFY_ONCE.md](VERIFY_ONCE.md). The Windows double-click demo does not use Kubernetes.

## Prerequisites

Build the local data and model artifacts before building images. Required files include the materialized Feast online SQLite store, processed features, exported XGBoost artifacts and GNN score/ring artifacts. The API image includes the materialized store; final Docker image sizes have not been measured. See [README.md](../README.md) for data and artifact generation.

## Minikube commands (user-side, runtime UNVERIFIED)

The intended resource envelope uses the configured WSL memory limit and Minikube Docker driver:

```bash
minikube start --driver=docker --memory=5120 --cpus=3
make k8s-build
make k8s-up
kubectl wait --for=condition=Ready pod -l app=kafka -n fraud --timeout=5m
kubectl wait --for=condition=Available deployment/mlflow -n fraud --timeout=10m
kubectl wait --for=condition=Available deployment/scoring -n fraud --timeout=10m
kubectl wait --for=condition=Available deployment/dashboard -n fraud --timeout=10m
make k8s-status
```

`make k8s-build` uses normal host `docker build` commands, then loads each tagged image into Minikube with `minikube image load`. It does not use `minikube docker-env`, which is not suitable for the configured containerd image store. On build/load failure, Make stops and prints the failing image step. Local project images use `imagePullPolicy: Never`.

`make k8s-up` applies the namespace, config, Kafka, MLflow, scoring, dashboard and drift CronJob resources. It does not create the producer Job. The producer is separate and only starts through `make k8s-demo`:

```bash
make k8s-demo
kubectl get jobs,pods -n fraud -o wide
```

The producer Job reads `TRANSACTION_LIMIT` and `PRODUCER_RATE` from `k8s/10-config.yaml`. The drift CronJob runs the report and a dry-run retraining check; outputs are ephemeral and it cannot read analyst feedback from the scoring pod's SQLite volume.

Port-forward each service from a separate terminal:

```bash
kubectl port-forward -n fraud svc/scoring 8000:8000
kubectl port-forward -n fraud svc/dashboard 8501:8501
kubectl port-forward -n fraud svc/mlflow 5000:5000
```

Then visit `http://localhost:8501`; check the API at `http://localhost:8000/health` and MLflow at `http://localhost:5000`. Reference pod roles are Kafka `1/1`, MLflow `1/1`, scoring `2/2`, and dashboard `1/1`; the producer pod is `Completed` after replay. These are expected shapes, not observed deployment output.

## Logs and cleanup

```bash
kubectl logs -n fraud deployment/scoring -c api --tail=100
kubectl logs -n fraud deployment/scoring -c consumer --tail=100
kubectl logs -n fraud deployment/kafka -c broker --tail=100
kubectl logs -n fraud deployment/mlflow -c mlflow --tail=100
kubectl logs -n fraud deployment/dashboard -c dashboard --tail=100
kubectl logs -n fraud job/producer-demo --tail=100
make k8s-down
```

Troubleshoot with `kubectl describe pod -n fraud <pod>` and `kubectl logs -n fraud <pod> -c <container> --previous`. For memory use, `kubectl top pods -n fraud` requires metrics-server. Kafka clients inside the cluster must use `kafka:29092`. Pod `emptyDir` content does not survive pod recreation.

## Compose fallback

Compose is the primary demo route. Its startup, scoring, screenshot and cleanup procedure is [docs/DEMO.md](DEMO.md); the one-click Windows procedure is [docs/VERIFY_ONCE.md](VERIFY_ONCE.md). The Minikube manifests should not be presented as a deployed runtime until a user has run the commands above.
