#!/usr/bin/env bash
# 无 sudo：用户级 pip + virtualenv 创建 .venv（适用于 Debian/Ubuntu PEP 668 环境）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export PIP_BREAK_SYSTEM_PACKAGES=1
export PATH="${HOME}/.local/bin:${PATH}"

if ! command -v pip3 >/dev/null 2>&1 && [[ ! -x "${HOME}/.local/bin/pip" ]]; then
  curl -sS -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
  python3 /tmp/get-pip.py --user
fi

pip install --user virtualenv --break-system-packages -q
virtualenv .venv
.venv/bin/pip install -U pip -q
.venv/bin/pip install -r requirements.txt

echo "完成。启动： .venv/bin/python manage.py runserver 0.0.0.0:8000"
