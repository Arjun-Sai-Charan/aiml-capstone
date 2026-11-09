SHELL := /bin/bash
UV ?= uv
VENV ?= .venv

.PHONY: setup data features feature-store train train-xgb train-xgb-local train-gnn train-gnn-local drift retrain retrain-local export-model benchmark ring-precision demo-data dashboard demo-start demo-stop demo-check k8s-build k8s-up k8s-demo k8s-status k8s-down gnn serve serve-registry test push
setup:
	$(UV) venv --python 3.11 $(VENV)
	$(UV) pip install --index-strategy unsafe-best-match --python $(VENV)/bin/python -r requirements.txt

data:
	$(VENV)/bin/python -m src.data.prepare

features:
	$(VENV)/bin/python -m src.features.build_features

feature-store:
	$(VENV)/bin/python -m src.features.build_features
	cd src/feature_repo && ../../$(VENV)/bin/feast apply
	cd src/feature_repo && ../../$(VENV)/bin/feast materialize 2017-11-30T00:00:00 2018-01-06T00:00:00
	$(VENV)/bin/python -m src.features.feature_parity

train:
	$(VENV)/bin/python -m src.models.train_xgb

train-xgb:
	$(VENV)/bin/python -m src.models.train_xgb --tracking-uri http://localhost:5000

train-xgb-local:
	$(VENV)/bin/python -m src.models.train_xgb --tracking-uri file:./mlruns_local

TRACKING_URI ?= file:./mlruns_local
export-model:
	$(VENV)/bin/python -m scripts.export_model --tracking-uri $(TRACKING_URI)

train-gnn:
	$(VENV)/bin/python -m src.models.train_gnn --tracking-uri http://localhost:5000

train-gnn-local:
	$(VENV)/bin/python -m src.models.train_gnn --tracking-uri file:./mlruns_local

drift:
	$(VENV)/bin/python -m src.monitoring.drift

retrain:
	$(VENV)/bin/python -m src.monitoring.retrain --tracking-uri http://localhost:5000 $(RETRAIN_ARGS)

retrain-local:
	$(VENV)/bin/python -m src.monitoring.retrain --tracking-uri file:./mlruns_local $(RETRAIN_ARGS)

gnn: train-gnn

serve:
	$(VENV)/bin/python -m uvicorn src.serving.api:app --host 0.0.0.0 --port 8000

serve-registry:
	FRAUD_MODEL_SOURCE=registry MLFLOW_TRACKING_URI=$(TRACKING_URI) $(VENV)/bin/python -m uvicorn src.serving.api:app --host 0.0.0.0 --port 8000

benchmark:
	$(VENV)/bin/python -m scripts.benchmark_latency

ring-precision:
	$(VENV)/bin/python -m scripts.ring_precision

demo-data:
	$(VENV)/bin/python -m scripts.seed_demo_alerts

dashboard:
	PYTHONPATH=. $(VENV)/bin/streamlit run src/dashboard/app.py --server.port 8501

demo-start:
	./scripts/demo_start.sh

demo-stop:
	./scripts/demo_stop.sh

demo-check:
	./scripts/demo_check.sh

k8s-build:
	@set -e; \
	build_and_load() { \
	  image="$$1"; dockerfile="$$2"; \
	  echo "Building $$image with host Docker..."; \
	  docker build -f "$$dockerfile" -t "$$image" . || { echo "ERROR: docker build failed for $$image ($$dockerfile)." >&2; return 1; }; \
	  echo "Loading $$image into Minikube's containerd image store..."; \
	  minikube image load "$$image" || { echo "ERROR: minikube image load failed for $$image." >&2; return 1; }; \
	}; \
	build_and_load fraud-api:phase8 docker/api.Dockerfile && \
	build_and_load fraud-dashboard:phase8 docker/dashboard.Dockerfile && \
	build_and_load fraud-jobs:phase8 docker/jobs.Dockerfile

k8s-up:
	kubectl apply -f k8s/00-namespace.yaml
	kubectl apply -f k8s/10-config.yaml
	kubectl apply -f k8s/20-kafka.yaml
	kubectl apply -f k8s/30-mlflow.yaml
	kubectl apply -f k8s/40-scoring.yaml
	kubectl apply -f k8s/50-dashboard.yaml
	kubectl apply -f k8s/60-jobs.yaml

k8s-demo:
	kubectl delete job producer-demo -n fraud --ignore-not-found
	kubectl apply -f k8s/61-producer-job.yaml
	kubectl wait --for=condition=complete job/producer-demo -n fraud --timeout=15m

k8s-status:
	kubectl get pods,services,jobs,cronjobs -n fraud -o wide

k8s-down:
	kubectl delete namespace fraud --ignore-not-found

test:
	$(VENV)/bin/python -m pytest -q

push:
	@email="$$(git config user.email)"; case "$$email" in *@users.noreply.github.com) ;; *) echo "ERROR: configure your GitHub noreply email before pushing." >&2; exit 1 ;; esac
	git rebase origin/main --exec "git commit --amend --reset-author --no-edit"
	git push

