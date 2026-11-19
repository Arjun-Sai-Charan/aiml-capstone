#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT/demo_logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/stop-$(date -u +%Y%m%dT%H%M%SZ).log"
exec > >(tee -a "$LOG_FILE") 2>&1

if ! docker info >/dev/null 2>&1; then
  printf 'Docker is not running. Open Docker Desktop, then try STOP_DEMO.bat again.\n' >&2
  exit 1
fi
docker compose --project-name fraud-platform --file "$ROOT/docker/docker-compose.full.yml" stop
printf '\nDemo containers are stopped. Images and named data volumes were kept.\n'
printf 'Log: %s\n' "$LOG_FILE"
