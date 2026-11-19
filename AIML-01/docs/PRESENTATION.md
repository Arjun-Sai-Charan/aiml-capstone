# Ten-minute presentation outline

## Slide 1 — Fraud is rare, and the operating point matters (1:00)

**On slide:** IEEE-CIS training window; chronological evaluation; why recall, precision and review capacity matter more than accuracy.

**Speaker notes:** This prototype processes 150,000 chronological rows. Fraud prevalence is 2.62% in train, 1.72% in validation and 3.67% in test (`results/eda_summary.json`). A model can look accurate by predicting the majority class, so we report PR-AUC against each split's own base rate and use alert budgets.

## Slide 2 — Data and causal feature design (1:15)

**On slide:** CSV → chronological join/split → per-uid features → Feast.

**Speaker notes:** Time ordering is preserved. Features use strictly earlier transactions; same-time rows are grouped so they cannot leak into each other. The model uses 52 numeric inputs and drops transaction identifiers, timestamps, split and label columns. Feast historical/online parity compared 67 fields on 100 sampled transactions with no mismatches (`results/feature_parity.json`); that is sample parity, not proof across every record or a live service.

## Slide 3 — Baselines and XGBoost (1:30)

**On slide:** Logistic, random, XGBoost without and with class weight; validation and test PR-AUC.

**Speaker notes:** Logistic regression PR-AUC is 0.0832 on validation and 0.1568 on test. Unweighted XGBoost is 0.4172 and 0.5531; weighted XGBoost is 0.3461 and 0.5075 (`results/xgb_metrics.json`). The unweighted run won validation PR-AUC. Test prevalence is higher than validation, so compare each PR-AUC with its base rate rather than treating the difference as pure model improvement.

## Slide 4 — Alert-budget threshold (1:00)

**On slide:** Validation top-3% cutoff; test precision/recall at 1%, 3%, and fixed threshold alert rate.

**Speaker notes:** The cutoff is chosen by validation review budget, not by maximizing F1. At the test set's 1% budget, unweighted XGBoost precision/recall are 0.8967/0.2445; at 3% they are 0.6133/0.5018 (`results/xgb_metrics.json`). Applying the validation cutoff to the whole test split flags 1,184 rows (3.9467%), so a fixed threshold does not force a fixed future alert rate.

## Slide 5 — Graph model and ablation (1:30)

**On slide:** Heterogeneous entities; train-only normalization; real and shuffled edges; blend.

**Speaker notes:** The real-graph GNN test PR-AUC is 0.2717, and shuffled edges score 0.2635. XGBoost is 0.5531; validation chose XGBoost weight 1.0, making the final blend equal to XGBoost (`results/ablation.json`). The GNN does not lift the final model, and the closeness of the shuffled control weakens the claim that entity structure drives its score. The offline snapshot also allows later-in-split feature messages, which is optimistic relative to incremental scoring.

## Slide 6 — Streaming, serving, and analyst workflow (1:15)

**On slide:** Kafka → consumer → FastAPI/shared scorer → SQLite → Streamlit.

**Speaker notes:** The producer replays test transaction IDs in time order. The consumer uses the shared scorer and persists scores/alerts before publishing responses. The API supports feedback and case status; the dashboard displays top XGBoost contributions and offline rings. The latency benchmark measures Feast online lookup plus inference, excluding Kafka and startup: p50 26.28 ms, p95 52.14 ms, p99 74.36 ms, throughput 33.01 transactions/second (`results/latency.json`). Kafka integration and browser deployment remain unverified until the live demo is run.

## Slide 7 — Drift and candidate retraining (1:15)

**On slide:** Natural adjacent windows, threshold rule, real recent window, synthetic stress and candidate comparison.

**Speaker notes:** Adjacent 15,000-row natural windows have mean drift share 0.2158 and maximum 0.50; the threshold is maximum plus 0.10 = 0.60 (`results/drift/natural_baseline.json`). The recent real window scores 0.0769, below threshold; the deliberately shifted synthetic stress scores 1.0. The retrain demo was triggered with that synthetic report. Candidate v4 scored test PR-AUC 0.5984 versus champion v2 at 0.5531 (`results/retrain_log.json`), but test is only a final comparison and promotion remains manual.

## Slide 8 — Limits and next steps (1:15)

**On slide:** What works locally; what is not yet demonstrated; deployment and submission plan.

**Speaker notes:** Results and tests support a local prototype, not a production service. Compose and Minikube images/manifests are present, but runtime is unverified. SQLite and Kubernetes `emptyDir` are demonstration storage. Next steps: run the end-to-end deployment, capture dashboard screens, document API/setup, and rehearse a clean-clone run.

## What we claim / what we do not claim

- **We claim:** chronological offline evaluation; prior-only per-uid features; XGBoost beats the tested baselines on saved PR-AUC; a local FastAPI/SQLite/dashboard and Kafka integration path exists in code; static Kubernetes manifests and offline tests exist.
- **We do not claim:** a production-grade detector; a verified live Kafka or Minikube deployment; a graph lift over XGBoost; unbiased proof that the candidate retrain generalizes beyond this test set; realistic drift detection from the synthetic stress test; durable storage or live incremental ring assignment.

## Likely questions

**Why is test precision at a 1% alert budget higher than validation?**

At the 1% alert budget, unweighted XGBoost precision is 0.6033 on validation and 0.8967 on test (`results/xgb_metrics.json`). Test prevalence is 3.67%, versus 1.72% validation, about 2.13 times as high. A higher positive rate can yield more true positives among the same top-ranked fraction, but the periods also differ, so prevalence alone does not prove why; recall and ranking metrics must be shown with the base rates.

**Why is the GNN not in the final score?**

Validation selected XGBoost blend weight 1.0 (`results/ablation.json`), so adding GNN score reduced or did not improve validation PR-AUC. Real graph test PR-AUC also trails XGBoost, and shuffled edges are close to real edges.

**Why is the drift threshold 0.60?**

The natural adjacent-window maximum is 0.50 and the configured rule adds a 0.10 margin (`results/drift/natural_baseline.json`). This leaves headroom over observed natural variation in this finite timeline; it is not a universal production threshold.

**What does the synthetic stress test show, and what does it not show?**

It shows that Evidently detects a deliberately extreme shift (drift share 1.0) (`results/drift/shifted_window_drift.json`). It does not establish detection quality on real incidents, nor that the observed recent real window should trigger.

**Why are labels unavailable at live scoring time?**

Fraud labels are outcomes of later investigation/chargeback processes. The scoring decision must be returned before that ground truth exists; analyst feedback can be collected later and handled as a separate retraining signal.
