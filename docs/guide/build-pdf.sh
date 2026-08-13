#!/usr/bin/env bash
# build-pdf.sh — assemble the shed build guide pages into one PDF for the job site.
#
# Prerequisite (already on this machine; the script installs nothing):
#   * python3 with the standard library
#   * WeasyPrint — the `weasyprint` command, or importable by python3
#     (checked below; /usr/bin/weasyprint as of 2026-08-13)
#
# Usage:
#   docs/guide/build-pdf.sh              # writes docs/guide/build-guide.pdf
#   docs/guide/build-pdf.sh out.pdf      # or a path of your choice
#   PAPER=letter docs/guide/build-pdf.sh # A4 is the default page size
#
# Pages are assembled in the canonical reading order from the shared contract.
# Pages that do not exist yet are skipped with a warning, never a failure, so the
# PDF always reflects what is written so far.

set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$DIR/build-guide.pdf}"

PAGES=(
  index.md
  01-what-youre-building.md
  02-order-framing.md
  03-order-finish.md
  04-blocks-and-skids.md
  05-floor.md
  06-front-wall.md
  07-back-wall.md
  08-side-walls.md
  09-raise-and-brace.md
  10-rake-plates.md
  11-rafters.md
  12-fascia-and-roof.md
  13-skirt-and-siding.md
  14-trim.md
  15-doors.md
  16-troubleshooting.md
  r01-cut-list.md
  r02-sources.md
)

EXISTING=()
for p in "${PAGES[@]}"; do
  if [ -f "$DIR/$p" ]; then
    EXISTING+=("$p")
  else
    echo "warning: $p not written yet — skipped" >&2
  fi
done

if [ "${#EXISTING[@]}" -eq 0 ]; then
  echo "error: no guide pages found in $DIR" >&2
  exit 1
fi

if ! command -v weasyprint >/dev/null 2>&1 && ! python3 -c 'import weasyprint' 2>/dev/null; then
  echo "error: WeasyPrint not found (need the weasyprint command or python3 module)" >&2
  exit 1
fi

python3 - "$DIR" "$OUT" "${EXISTING[@]}" <<'PY'
import html
import os
import re
import sys

guide_dir, out_path, pages = sys.argv[1], sys.argv[2], sys.argv[3:]

css = open(os.path.join(guide_dir, "assets", "guide.css"), encoding="utf-8").read()
if os.environ.get("PAPER", "").strip().lower() == "letter":
    css += "\n@page { size: letter; }\n"


def parse_front_matter(text):
    fm = {}
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            for line in text[4:end].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip()
            text = text[end + 5:]
    return fm, text


def inline(s):
    # markdown backslash escapes (\" etc.) must not reach the paper; the
    # guide's quoted-inch idiom "…\"" renders as a single closing quote
    s = s.replace('\\""', '"')
    s = re.sub(r'\\(["`*\\])', r'\1', s)
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', s)
    s = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',
               lambda m: f'<img src="{m.group(2)}" alt="{m.group(1)}"/>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
    return s


def join_wrapped_images(lines):
    """A figure ref may be wrapped over source lines; rejoin it to one line so
    the standalone-figure rule below sees it (Markdown wraps inline freely)."""
    merged, buf = [], ''
    for line in lines:
        s = line.strip()
        if buf:
            buf += ' ' + s
            if re.search(r'\]\([^)]+\)$', buf):
                merged.append(buf)
                buf = ''
            continue
        if s.startswith('![') and not re.search(r'\]\([^)]+\)$', s):
            buf = s
            continue
        merged.append(line)
    if buf:
        merged.append(buf)
    return merged


def convert(md_text):
    """Convert the Markdown subset the contract's page format uses."""
    out = []
    lines = join_wrapped_images(md_text.splitlines())
    i = 0
    para = []

    def flush_para():
        if para:
            # join wrapped source lines first, then mark up: emphasis spans
            # that wrap across a line break must survive as one span
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            flush_para()
            i += 1
            continue

        m = re.match(r'^(#{1,4})\s+(.*)$', stripped)
        if m:
            flush_para()
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue

        if stripped == "---":
            flush_para()
            out.append("<hr/>")
            i += 1
            continue

        m = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)$', stripped)
        if m:
            flush_para()
            if 'birdsmouth-template' in m.group(2):
                # true-size sheet: the figure takes its own margin-free page,
                # so the caption rides along as a paragraph on the next page
                out.append(f'<figure class="truesize"><img src="{m.group(2)}" '
                           f'alt="{html.escape(m.group(1), quote=False)}"/></figure>')
                out.append(f'<p class="truesize-cap">{inline(m.group(1))}</p>')
            else:
                out.append(f'<figure><img src="{m.group(2)}" alt="{html.escape(m.group(1), quote=False)}"/>'
                           f'<figcaption>{inline(m.group(1))}</figcaption></figure>')
            i += 1
            continue

        if stripped.startswith(">"):
            flush_para()
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip("> ").strip())
                i += 1
            joined = " ".join(quote)
            cls = ' class="warn"' if ("WARNING" in joined or "⚠" in joined) else ""
            out.append(f"<blockquote{cls}><p>{inline(joined)}</p></blockquote>")
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and re.match(r'^\|[\s:|-]+\|?$', lines[i + 1].strip()):
            flush_para()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head, body = rows[0], rows[2:]
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) +
                       "</tr></thead><tbody>")
            for r in body:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            out.append("</tbody></table>")
            continue

        m = re.match(r'^(\s*)([-*]|\d+\.)\s+(.*)$', line)
        if m:
            flush_para()
            ordered = m.group(2)[0].isdigit()
            items = []
            while i < len(lines):
                mm = re.match(r'^(\s*)([-*]|\d+\.)\s+(.*)$', lines[i])
                if mm:
                    items.append([len(mm.group(1)), mm.group(3)])
                    i += 1
                    continue
                # hard-wrapped continuation of the previous item: indented,
                # not a new bullet, not another block start
                s = lines[i].strip()
                if (s and lines[i][:1] in (' ', '\t') and items
                        and not re.match(r'^(#{1,4}\s|>|!\[|\||---)', s)):
                    items[-1][1] += ' ' + s
                    i += 1
                    continue
                break
            tag = "ol" if ordered else "ul"
            buf = [f"<{tag}>"]
            depth = 0
            for indent, content in items:
                level = 1 if indent >= 2 else 0
                while depth < level:
                    buf.append(f"<{tag}>")
                    depth += 1
                while depth > level:
                    buf.append(f"</{tag}>")
                    depth -= 1
                cm = re.match(r'^\[([ x])\]\s+(.*)$', content)
                if cm and not ordered:
                    buf.append(f'<li class="check">{inline(cm.group(2))}</li>')
                else:
                    buf.append(f"<li>{inline(content)}</li>")
            while depth:
                buf.append(f"</{tag}>")
                depth -= 1
            buf.append(f"</{tag}>")
            # a checklist block gets the printable box style
            joined = "".join(buf)
            if 'class="check"' in joined and not ordered:
                joined = joined.replace("<ul>", '<ul class="checks">', 1)
            out.append(joined)
            continue

        para.append(stripped)
        i += 1
    flush_para()
    return "\n".join(out)


sections = []
for page in pages:
    raw = open(os.path.join(guide_dir, page), encoding="utf-8").read()
    raw = re.sub(r'<!--.*?-->', '', raw, flags=re.S)   # model-trace comments never render
    fm, body = parse_front_matter(raw)
    pid = fm.get("page", page)
    stage = fm.get("stage", "")
    head = (f'<header class="page-head"><span class="page-id">{html.escape(pid)}</span>'
            + (f'<span class="page-stage">{html.escape(stage)}</span>' if stage else "")
            + "</header>")
    nav = ['<nav class="page-nav">']
    if fm.get("prev"):
        nav.append(f'<span class="prev">← prev: <a href="{fm["prev"]}">{fm["prev"]}</a></span>')
    else:
        nav.append('<span class="prev">← prev: —</span>')
    if fm.get("next"):
        nav.append(f'<span class="next">next: <a href="{fm["next"]}">{fm["next"]}</a> →</span>')
    else:
        nav.append('<span class="next">next: — →</span>')
    nav.append("</nav>")
    sections.append(f'<section class="guide-page" id="{html.escape(pid)}">\n{head}\n'
                    + convert(body) + "\n" + "".join(nav) + "\n</section>")

doc = ("<!doctype html><html><head><meta charset='utf-8'>"
       "<title>Wood Bike Shed — Build Guide</title>"
       f"<style>{css}</style></head><body>\n" + "\n".join(sections) + "\n</body></html>")

from weasyprint import HTML  # noqa: E402  (import after arg parsing for a clear error)

rendered = HTML(string=doc, base_url=guide_dir).render()
rendered.write_pdf(out_path)
print(f"wrote {out_path} ({len(rendered.pages)} pages, {os.path.getsize(out_path)} bytes)")
PY
