---
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
---

给 app.py 加上登录失败锁定：同一用户连续输错密码 5 次就锁定 15 分钟，锁定状态要能在进程重启后保留
