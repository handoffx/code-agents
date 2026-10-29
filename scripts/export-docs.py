#!/usr/bin/env python3
"""把 Obsidian 里的方法论笔记单向导出到仓库 docs/。

Obsidian 是唯一来源，docs/ 只由本脚本生成：
- 只导出 status 为共识的笔记，路线图除外
- 去掉 frontmatter，第一行注明"由 Obsidian 导出，请勿直接修改"
- 导出笔记之间的 [[双链]] 转成相对链接；指向不导出笔记的只保留文字
- 生成 docs/README.md 索引：方法论总览第一，其余按总览里第一次链接到它们的顺序

用法：
  scripts/export-docs.py [--vault <vault 路径>] [--out docs]   导出（--vault 默认读 OBSIDIAN_VAULT）
  scripts/export-docs.py --check                               只比较，不写文件；docs/ 与笔记不一致时退出码 1
"""
import argparse
import os
import re
import sys

NOTES_SUBDIR = os.path.join("code-agents", "笔记")
EXPORT_STATUS = "共识"
EXCLUDED = {"路线图"}
OVERVIEW = "方法论总览"
INDEX = "README.md"
HEADER = "> 由 Obsidian 导出，请勿直接修改。要修改请改 Obsidian 里的原笔记，再运行 `scripts/export-docs.py`。"
INDEX_BODY = """# 方法论笔记

code-agents 方法论的完整笔记，从作者的 Obsidian 笔记单向导出。仓库 README 的"方法论"一节是它的概述，建议从下面第一篇"方法论总览"读起。

正文里没有链接的笔记名（如"待争论问题""读书：……"）是未公开的内部笔记：讨论记录、读书笔记和调研资料。

"""
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
WIKILINK = re.compile(r"(!?)\[\[([^\]]+)\]\]")
# 行内代码和代码块里的 [[...]] 是字面文字，不转换
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)


def load_notes(vault):
    d = os.path.join(vault, NOTES_SUBDIR)
    if not os.path.isdir(d):
        sys.exit(f"找不到笔记目录：{d}")
    notes = {}
    for name in sorted(os.listdir(d)):
        if not name.endswith(".md"):
            continue
        with open(os.path.join(d, name), encoding="utf-8") as f:
            text = f.read()
        m = FRONTMATTER.match(text)
        status = ""
        if m:
            s = re.search(r"^status:\s*(.*)$", m.group(1), re.M)
            status = s.group(1).strip() if s else ""
            text = text[m.end():]
        notes[name[:-3]] = (status, text)
    return notes


def link_path(name):
    return name.replace(" ", "%20") + ".md"


def convert_links(text, exported, source):
    def repl(m):
        embed, inner = m.groups()
        target, _, alias = inner.partition("|")
        if embed or "#" in target:
            sys.exit(f"{source}：不支持的双链写法 {m.group(0)}（嵌入或标题链接），请改写笔记或扩展本脚本")
        label = alias or target
        return f"[{label}]({link_path(target)})" if target in exported else label

    out, pos = [], 0
    for c in CODE.finditer(text):
        out.append(WIKILINK.sub(repl, text[pos:c.start()]))
        out.append(c.group(0))
        pos = c.end()
    out.append(WIKILINK.sub(repl, text[pos:]))
    return "".join(out)


def render(vault):
    notes = load_notes(vault)
    exported = [n for n, (status, _) in notes.items() if status == EXPORT_STATUS and n not in EXCLUDED]
    files = {}
    for name in exported:
        body = convert_links(notes[name][1], set(exported), name).strip("\n")
        files[name + ".md"] = f"{HEADER}\n\n{body}\n"

    order = [OVERVIEW] if OVERVIEW in exported else []
    if OVERVIEW in notes:
        for m in WIKILINK.finditer(notes[OVERVIEW][1]):
            target = m.group(2).partition("|")[0]
            if target in exported and target not in order:
                order.append(target)
    order += [n for n in exported if n not in order]
    items = "".join(f"- [{n}]({link_path(n)})\n" for n in order)
    files[INDEX] = f"{HEADER}\n\n{INDEX_BODY}{items}"
    return files


def existing(out):
    if not os.path.isdir(out):
        return {}
    files = {}
    for name in sorted(os.listdir(out)):
        if name.endswith(".md"):
            with open(os.path.join(out, name), encoding="utf-8") as f:
                files[name] = f.read()
    return files


def main():
    p = argparse.ArgumentParser(prog="export-docs")
    p.add_argument("--vault", default=os.environ.get("OBSIDIAN_VAULT"),
                   help="Obsidian vault 根目录，默认读环境变量 OBSIDIAN_VAULT")
    p.add_argument("--out", default=os.path.join(REPO_ROOT, "docs"), help="输出目录，默认仓库的 docs/")
    p.add_argument("--check", action="store_true", help="只比较，不写文件")
    a = p.parse_args()
    if not a.vault:
        sys.exit("请用 --vault 或环境变量 OBSIDIAN_VAULT 指定 Obsidian vault 的路径")

    want, have = render(a.vault), existing(a.out)
    if a.check:
        problems = [f"缺少：{n}" for n in want if n not in have]
        problems += [f"内容不一致：{n}" for n in want if n in have and have[n] != want[n]]
        problems += [f"多余：{n}" for n in have if n not in want]
        if problems:
            print(f"{a.out} 与 Obsidian 笔记不一致，运行 scripts/export-docs.py 重新导出：")
            print("\n".join(f"  {x}" for x in problems))
            sys.exit(1)
        print(f"{a.out} 与 Obsidian 笔记一致（{len(want)} 个文件）")
        return

    os.makedirs(a.out, exist_ok=True)
    for name in have:
        if name not in want:
            os.remove(os.path.join(a.out, name))
    for name, text in want.items():
        with open(os.path.join(a.out, name), "w", encoding="utf-8") as f:
            f.write(text)
    print(f"已导出 {len(want)} 个文件到 {a.out}")


if __name__ == "__main__":
    main()
