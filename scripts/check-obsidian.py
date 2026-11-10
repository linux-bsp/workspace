#!/usr/bin/env python3
"""Check SadBoard's Obsidian note links, headings, cases and local source paths."""

import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "docs/obsidian/sadboard"
WIKI = re.compile(r"\[\[([^\]\n]+)\]\]")
LINK = re.compile(r"\[([^\]\n]+)\]\(([^)\n]+)\)")
CASE_FOLDER = re.compile(r"([AB]-[A-Z]+\d{2})-\S.*")
REPOS = {
    "linux-bsp/linux-7.0": ROOT / "linux/linux-7.0",
    "linux-bsp/sadboard-external": ROOT / "sadboard-external",
    "linux-bsp/workspace": ROOT,
}


def outside_code(text, transform):
    """Do not interpret shell comments or fenced Markdown examples as note syntax."""
    fence = None
    output = []
    for line in text.splitlines(keepends=True):
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\n"))
        if match:
            token, suffix = match.groups()
            if fence is None:
                fence = (token[0], len(token))
            elif token[0] == fence[0] and len(token) >= fence[1] and not suffix.strip():
                fence = None
            output.append(line)
        else:
            output.append(line if fence else transform(line))
    if fence:
        raise ValueError("Unclosed fenced code block")
    return "".join(output)


def headings(text):
    found = []

    def collect(line):
        match = re.match(r"^(#{1,6}) (.+)", line)
        if match:
            title = match[2].replace("`", "").replace("**", "").replace("__", "")
            found.append((len(match[1]), re.sub(r"\s+#+\s*$", "", title).strip()))
        return line

    outside_code(text, collect)
    return found


def read_notes():
    notes = {}
    for note in sorted(VAULT.rglob("*.md")):
        parts = note.relative_to(VAULT).parts
        if any(part.startswith(".") for part in parts):
            continue
        name = note.relative_to(VAULT).as_posix()[:-3]
        if name.startswith("实验记录/"):
            continue
        notes[name] = note.read_text()
    return notes


def validate(notes):
    errors = []
    link_count = 0
    source_paths = set()
    graph = {name: set() for name in notes}
    note_headings = {name: headings(text) for name, text in notes.items()}
    for name, text in notes.items():
        if text.startswith("---\n"):
            errors.append(f"{name}: keep note properties out of the handbook")
        if any(level == 1 for level, _ in note_headings[name]):
            errors.append(f"{name}: use the filename as the title; body headings start at ##")

        def check_line(line):
            nonlocal link_count
            for match in WIKI.finditer(line):
                target = match[1].replace("\\|", "|").split("|", 1)[0]
                path, sep, heading = target.partition("#")
                path = path.removesuffix(".md") or name
                link_count += 1
                if path not in notes:
                    errors.append(f"{name}: missing note {path}")
                elif sep and heading not in {title for _, title in note_headings[path]}:
                    errors.append(f"{name}: missing heading {target}")
                else:
                    graph[name].add(path)
            for match in LINK.finditer(line):
                target = match[2]
                if not target.startswith(("https://", "http://", "mailto:")):
                    errors.append(f"{name}: use a vault link or a source URL: {target}")
                url = urlsplit(target)
                source = re.fullmatch(r"/([^/]+/[^/]+)/blob/[^/]+/(.+)", url.path)
                if url.netloc == "github.com" and source and source[1] in REPOS:
                    local = REPOS[source[1]] / unquote(source[2])
                    source_paths.add(local)
                    if not local.exists():
                        errors.append(f"{name}: missing workspace source {local.relative_to(ROOT)}")
            return line

        outside_code(text, check_line)
    cases = []
    case_notes = set()
    for name in notes:
        path = Path(name)
        match = CASE_FOLDER.fullmatch(path.parent.name)
        if match:
            case_id = match[1]
            cases.append(case_id)
            case_notes.add(name)
            title = re.fullmatch(r"([AB]-[A-Z]+\d{2})：\S.*", path.name)
            if not title or title[1] != case_id:
                errors.append(f"{name}: case filename must use {case_id}：<actual-title>.md")
        elif re.match(r"[AB]-[A-Z]+\d{2}：", path.name):
            errors.append(f"{name}: case directory must use <case-id>-<specific-problem>")
    tool_notes = {name for name in notes if name.startswith("工具手册/")}
    for name in case_notes:
        for tool in graph[name] & tool_notes:
            if name not in graph[tool]:
                errors.append(f"{tool}: add a usage-scenario backlink to {name}")
    for name in tool_notes:
        if not graph[name] & case_notes:
            errors.append(f"{name}: link to at least one concrete usage scenario")
    expected = {
        *[f"B-{family}{n:02d}" for family in ("CR", "FD", "MM", "CPU", "SYNC", "NET", "BOOT") for n in range(1, 6)],
        *[f"A-{family}{n:02d}" for family in ("P", "M", "N") for n in range(1, 9)],
    }
    if set(cases) != expected or len(cases) != len(expected):
        errors.append("Expected 35 basic and 24 advanced distinct cases")
    reachable, pending = set(), ["首页"]
    while pending:
        name = pending.pop()
        if name not in reachable:
            reachable.add(name)
            pending.extend(graph.get(name, set()) - reachable)
    for name in notes.keys() - reachable:
        errors.append(f"{name}: not reachable from 首页")
    if errors:
        raise ValueError("\n".join(sorted(set(errors))))
    counts = Counter(case.split("-", 1)[0] for case in cases)
    return f"{len(notes)} notes; {counts['B']} basic + {counts['A']} advanced cases; {link_count} valid wiki links; {len(source_paths)} source paths checked"


def main():
    try:
        print(validate(read_notes()))
    except (ValueError, OSError) as error:
        print(f"obsidian: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
