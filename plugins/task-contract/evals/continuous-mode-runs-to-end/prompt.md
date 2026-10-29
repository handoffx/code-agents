---
max_turns: 80
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill]
---

给 app.py 加上登录失败锁定：同一用户连续输错密码 5 次就锁定 15 分钟，锁定状态要能在进程重启后保留。再写 test_app.py 覆盖锁定和解锁，用 python3 -m unittest 跑通。决策都交给你判断，拆解也不用等我确认，决策后一口气做完，我不在电脑前。
