#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${TMPDIR:-/tmp}/llm-fun"
mkdir -p "$LOG_DIR"
cd "$ROOT_DIR"

if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  source "$ROOT_DIR/.env"
  set +a
fi

for command in uv uvx curl; do
  if ! command -v "$command" >/dev/null 2>&1; then
    printf 'Required command not found: %s\n' "$command" >&2
    exit 1
  fi
done

if [[ -n "${VLLM_BIN:-}" ]]; then
  if ! command -v "$VLLM_BIN" >/dev/null 2>&1; then
    printf 'vLLM executable not found: %s\n' "$VLLM_BIN" >&2
    exit 1
  fi
  VLLM_BIN="$(command -v "$VLLM_BIN")"
elif command -v vllm >/dev/null 2>&1; then
  VLLM_BIN="$(command -v vllm)"
elif [[ -x "$HOME/.venv-vllm-metal/bin/vllm" ]]; then
  VLLM_BIN="$HOME/.venv-vllm-metal/bin/vllm"
else
  printf 'vllm not found. Install the vLLM Metal environment, add vllm to PATH, or set VLLM_BIN.\n' >&2
  exit 1
fi

service_pids=()
service_pid=""

cleanup() {
  local pid
  for pid in "${service_pids[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  for pid in "${service_pids[@]}"; do
    wait "$pid" 2>/dev/null || true
  done
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

start_service() {
  local name="$1"
  shift
  printf 'Starting %s; log: %s/%s.log\n' "$name" "$LOG_DIR" "$name"
  "$@" >"$LOG_DIR/$name.log" 2>&1 &
  service_pid="$!"
  service_pids+=("$service_pid")
}

wait_for_health() {
  local name="$1"
  local url="$2"
  local pid="$3"
  local elapsed

  for ((elapsed = 0; elapsed < 600; elapsed += 2)); do
    if curl --silent --fail "$url" >/dev/null; then
      printf '%s is ready.\n' "$name"
      return
    fi
    if ! kill -0 "$pid" 2>/dev/null; then
      printf '%s exited during startup; see %s/%s.log\n' "$name" "$LOG_DIR" "$name" >&2
      tail -n 40 "$LOG_DIR/$name.log" >&2
      exit 1
    fi
    sleep 2
  done

  printf 'Timed out waiting for %s; see %s/%s.log\n' "$name" "$LOG_DIR" "$name" >&2
  tail -n 40 "$LOG_DIR/$name.log" >&2
  exit 1
}

start_service qwen \
  "$VLLM_BIN" serve --stream-interval 8 --max-model-len 4096 \
    mlx-community/Qwen2.5-7B-Instruct-4bit \
    --enable-auto-tool-choice --tool-call-parser hermes --port 8001
wait_for_health qwen http://127.0.0.1:8001/health "$service_pid"

start_service litellm \
  uvx --from 'litellm[proxy]' litellm --config "$ROOT_DIR/litellm.yaml" --port 4000
wait_for_health litellm http://127.0.0.1:4000/health/liveliness "$service_pid"

printf 'All services are ready. Starting the agent; type quit to stop.\n'
uv run python agent.py