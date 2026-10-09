#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
project_name="clearview_bi_judge"
cd "$repo_root"

if [[ "${1:-}" == "--stop" ]]; then
  docker compose --project-name "$project_name" down
  echo "Demo containers stopped. The demo database volume was kept."
  exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed. Install Docker Desktop, start it, then retry." >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "Docker Desktop is not running. Start it and wait until the engine is ready." >&2
  exit 1
fi

export CLEARVIEW_DB_HOST_PORT=55432
export CLEARVIEW_MOCK_HOST_PORT=18001
export CLEARVIEW_API_HOST_PORT=18000
export CLEARVIEW_WEB_HOST_PORT=5175

docker compose --project-name "$project_name" up --build -d

health_url="http://127.0.0.1:${CLEARVIEW_API_HOST_PORT}/api/v1/health"
healthy=false
for _ in $(seq 1 60); do
  if curl --fail --silent "$health_url" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"healthy"'; then
    healthy=true
    break
  fi
  sleep 2
done
if [[ "$healthy" != true ]]; then
  echo "The API did not become healthy. Check: docker compose --project-name $project_name logs app postgres" >&2
  exit 1
fi

docker compose --project-name "$project_name" exec -T app python scripts/seed_demo_analytics.py
echo
echo "Clearview BI demo is ready."
echo "Open: http://127.0.0.1:${CLEARVIEW_WEB_HOST_PORT}"
echo "Create a company account to claim the seeded demo workspace. No API keys are required."
echo "To stop the demo and keep its data: bash scripts/judge_demo.sh --stop"
