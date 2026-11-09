# Five-minute Compose demo

## Verification note

The walkthrough below is the intended Compose demo script. Container behavior is **UNVERIFIED** in this sandbox. Complete the one-time data/artifact preparation described in [README.md](../README.md) and [VERIFY_ONCE.md](VERIFY_ONCE.md). The first image build can take about 15–25 minutes; complete it before presenting.

## Run of show

| Time | What to do | What to say |
|---|---|---|
| 0:00–0:40 | Double-click `START_DEMO.bat`; wait for the browser to open `http://localhost:8501`. | “This prototype replays chronological test transactions through Kafka and presents resulting scores as analyst cases.” |
| 0:40–1:30 | Point to dashboard KPIs, drift state and the last retraining decision. | “The dashboard reads the scoring API and local report summaries. The drift retraining example is a synthetic stress test, not a real production incident.” |
| 1:30–2:30 | In Alerts, filter/open an alert and show XGBoost/GNN/final score, ring fields and top feature contributions. | “The model explanation is the top XGBoost contributions for this transaction. A null GNN or ring field is valid when no offline GNN artifact matches it.” |
| 2:30–3:30 | Submit an analyst case status such as Under review; return to the alert list. | “Feedback is persisted in the local SQLite demonstration database. It is a later label signal, not an input to the score that was just produced.” |
| 3:30–4:20 | Open Rings and show ring size/status summaries and the offline evaluation note. | “Ring membership is computed offline; weak links can connect unrelated transactions. The label-based precision comparison is post-hoc and unavailable during live scoring.” |
| 4:20–5:00 | Double-click `CHECK_DEMO.bat`; show the result window. | “The smoke check confirms containers, API, processed score count, alert presence and dashboard reachability. It does not prove production durability.” |

## Expected output

The launcher should report Kafka, MLflow, API and dashboard healthy, create `transactions` and `fraud-scores`, then print producer JSON containing `"published": 300`. If replay fails, it should print that the existing seed script is being used. It waits for the API to report at least 300 scored rows and prints the dashboard/API/MLflow URLs. The check window should show PASS for each configured check; alert count is data-dependent but must be nonzero for the demo check to pass.

## Screenshots to save

Save under `docs/screenshots/`:

1. Dashboard overview with KPIs and alert table.
2. An alert detail with scores and top feature contributions.
3. Rings page with the offline-label caveat visible.

Only `.gitkeep` is present until the user captures screenshots. Do not include raw card data or secrets.

## Stop

Double-click `STOP_DEMO.bat`. It stops the Compose containers while keeping images and named data volumes. The next `START_DEMO.bat` run resets the serving database so the replay starts cleanly.
