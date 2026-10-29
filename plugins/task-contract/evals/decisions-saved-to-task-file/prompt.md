---
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, AskUserQuestion]
---

把 app.py 里的用户存储从内存字典改成 SQLite，密码要加盐哈希，现有的 save 函数和已经保存的 json 数据也要迁移过去
