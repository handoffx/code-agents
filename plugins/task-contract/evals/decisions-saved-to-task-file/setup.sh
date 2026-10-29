#!/bin/bash
# 一个小 Python 项目：用户存储在内存字典里，save 写明文 JSON
set -euo pipefail
git init -q
cat > app.py <<'PY'
import json
USERS = {}
def register(name, pw):
    USERS[name] = pw
def login(name, pw):
    return USERS.get(name) == pw
def save(path):
    json.dump(USERS, open(path, "w"))
PY
git add app.py
git -c user.name=eval -c user.email=eval@example.com commit -qm init
