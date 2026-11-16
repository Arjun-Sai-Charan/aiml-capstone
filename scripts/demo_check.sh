#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT/demo_logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/check-$(date -u +%Y%m%dT%H%M%SZ).log"
exec > >(tee -a "$LOG_FILE") 2>&1
dc=(docker compose --project-name fraud-platform --file "$ROOT/docker/docker-compose.full.yml")
failures=0

report() {
  local name="$1" result="$2" detail="$3"
  if [[ "$result" == "PASS" ]]; then printf 'PASS: %s — %s\n' "$name" "$detail"
  else printf 'FAIL: %s — %s\n' "$name" "$detail"; failures=$((failures + 1)); fi
}

if ! docker info >/dev/null 2>&1; then
  report "Docker reachable" FAIL "Open Docker Desktop and retry."
  for name in "containers up" "API health" "score_count >= 300" "alert_count > 0" "dashboard reachable"; do
    report "$name" FAIL "Docker is unavailable."
  done
  exit 1
fi
report "Docker reachable" PASS "Docker responds."

containers_ok=1
for service in kafka mlflow api consumer dashboard; do
  id="$("${dc[@]}" ps --quiet "$service" 2>/dev/null || true)"
  status=""
  if [[ -n "$id" ]]; then status="$(docker inspect --format '{{.State.Status}}' "$id" 2>/dev/null || true)"; fi
  if [[ "$status" != "running" ]]; then containers_ok=0; fi
done
if (( containers_ok )); then
  report "containers up" PASS "Kafka, MLflow, API, consumer, and dashboard are running."
else
  report "containers up" FAIL "One or more required containers are not running; see docker compose ps."
fi

if curl --silent --show-error --fail --max-time 5 http://localhost:8000/health >/dev/null 2>&1; then
  report "API health" PASS "http://localhost:8000/health responds."
else
  report "API health" FAIL "API health endpoint did not respond."
fi

metrics="$(curl --silent --show-error --fail --max-time 5 http://localhost:8000/metrics-lite 2>/dev/null || true)"
if [[ -n "$metrics" ]]; then
  score_count="$(printf '%s' "$metrics" | "${dc[@]}" exec --no-TTY api python -c 'import json,sys; print(json.load(sys.stdin)["score_count"])' 2>/dev/null || true)"
  alert_count="$(printf '%s' "$metrics" | "${dc[@]}" exec --no-TTY api python -c 'import json,sys; print(json.load(sys.stdin)["alert_count"])' 2>/dev/null || true)"
  if [[ "$score_count" =~ ^[0-9]+$ ]] && (( score_count >= 300 )); then
    report "score_count >= 300" PASS "API reports $score_count scored transactions."
  else
    report "score_count >= 300" FAIL "API reports ${score_count:-unavailable}."
  fi
  if [[ "$alert_count" =~ ^[0-9]+$ ]] && (( alert_count > 0 )); then
    report "alert_count > 0" PASS "API reports $alert_count alerts."
  else
    report "alert_count > 0" FAIL "API reports ${alert_count:-unavailable}."
  fi
else
  report "score_count >= 300" FAIL "Metrics endpoint did not respond."
  report "alert_count > 0" FAIL "Metrics endpoint did not respond."
fi

if curl --silent --show-error --fail --max-time 5 http://localhost:8501/_stcore/health >/dev/null 2>&1; then
  report "dashboard reachable" PASS "http://localhost:8501 responds."
else
  report "dashboard reachable" FAIL "Dashboard health endpoint did not respond."
fi

printf 'Log: %s\n' "$LOG_FILE"
(( failures == 0 ))
