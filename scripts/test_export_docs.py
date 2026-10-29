#!/usr/bin/env python3
"""scripts/export-docs.py 的整体验收。

  python3 scripts/test_export_docs.py                         只跑用临时 vault 的部分
  OBSIDIAN_VAULT=<vault 路径> python3 scripts/test_export_docs.py   再加上真实 vault 的检查
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest
import urllib.parse

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "export-docs.py")
HEADER = "由 Obsidian 导出，请勿直接修改"
NOT_EXPORTED = ["路线图", "待争论问题", "实践日志", "讨论日志"]


def run(*args):
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)


def note(status, body):
    return f"---\ntags: [code-agent]\ncreated: 2026-10-28\nstatus: {status}\n---\n\n{body}"


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def md_links(text):
    return re.findall(r"\]\(([^)]+\.md)\)", text)


class FixtureVault(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = os.path.join(self.tmp.name, "vault")
        self.out = os.path.join(self.tmp.name, "docs")
        notes = os.path.join(self.vault, "code-agents", "笔记")
        write(os.path.join(notes, "方法论总览.md"), note("共识",
              "# 方法论总览\n\n> 总览的一句话说明。\n\n见 [[分级规则]] 和 [[并行多 agent]]，原始讨论见 [[待争论问题]] 第 1 题。\n"))
        write(os.path.join(notes, "分级规则.md"), note("共识",
              "# 分级规则\n\n> 分级的一句话说明。\n\n回到 [[方法论总览]]。依据见 [[读书：某书]]。\n"))
        write(os.path.join(notes, "并行多 agent.md"), note("共识",
              "# 并行多 agent\n\n> 并行的一句话说明。\n\n相关：[[分级规则]]\n"))
        write(os.path.join(notes, "路线图.md"), note("共识", "# 路线图\n\n见 [[实践日志]]\n"))
        write(os.path.join(notes, "待争论问题.md"), note("进行中", "# 待争论问题\n"))
        write(os.path.join(notes, "实践日志.md"), note("进行中", "# 实践日志\n"))
        write(os.path.join(notes, "读书：某书.md"), note("资料", "# 读书：某书\n"))
        write(os.path.join(self.vault, "code-agents", "讨论日志", "2026-10-27.md"), "# 讨论\n")

    def tearDown(self):
        self.tmp.cleanup()

    def export(self):
        r = run("--vault", self.vault, "--out", self.out)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_exports_only_consensus_notes_except_roadmap(self):
        self.export()
        self.assertEqual(sorted(os.listdir(self.out)),
                         sorted(["README.md", "方法论总览.md", "分级规则.md", "并行多 agent.md"]))

    def test_header_replaces_frontmatter(self):
        self.export()
        for name in ["方法论总览.md", "分级规则.md", "并行多 agent.md"]:
            text = read(os.path.join(self.out, name))
            self.assertIn(HEADER, text.splitlines()[0], name)
            self.assertNotIn("status:", text, name)
            self.assertNotIn("tags:", text, name)

    def test_links_between_exported_notes_become_relative(self):
        self.export()
        text = read(os.path.join(self.out, "方法论总览.md"))
        self.assertIn("[分级规则](分级规则.md)", text)
        self.assertIn("[并行多 agent](并行多%20agent.md)", text)
        self.assertIn("[方法论总览](方法论总览.md)", read(os.path.join(self.out, "分级规则.md")))

    def test_links_to_unexported_notes_keep_only_text(self):
        self.export()
        overview = read(os.path.join(self.out, "方法论总览.md"))
        self.assertIn("原始讨论见 待争论问题 第 1 题", overview)
        self.assertIn("依据见 读书：某书。", read(os.path.join(self.out, "分级规则.md")))
        for name in os.listdir(self.out):
            self.assertNotIn("[[", read(os.path.join(self.out, name)), name)

    def test_index_follows_overview_order_and_explains_unlinked_names(self):
        self.export()
        index = read(os.path.join(self.out, "README.md"))
        self.assertIn(HEADER, index.splitlines()[0])
        self.assertIn("未公开", index)
        # 总览第一，其余按总览里第一次链接到它们的顺序
        self.assertEqual(md_links(index), ["方法论总览.md", "分级规则.md", "并行多%20agent.md"])

    def test_check(self):
        self.export()
        self.assertEqual(run("--vault", self.vault, "--out", self.out, "--check").returncode, 0)
        # docs/ 被直接改过
        path = os.path.join(self.out, "分级规则.md")
        write(path, read(path) + "\n手改的一行\n")
        self.assertNotEqual(run("--vault", self.vault, "--out", self.out, "--check").returncode, 0)
        self.export()
        # docs/ 里多了不该有的文件
        write(os.path.join(self.out, "旧笔记.md"), "x\n")
        self.assertNotEqual(run("--vault", self.vault, "--out", self.out, "--check").returncode, 0)
        self.export()
        self.assertFalse(os.path.exists(os.path.join(self.out, "旧笔记.md")))
        # 笔记改了没导出
        src = os.path.join(self.vault, "code-agents", "笔记", "分级规则.md")
        write(src, read(src) + "\n新增一段\n")
        self.assertNotEqual(run("--vault", self.vault, "--out", self.out, "--check").returncode, 0)


@unittest.skipUnless(os.environ.get("OBSIDIAN_VAULT"), "没设 OBSIDIAN_VAULT，跳过真实 vault 检查")
class RealVault(unittest.TestCase):
    def test_real_vault(self):
        with tempfile.TemporaryDirectory() as out:
            r = run("--vault", os.environ["OBSIDIAN_VAULT"], "--out", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            names = sorted(os.listdir(out))
            self.assertEqual(len(names), 14, names)  # 13 篇共识笔记 + README
            for name in names:
                self.assertFalse(any(x in name for x in NOT_EXPORTED), name)
                text = read(os.path.join(out, name))
                self.assertNotIn("[[", text, name)
                self.assertIn(HEADER, text.splitlines()[0], name)
                for link in md_links(text):
                    target = os.path.join(out, urllib.parse.unquote(link))
                    self.assertTrue(os.path.isfile(target), f"{name} → {link}")


if __name__ == "__main__":
    unittest.main()
