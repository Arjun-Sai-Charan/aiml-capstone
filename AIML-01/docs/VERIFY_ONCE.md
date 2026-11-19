# One-time demo verification

**Current status: UNVERIFIED.** No Docker, Compose, Kafka or browser service was started from this sandbox.

## Before the click

Use the WSL2 Ubuntu checkout at `~/fraud-platform`, with Docker Desktop's WSL integration enabled. The permitted training CSVs and generated local model/Feast artifacts must already exist; see the prerequisite list and build sequence in [README.md](../README.md). Leave Docker Desktop installed and openable from Windows. First image build can take about 15–25 minutes.

## Verification run

1. In Windows Explorer, open the repository folder and double-click **`START_DEMO.bat`**. Keep its window open while it works.
2. Wait for the progress messages: Docker ready, image checks/builds, Kafka/MLflow/API/dashboard healthy, topics created, and replay progress. A successful Kafka replay prints JSON containing `"published": 300`; if replay fails, the launcher says it is using the local seed fallback.
3. When it prints the dashboard URL, your default browser opens `http://localhost:8501`. Confirm the page shows dashboard KPIs and at least one alert/case. The other printed links are API health (`http://localhost:8000/health`), metrics (`http://localhost:8000/metrics-lite`), and MLflow (`http://localhost:5000`).
4. Double-click **`CHECK_DEMO.bat`**. Success prints PASS for: containers up, API health, score count at least 300, alert count greater than zero, and dashboard reachable.
5. Capture the three screens listed in [DEMO.md](DEMO.md). Double-click **`STOP_DEMO.bat`** afterward; it stops containers while retaining images and named volumes. The next start clears only the serving database before replay.

## If anything fails

Keep the batch window open and send the full error text plus the newest matching `demo_logs/start-*.log` or `demo_logs/check-*.log` file. If the failure is during startup, also send `demo_logs/compose.log` if present. Tell me whether Docker Desktop reported that its engine was running. Do not send raw Kaggle CSVs, credentials, or payment data.

The Compose runtime, replay count, dashboard screenshots and stop/restart behavior will be marked verified only after this user-side run succeeds.
