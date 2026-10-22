"""Build the native remark/xaringan-style HTML and rehearsal notes.

Run `python render_slides.py` in this directory. No Python packages or R
installation are needed. Sources use Markdown/HTML, without executable R chunks.
The Rmd files can also be rendered by xaringan in an R installation that has it.
"""
from pathlib import Path
from html import escape
import json
import re

ROOT = Path(__file__).resolve().parent


def read_source(path):
    text = path.read_text(encoding="utf-8-sig")
    header, body = text.split("---", 2)[1:]
    meta = {}
    for line in header.splitlines():
        match = re.match(r"^(title|subtitle|author|institute|date):\s*(.+)$", line)
        if match:
            meta[match[1]] = json.loads(match[2])
    return meta, body.strip()


def build(path):
    meta, body = read_source(path)
    first_note, rest = body.split("\n---\n", 1)
    title = "class: center, middle, inverse, title-slide\n\n"
    for field, heading in (("title", "#"), ("subtitle", "##"), ("author", "###"), ("institute", "###"), ("date", "###")):
        if meta.get(field):
            title += f".{field}[\n{heading} {meta[field]}\n]\n"
    source = title + "\n" + first_note + "\n\n---\n" + rest
    render_parts = []
    for segment in re.split(r"\n---\s*\n", source):
        visual, note = segment.split("\n???\n", 1)
        builds = re.split(r"\n--\s*\n", visual)
        first_build = builds[0].rstrip() + "\n\n???\n" + note.rstrip()
        continuation = "\n\n--\n" + "\n--\n".join(builds[1:]) if len(builds) > 1 else ""
        render_parts.append(first_build + continuation)
    render_source = "\n---\n".join(render_parts)
    page_title = re.sub(r"<[^>]+>", " ", meta["title"])
    template = '''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="author" content="Eren Bilen">
<title>__TITLE__</title>
<link rel="stylesheet" href="libs/remark-css/default.css">
<link rel="stylesheet" href="styles.css">
</head><body>
<textarea id="source">__SOURCE__</textarea>
<script src="libs/remark-local.min.js"></script>
<script>
var slideshow = remark.create({ratio:'4:3',highlightStyle:'github',highlightLines:true,countIncrementalSlides:false,slideNumberFormat:'%current% / %total%'});
(function(){
  var scaler=document.querySelector('.remark-slide-scaler');
  if(scaler){var style=document.createElement('style');style.textContent='@page{size:'+scaler.style.width+' '+scaler.style.height+';margin:0}';document.head.appendChild(style);}
})();
</script></body></html>'''
    output = path.with_suffix(".html")
    output.write_text(template.replace("__TITLE__", escape(page_title)).replace("__SOURCE__", escape(render_source, quote=False)), encoding="utf-8")
    return source


def simple_markdown(text):
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return "\n".join("<p>" + para.replace("\n", " ") + "</p>" for para in text.strip().split("\n\n") if para.strip())


def write_notes(source):
    sections = []
    for index, slide in enumerate(re.split(r"\n---\s*\n", source), start=1):
        visual, note = slide.split("\n???\n", 1)
        heading = re.search(r"^#\s+(.+)$", visual, flags=re.M)
        title = re.sub(r"<[^>]+>", " ", heading[1]) if heading else ("The opponent's displayed flag" if "opponent-flags.png" in visual else "Research question")
        sections.append(f'<section><h2>{index}. {escape(title)}</h2>{simple_markdown(note)}</section>')
    html = '''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>St. Louis 2026 — speaking cues</title>
<style>body{font:18px/1.6 Georgia,serif;max-width:850px;margin:40px auto;padding:0 28px;color:#222}h1,h2{font-family:Arial,sans-serif;line-height:1.2}section{border-top:1px solid #ccc;margin-top:36px;padding-top:20px}p{margin:16px 0}strong{font-weight:700}.intro{font-size:16px;color:#555}@media print{section{break-inside:avoid;page-break-inside:avoid}body{font-size:12pt}}</style></head><body>
<h1>St. Louis 2026 — speaking cues</h1><p class="intro">Sixteen short slides: David's concession argument in the EEA layout. Target: 12 minutes, leaving about 3 minutes for questions if the slot is 15 minutes in total. These cues are also embedded in the slides: press P for presenter view. Main deck: <a href="slides.html">slides.html</a>. Optional technical answers and figures: <a href="backup.html">backup.html</a>.</p>'''
    (ROOT / "speaker_notes.html").write_text(html + "\n".join(sections) + "</body></html>", encoding="utf-8")


if __name__ == "__main__":
    source = build(ROOT / "slides.Rmd")
    slide_count = len(re.split(r"\n---\s*\n", source))
    assert slide_count == 16
    write_notes(source)
    if (ROOT / "backup.Rmd").exists():
        build(ROOT / "backup.Rmd")
    print("Built slides.html (16 slides), speaker_notes.html, and optional backup.html")
