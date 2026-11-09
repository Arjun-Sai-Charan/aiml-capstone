#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="fraud-platform"
COMPOSE_FILE="$ROOT/docker/docker-compose.full.yml"
LOG_DIR="$ROOT/demo_logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/start-$(date -u +%Y%m%dT%H%M%SZ).log"
exec > >(tee -a "$LOG_FILE") 2>&1

dc=(docker compose --project-name "$PROJECT" --file "$COMPOSE_FILE")
required_ports=(8000 8501 9092 5000)
health_timeout=300
score_timeout=600

say() { printf '\n[demo] %s\n' "$*"; }
fail() { say "ERROR: $*" >&2; exit 1; }
docker_reachable() { docker info >/dev/null 2>&1; }

ensure_docker() {
  if docker_reachable; then return; fi
  say "Docker is not responding or its command is missing. I will try to open Docker Desktop; please wait."
  local desktop_exe="/mnt/c/Program Files/Docker/Docker/Docker Desktop.exe"
  if [[ -f "$desktop_exe" ]]; then
    nohup "$desktop_exe" >/dev/null 2>&1 </dev/null &
  else
    say "Docker Desktop.exe was not found at its usual Windows path. Open Docker Desktop from the Start menu."
  fi
  for second in $(seq 1 180); do
    if command -v docker >/dev/null 2>&1 && docker_reachable; then say "Docker is ready."; return; fi
    if (( second % 15 == 0 )); then say "Still waiting for Docker Desktop ($second/180 seconds)."; fi
    sleep 1
  done
  fail "Docker did not become ready within 3 minutes. Open Docker Desktop and enable WSL integration for Ubuntu, wait until the engine is running, then double-click START_DEMO.bat again."
}

check_project_inputs() {
  local path
  local -a required_files=(
    "data/processed/features.parquet"
    "src/feature_repo/data/online.db"
    "src/feature_repo/data/registry.db"
    "artifacts/xgb/model/MLmodel"
    "artifacts/xgb/feature_list.json"
    "artifacts/xgb/threshold.json"
    "artifacts/gnn/gnn_scores.parquet"
    "artifacts/gnn/rings.parquet"
    "artifacts/gnn/blend_config.json"
  )
  for path in "${required_files[@]}"; do
    [[ -f "$ROOT/$path" ]] || fail "Required local input is missing: $path. Obtain the permitted Kaggle training files and follow the ordered build steps in README.md before starting the demo."
  done
}

check_ports() {
  command -v ss >/dev/null 2>&1 || fail "Cannot check demo ports because 'ss' is missing. Install Ubuntu iproute2 and retry."
  local own_ports port
  own_ports="$(docker ps --filter "label=com.docker.compose.project=$PROJECT" --format '{{.Ports}}')"
  for port in "${required_ports[@]}"; do
    if ss -H -ltn "sport = :$port" 2>/dev/null | grep -q .; then
      if grep -Eq ":${port}->" <<<"$own_ports"; then
        say "Port $port is used by this demo's own container; it will be restarted."
      else
        fail "Port $port is used by another application. Close that application and retry; no containers were changed."
      fi
    fi
  done
}

build_missing_images() {
  local image dockerfile entry
  local -a images=("fraud-api:phase8|docker/api.Dockerfile" "fraud-dashboard:phase8|docker/dashboard.Dockerfile" "fraud-jobs:phase8|docker/jobs.Dockerfile")
  for entry in "${images[@]}"; do
    image="${entry%%|*}"
    dockerfile="${entry#*|}"
    if docker image inspect "$image" >/dev/null 2>&1; then
      say "Image $image is already available."
      continue
    fi
    say "Building $image. The first build can take about 15–25 minutes because packages and the Feast store are large."
    docker build --file "$ROOT/$dockerfile" --tag "$image" "$ROOT" || fail "Building $image failed. See output above and $LOG_FILE."
  done
}

container_health() {
  local service="$1" container_id status
  container_id="$("${dc[@]}" ps --quiet "$service" 2>/dev/null || true)"
  [[ -n "$container_id" ]] || return 1
  status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id" 2>/dev/null || true)"
  [[ "$status" == "healthy" ]]
}

http_ready() { curl --silent --show-error --fail --max-time 3 "$1" >/dev/null 2>&1; }

wait_ready() {
  local service="$1" url="$2" deadline=$((SECONDS + health_timeout))
  say "Waiting for $service to become healthy..."
  while (( SECONDS < deadline )); do
    if container_health "$service" && { [[ -z "$url" ]] || http_ready "$url"; }; then say "$service is healthy."; return; fi
    if (( SECONDS % 15 < 5 )); then say "Still waiting for $service..."; fi
    sleep 5
  done
  "${dc[@]}" logs --no-color --tail=80 "$service" || true
  fail "$service did not become healthy within the timeout. See $LOG_FILE."
}

metric_value() {
  local key="$1" payload="$2"
  printf '%s' "$payload" | "${dc[@]}" exec --no-TTY api python -c 'import json,sys; print(json.load(sys.stdin)[sys.argv[1]])' "$key"
}

wait_for_scores() {
  local deadline=$((SECONDS + score_timeout)) payload count
  say "Waiting for the API to report at least 300 scored transactions..."
  while (( SECONDS < deadline )); do
    payload="$(curl --silent --show-error --fail --max-time 5 http://localhost:8000/metrics-lite 2>/dev/null || true)"
    if [[ -n "$payload" ]]; then
      count="$(metric_value score_count "$payload" 2>/dev/null || true)"
      if [[ "$count" =~ ^[0-9]+$ ]] && (( count >= 300 )); then say "Score count is $count."; return; fi
      if [[ "$count" =~ ^[0-9]+$ ]] && (( count % 50 == 0 )); then say "Scored $count transactions so far."; fi
    fi
    sleep 5
  done
  fail "The API did not reach the required score count. Check demo_logs and run CHECK_DEMO.bat."
}

ensure_docker
check_project_inputs
check_ports
build_missing_images

say "Stopping any previous demo containers and clearing only the serving database for a predictable run."
"${dc[@]}" down --remove-orphans
docker volume rm fraud-platform-demo-serving >/dev/null 2>&1 || true
"${dc[@]}" run --rm --no-deps --entrypoint /bin/sh api -c 'rm -f /runtime/serving.db*'

say "Starting Kafka, MLflow, scorer API, consumer, and dashboard."
"${dc[@]}" up --detach
wait_ready kafka ""
wait_ready mlflow http://localhost:5000/health
wait_ready api http://localhost:8000/health
wait_ready dashboard http://localhost:8501/_stcore/health

say "Ensuring the demo topics exist."
"${dc[@]}" exec --no-TTY kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:29092 --create --if-not-exists --topic transactions --partitions 1 --replication-factor 1
"${dc[@]}" exec --no-TTY kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:29092 --create --if-not-exists --topic fraud-scores --partitions 1 --replication-factor 1

say "Replaying 300 chronological test transactions through Kafka at 20 transactions per second."
if ! "${dc[@]}" run --rm producer; then
  say "Kafka replay failed. Resetting the serving DB and using the existing seed script so the dashboard can show cases."
  "${dc[@]}" stop api consumer
  "${dc[@]}" rm --force api consumer
  docker volume rm fraud-platform-demo-serving >/dev/null 2>&1 || true
  "${dc[@]}" up --detach api consumer
  wait_ready api http://localhost:8000/health
  "${dc[@]}" run --rm --no-deps api python -m scripts.seed_demo_alerts --limit 300 --database /runtime/serving.db
fi

wait_for_scores
alerts="$(curl --silent --show-error --fail http://localhost:8000/metrics-lite | "${dc[@]}" exec --no-TTY api python -c 'import json,sys; print(json.load(sys.stdin)["alert_count"])')"
if [[ "$alerts" == "0" ]]; then
  say "Replay produced no alert cases. Adding the existing test-split seed sample for dashboard review."
  "${dc[@]}" run --rm --no-deps api python -m scripts.seed_demo_alerts --limit 300 --database /runtime/serving.db
fi
alerts="$(curl --silent --show-error --fail http://localhost:8000/metrics-lite | "${dc[@]}" exec --no-TTY api python -c 'import json,sys; print(json.load(sys.stdin)["alert_count"])')"
[[ "$alerts" =~ ^[0-9]+$ ]] && (( alerts > 0 )) || fail "No alerts were produced by replay or the seed fallback. Check the demo logs before using the dashboard."

"${dc[@]}" logs --no-color >"$LOG_DIR/compose.log" 2>&1 || true
say "Demo is ready."
say "Dashboard: http://localhost:8501"
say "Scoring API: http://localhost:8000/health"
say "Metrics: http://localhost:8000/metrics-lite"
say "MLflow: http://localhost:5000"
say "Run ./scripts/demo_check.sh to verify. Full log: $LOG_FILE"
