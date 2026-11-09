# Five-minute demo runbook

## Verification status

**UNVERIFIED:** Docker Compose and Minikube runtime paths were not run in this documentation environment. The commands below are the intended user-side sequence. Expected output describes the application contract and producer's documented count; it is not captured deployment output. Complete the generated-data/model steps first and build images from the repository root.

## Prerequisites

For either option, the repository needs the two permitted Kaggle training CSVs under `data/raw/`, generated processed features, a materialized Feast online store, and exported XGBoost/GNN artifacts. Build the images before first run. The API image includes the local Feast online SQLite store, so rebuilding it can take time and requires the generated files.

## A. Docker Compose fallback

1. Start the stack:

   ```bash
   docker compose -f docker/docker-compose.full.yml up -d
   docker compose -f docker/docker-compose.full.yml ps
   ```

   Expected: `kafka`, `mlflow`, `api`, `consumer`, and `dashboard` containers are listed. A `Up` state is only a process-level check; verify health below.

2. Check API health and open the dashboard:

   ```bash
   curl -sS http://localhost:8000/health
   curl -sS http://localhost:8000/metrics-lite
   ```

   Expected health body: `{"status":"ok"}`. Open `http://localhost:8501`; MLflow is available at `http://localhost:5000`.

3. Replay the test split through the Compose network:

   ```bash
   docker compose -f docker/docker-compose.full.yml run --rm api \
     python -m src.streaming.producer --docker --limit 1000 --rate 20
   ```

   Expected producer JSON includes `"published": 1000`. The consumer runs continuously. Poll `curl -sS http://localhost:8000/metrics-lite` until score count reaches the replay count in a clean database; alert count depends on the saved model cutoff and input rows.

4. In the dashboard, open an alert, inspect its scores/contributions, and submit a case status. The database is a named Compose volume. To reset this demonstration before rerunning, stop the stack and remove volumes:

   ```bash
   docker compose -f docker/docker-compose.full.yml down -v
   ```

## B. Minikube

1. Start the requested local cluster and deploy:

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

   Expected pod roles: Kafka `1/1`, MLflow `1/1`, scoring `2/2`, dashboard `1/1`; the producer Job appears as `Completed` after replay. Names gain generated suffixes. This is a reference state, not verified output.

2. Start three port-forwards, each in its own terminal:

   ```bash
   kubectl port-forward -n fraud svc/scoring 8000:8000
   kubectl port-forward -n fraud svc/dashboard 8501:8501
   kubectl port-forward -n fraud svc/mlflow 5000:5000
   ```

   Check `curl -sS http://localhost:8000/health` and open `http://localhost:8501`.

3. Run and inspect replay:

   ```bash
   make k8s-demo
   kubectl get jobs,pods -n fraud -o wide
   kubectl logs -n fraud job/producer-demo --tail=100
   kubectl logs -n fraud deployment/scoring -c consumer --tail=100
   curl -sS http://localhost:8000/metrics-lite
   ```

   The producer Job defaults to 1,000 transactions at 20 transactions/second through the `fraud-settings` ConfigMap. Expected completed Job output and service score count are not runtime-verified. Pod `emptyDir` contents disappear when the pod is recreated.

4. Troubleshoot a pod before repeating the demo:

   ```bash
   kubectl get pods -n fraud -o wide
   kubectl describe pod -n fraud <pod-name>
   kubectl logs -n fraud <pod-name> -c <container-name> --previous
   ```

## Three screenshots to capture

Save under `docs/screenshots/` and include no raw payment data:

1. Dashboard overview: KPI row and filtered alert table.
2. Case detail: XGBoost/GNN/final scores, ring fields, top contributions, and analyst status controls.
3. Rings view: ring grouping plus its note that fraud labels are used only for offline evaluation.

`docs/screenshots/.gitkeep` reserves the folder; screenshots are not present yet.
