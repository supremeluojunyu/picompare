#!/usr/bin/env bash
# 开发环境：停止旧进程并启动 Django（监听 0.0.0.0:8000）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -x .venv/bin/python ]]; then
  echo "未找到 .venv。无 sudo 可执行： bash deployment/setup_venv_no_sudo.sh"
  echo "有 sudo 可执行： sudo apt install -y python3-venv && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

pkill -f "$ROOT.*manage.py runserver" 2>/dev/null || true
sleep 1

.venv/bin/python manage.py migrate --noinput
exec .venv/bin/python manage.py runserver 0.0.0.0:8000
