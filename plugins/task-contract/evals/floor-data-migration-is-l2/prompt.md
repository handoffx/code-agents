---
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
---

把 save 函数写出的 json 里的字段改个名：顶层改成 {"users": {...}} 的结构，已经存在的 json 数据文件也一起转换成新格式
