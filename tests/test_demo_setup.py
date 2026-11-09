from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPOSE_PATH = ROOT / "docker/docker-compose.full.yml"


def _make_targets() -> set[str]:
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    return set(re.findall(r"^([A-Za-z0-9_.-]+):", text, re.MULTILINE))


def test_demo_scripts_are_strict_and_windows_launchers_call_them():
    for script in ("demo_start.sh", "demo_stop.sh", "demo_check.sh"):
        text = (ROOT / "scripts" / script).read_text(encoding="utf-8")
        assert text.startswith("#!/usr/bin/env bash\n")
        assert "set -Eeuo pipefail" in text
        assert (ROOT / "scripts" / script).stat().st_mode & 0o111

    expected = {
        "START_DEMO.bat": "demo_start.sh",
        "STOP_DEMO.bat": "demo_stop.sh",
        "CHECK_DEMO.bat": "demo_check.sh",
    }
    for batch, script in expected.items():
        text = (ROOT / batch).read_text(encoding="utf-8")
        assert f"wsl.exe -d Ubuntu -- bash -lc \"cd ~/fraud-platform && ./scripts/{script}\"" in text
        assert "if errorlevel 1 goto failed" in text
        assert ":failed" in text and "pause" in text
    assert "http://localhost:8501" in (ROOT / "START_DEMO.bat").read_text(encoding="utf-8")


def test_compose_services_ports_images_and_environment_match_demo_controls():
    compose = yaml.safe_load(COMPOSE_PATH.read_text(encoding="utf-8"))
    services = compose["services"]
    assert set(services) == {"kafka", "mlflow", "api", "consumer", "dashboard", "producer"}

    host_ports = {
        int(port.split(":", 1)[0])
        for service in services.values()
        for port in service.get("ports", [])
    }
    assert host_ports == {8000, 8501, 9092, 5000}
    starter = (ROOT / "scripts/demo_start.sh").read_text(encoding="utf-8")
    checker = (ROOT / "scripts/demo_check.sh").read_text(encoding="utf-8")
    for port in (8000, 8501, 9092, 5000):
        assert str(port) in starter
    for port in (8000, 8501):
        assert str(port) in checker

    expected_images = {
        "fraud-api:phase8",
        "fraud-dashboard:phase8",
        "fraud-jobs:phase8",
    }
    compose_images = {service["image"] for service in services.values() if service["image"].startswith("fraud-")}
    built_images = set(re.findall(r'"(fraud-[a-z]+:phase8)\|', starter))
    assert compose_images == built_images == expected_images

    assert services["api"]["environment"] == {
        "FRAUD_SERVING_DB_PATH": "/runtime/serving.db",
        "FRAUD_MODEL_SOURCE": "local",
        "KAFKA_BOOTSTRAP_DOCKER": "kafka:29092",
        "MLFLOW_TRACKING_URI": "http://mlflow:5000",
    }
    assert services["consumer"]["environment"] == services["api"]["environment"]
    assert services["dashboard"]["environment"] == {"FRAUD_API_URL": "http://api:8000"}
    assert services["producer"]["environment"] == {"KAFKA_BOOTSTRAP_DOCKER": "kafka:29092"}
    assert "${DEMO_TRANSACTION_LIMIT:-300}" in " ".join(services["producer"]["command"])
    assert "${DEMO_PRODUCER_RATE:-20}" in " ".join(services["producer"]["command"])


def test_compose_has_health_gates_restarts_one_shot_producer_and_memory_budget():
    services = yaml.safe_load(COMPOSE_PATH.read_text(encoding="utf-8"))["services"]
    for name in ("kafka", "mlflow", "api", "dashboard"):
        assert services[name].get("healthcheck"), name
    assert services["api"]["depends_on"]["kafka"]["condition"] == "service_healthy"
    assert services["api"]["depends_on"]["mlflow"]["condition"] == "service_healthy"
    assert services["consumer"]["depends_on"]["kafka"]["condition"] == "service_healthy"
    assert services["dashboard"]["depends_on"]["api"]["condition"] == "service_healthy"
    for name in ("kafka", "mlflow", "api", "consumer", "dashboard"):
        assert services[name]["restart"] == "unless-stopped"
    assert services["producer"]["restart"] == "no"
    assert services["producer"]["profiles"] == ["manual-demo"]
    assert services["producer"]["depends_on"]["kafka"]["condition"] == "service_healthy"
    limits_mb = sum(int(service["mem_limit"].removesuffix("m")) for service in services.values())
    assert limits_mb < 10 * 1024
    assert services["api"]["volumes"] == services["consumer"]["volumes"]


def test_make_documented_targets_exist_and_push_is_not_implicit():
    targets = _make_targets()
    docs = [ROOT / "README.md", *Path(ROOT / "docs").rglob("*.md")]
    referenced = set()
    for path in docs:
        text = path.read_text(encoding="utf-8")
        code = re.findall(r"```[A-Za-z0-9_-]*\n(.*?)```|`([^`]+)`", text, re.DOTALL)
        for block, inline in code:
            referenced.update(re.findall(r"\bmake\s+([A-Za-z][A-Za-z0-9_-]*)", block or inline))
    assert referenced <= targets, sorted(referenced - targets)

    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    push_recipe = makefile.split("push:\n", 1)[1]
    assert 'git rebase origin/main --exec "git commit --amend --reset-author --no-edit"' in push_recipe
    assert push_recipe.index("git rebase origin/main") < push_recipe.index("git push")


def test_k8s_build_loads_host_images_and_up_does_not_launch_producer():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    build_recipe = makefile.split("k8s-build:\n", 1)[1].split("\nk8s-up:", 1)[0]
    assert "docker build" in build_recipe and "minikube image load" in build_recipe
    assert "minikube docker-env" not in build_recipe
    for image in ("fraud-api:phase8", "fraud-dashboard:phase8", "fraud-jobs:phase8"):
        assert image in build_recipe
    up_recipe = makefile.split("k8s-up:\n", 1)[1].split("\nk8s-demo:", 1)[0]
    demo_recipe = makefile.split("k8s-demo:\n", 1)[1].split("\nk8s-status:", 1)[0]
    assert "61-producer-job.yaml" not in up_recipe
    assert "kubectl apply -f k8s/\n" not in up_recipe
    assert "61-producer-job.yaml" in demo_recipe
    assert (ROOT / "k8s/60-jobs.yaml").read_text(encoding="utf-8").count("kind: Job") == 0
    assert "kind: Job" in (ROOT / "k8s/61-producer-job.yaml").read_text(encoding="utf-8")
    kafka = next(yaml.safe_load_all((ROOT / "k8s/20-kafka.yaml").read_text(encoding="utf-8")))
    broker = kafka["spec"]["template"]["spec"]
    assert broker["securityContext"]["runAsUser"] == 1000


def test_demo_logs_and_audit_are_ignored():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "demo_logs/" in ignore
    assert "audit/" in ignore
