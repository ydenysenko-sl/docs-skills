#!/usr/bin/env python3
"""
check-links.py <docs-root>

Verifies every relative link under <docs-root>/**/*.md resolves to an existing file or directory.

Scanned:
- HTML  <a href="..."> / <a href='...'>     — anywhere (including inside <pre> blocks per the linked-docs spec)
- Markdown [text](path) / ![alt](path)       — outside fenced code (``` / ~~~) and outside <pre> blocks

Skipped:
- absolute URLs (http://, https://, mailto:)
- root-absolute paths (/...)
- pure anchors (#section)
- fragments are stripped before resolution (path.md#x → path.md)

Exits 0 if every relative link resolves; 1 otherwise with a structured report.
"""
import re
import sys
from pathlib import Path

MD_LINK = re.compile(r'!?\]\(([^)\s]+?)(?:\s+"[^"]*")?\)')
HREF = re.compile(r"""href\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
FENCE = re.compile(r'^\s*(```|~~~)')
PRE_OPEN = re.compile(r'<pre[\s>]', re.IGNORECASE)
PRE_CLOSE = re.compile(r'</pre\s*>', re.IGNORECASE)


def extract_links(text):
    in_fence = False
    fence_marker = None
    in_pre = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if not in_pre:
            m = FENCE.match(line)
            if m:
                if not in_fence:
                    in_fence = True
                    fence_marker = m.group(1)
                elif line.lstrip().startswith(fence_marker):
                    in_fence = False
                    fence_marker = None
                continue

        opened_here = False
        if not in_fence and PRE_OPEN.search(line):
            in_pre = True
            opened_here = True

        for m in HREF.finditer(line):
            yield lineno, 'href', m.group(1)

        if not in_fence and not (in_pre and not opened_here):
            if not in_pre:
                for m in MD_LINK.finditer(line):
                    yield lineno, 'md', m.group(1)

        if PRE_CLOSE.search(line):
            in_pre = False


def is_relative_local(target):
    if target.startswith(('http://', 'https://', 'mailto:', 'tel:', '#')):
        return False
    if target.startswith('/'):
        return False
    return True


def main():
    if len(sys.argv) != 2:
        print("usage: check-links.py <docs-root>", file=sys.stderr)
        sys.exit(2)

    docs_root = Path(sys.argv[1]).resolve()
    if not docs_root.is_dir():
        print(f"ERROR: docs-root not found: {docs_root}", file=sys.stderr)
        sys.exit(2)

    md_files = sorted(docs_root.rglob('*.md'))
    if not md_files:
        print(f"No .md files under {docs_root}")
        sys.exit(0)

    failures = []
    for md in md_files:
        try:
            text = md.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            text = md.read_text(encoding='utf-8', errors='replace')

        for lineno, kind, target in extract_links(text):
            if not is_relative_local(target):
                continue
            path_part = target.split('#', 1)[0]
            if not path_part:
                continue
            resolved = (md.parent / path_part).resolve()
            if not resolved.exists():
                failures.append((md, lineno, kind, target))

    scanned = len(md_files)
    if failures:
        print(f"BROKEN LINKS ({len(failures)} of {scanned} files scanned):")
        last_file = None
        for md, lineno, kind, target in failures:
            rel = md.relative_to(docs_root)
            if rel != last_file:
                print(f"\n  {rel}")
                last_file = rel
            print(f"    L{lineno} [{kind}] → {target}")
        sys.exit(1)

    print(f"OK: all relative links resolve ({scanned} files scanned)")
    sys.exit(0)


if __name__ == '__main__':
    main()
