"""Build the St. Louis deck from the editable EEA opening and David's PDF.

Run with Python that has pypdf and reportlab; pdftoppm must be on PATH.
The imported slides remain original PDF pages, with remapped link destinations.
"""
from pathlib import Path
from html import escape
from io import BytesIO
import hashlib
import json
import re
import shutil
import subprocess
from copy import copy

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, DecodedStreamObject, NameObject, FloatObject
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "sources" / "david_original.pdf"
TMP = ROOT / ".build"
TMP.mkdir(exist_ok=True)
FONT_DIR = ROOT / "assets" / "fonts"
for font, file in [("Yanone", "yanone-regular"), ("YanoneSymbols", "yanone-symbols"), ("Droid", "droid-serif-regular"), ("DroidBold", "droid-serif-bold"), ("DroidItalic", "droid-serif-italic")]:
    pdfmetrics.registerFont(TTFont(font, str(FONT_DIR / (file + ".ttf"))))
pdfmetrics.registerFontFamily("Droid", normal="Droid", bold="DroidBold", italic="DroidItalic", boldItalic="DroidBold")
pdfmetrics.registerFont(TTFont("CrossedSwords", "C:/Windows/Fonts/seguisym.ttf"))

question = "When wars begin, do individuals change how they treat members of the opposing country in everyday encounters that have nothing to do with the war?"
opening = (ROOT / "opening.Rmd").read_text(encoding="utf-8-sig")
header, opening_body = opening.split("---", 2)[1:]
meta = {}
for line in header.splitlines():
    m = re.match(r"^(title|subtitle|author|institute|date):\s*(.+)$", line)
    if m:
        meta[m[1]] = json.loads(m[2])


def para(c, text, x, top, width, size=20, leading=26, font="Droid", color="#000000", alignment=0):
    style = ParagraphStyle("p", fontName=font, fontSize=size, leading=leading, textColor=color, alignment=alignment)
    p = Paragraph(text, style)
    _, height = p.wrap(width, 1000)
    p.drawOn(c, x, top - height)
    return top - height


def footer(c, number):
    c.setFillColorRGB(.5, .5, .5)
    c.setFont("Droid", 15)
    c.drawRightString(882, 18, str(number))


custom_path = TMP / "eea_pages.pdf"
c = canvas.Canvas(str(custom_path), pagesize=(908, 681))
c.setFillColorRGB(39 / 255, 40 / 255, 34 / 255)
c.rect(0, 0, 908, 681, fill=1, stroke=0)
para(c, meta["title"], 80, 608, 748, 55, 55, "Yanone", "#f3f3f3", 1)
c.setFillColorRGB(.95, .95, .95)
c.setFont("CrossedSwords", 45)
c.drawCentredString(454, 416, "⚔")
para(c, meta["subtitle"].split("<br/>", 1)[1], 80, 388, 748, 45, 45, "Yanone", "#f3f3f3", 1)
for text, y in [(meta["author"], 236), (meta["institute"], 164), (meta["date"], 94)]:
    c.setFont("Yanone", 35)
    c.setFillColorRGB(.95, .95, .95)
    c.drawCentredString(454, y, text)
footer(c, "1 / 32")
c.showPage()
y = para(c, "<b>" + question + "</b>", 80, 652, 748)
y -= 20
opening_visual = opening_body.split("\n---\n", 1)[1].split("\n???\n", 1)[0]
for line in opening_visual.splitlines():
    if re.match(r"^\s*- ", line):
        nested = line.startswith("  ")
        text = re.sub(r"^\s*- ", "", line)
        x = 160 if nested else 120
        y = para(c, "• " + escape(text), x, y, 828 - x)
        y -= 8 if not nested else 4
    elif line.strip() == "<br/>":
        y -= 12
assert y > 30, y
footer(c, "2 / 32")
c.showPage()
for title, sub in [("Backup slides", ""), ("Additional source slides", "Original return-link destinations")]:
    para(c, title, 80, 400, 748, 55, 60, "Yanone", alignment=1)
    if sub:
        para(c, sub, 80, 310, 748, 25, 30, "Yanone", alignment=1)
    c.showPage()
c.save()

# Replace the two-screenshot page without rewriting any source typography.
# Preserve its original title drawing operations and original image XObjects;
# omit all other text, then center the two original images at their old size.
original = PdfReader(SOURCE)
native = PdfWriter(clone_from=original)
p = native.pages[4]
ops = ContentStream(p.get_contents(), native).operations
end_title = next(i for i, (_, op) in enumerate(ops) if op == b"ET")
prefix = ops[:end_title + 1]
assert sum(op == b"q" for _, op in prefix) == sum(op == b"Q" for _, op in prefix)
image_names = [operands[0] for operands, op in ops if op == b"Do"]
assert len(image_names) == 2
image_widths = [float(p["/Resources"]["/XObject"][name].get_object()["/Width"]) * .18501 for name in image_names]
image_height = 805 * .18501
gap = 64
x = (float(p.mediabox.width) - sum(image_widths) - gap) / 2
new_ops = list(prefix)
for image_name, width in zip(image_names, image_widths):
    new_ops.extend([([], b"q"), ([FloatObject(width), FloatObject(0), FloatObject(0), FloatObject(image_height), FloatObject(x), FloatObject(72.404)], b"cm"), ([image_name], b"Do"), ([], b"Q")])
    x += width + gap
new_stream = ContentStream(None, native)
new_stream.operations = new_ops
p[NameObject("/Contents")] = native._add_object(new_stream)
modified_source = TMP / "david_with_two_screenshots.pdf"
native.write(modified_source)
source = PdfReader(modified_source)
assert re.sub(r"\s+", " ", source.pages[4].extract_text()).strip() == "What a player sees"

# Numbers here are physical PDF pages. David's frame 19 has two overlay pages.
# All requested named slides and source frames 23–36 are included in main.
main = [4, 5, *range(7, 16), *range(17, 22), *range(23, 38)]
backups = list(range(38, 93))
extra = [2, 3, 6, 16, 22]
assert sorted(main + backups + extra) == list(range(2, 93))

writer = PdfWriter()
custom = PdfReader(custom_path)
writer.append(custom, pages=[0, 1], import_outline=False)
source_order = main + backups + extra
writer.append(source, pages=[n - 1 for n in source_order], import_outline=False)
backup_index = 2 + len(main)
writer.merge(backup_index, custom, pages=[2], import_outline=False)
extra_index = backup_index + 1 + len(backups)
writer.merge(extra_index, custom, pages=[3], import_outline=False)
writer.add_metadata({"/Title": "St. Louis 2026 — War and everyday rivalry online", "/Author": "Eren Bilen; with Nino Doghonadze, Robizon Khubulashvili, David Smerdon"})
final_path = ROOT / "slides.pdf"
writer.write(final_path)
final = PdfReader(final_path)

page_map = {}
for i, n in enumerate(main):
    page_map[n] = i + 2
for i, n in enumerate(backups):
    page_map[n] = backup_index + 1 + i
for i, n in enumerate(extra):
    page_map[n] = extra_index + 1 + i
assert len(final.pages) == 95


def page_for_ref(ref):
    if hasattr(ref, "idnum"):
        for i, pg in enumerate(final.pages):
            if pg.indirect_reference.idnum == ref.idnum:
                return i
    if isinstance(ref, int):
        return ref
    return None


destinations = {name: final.get_destination_page_number(dest) for name, dest in final.named_destinations.items()}
assert all(0 <= i < len(final.pages) for i in destinations.values())


def resolve(dest):
    if isinstance(dest, (str, bytes)):
        key = dest.decode() if isinstance(dest, bytes) else str(dest)
        return destinations.get(key)
    if hasattr(dest, "get_object"):
        dest = dest.get_object()
    if isinstance(dest, dict):
        return resolve(dest.get("/D"))
    if isinstance(dest, list) and dest:
        return page_for_ref(dest[0])
    return None


titles = []
for i, pg in enumerate(final.pages):
    lines = (pg.extract_text() or "").splitlines()
    titles.append(lines[0] if lines else f"Slide {i + 1}")

links = []
unresolved = []
for i, pg in enumerate(final.pages):
    page_links = []
    for annot_ref in pg.get("/Annots", []):
        annot = annot_ref.get_object()
        if annot.get("/Subtype") != "/Link":
            continue
        action = annot.get("/A", {})
        if action and hasattr(action, "get_object"):
            action = action.get_object()
        dest = annot.get("/Dest") or (action.get("/D") if action.get("/S") == "/GoTo" else None)
        if dest is not None:
            target = resolve(dest)
            if target is None:
                unresolved.append({"page": i + 1, "destination": str(dest)})
                continue
            href = f"#p-{target + 1:03d}"
            label = "Go to " + titles[target]
        elif action.get("/S") == "/URI":
            href = str(action["/URI"])
            label = "Open source"
        else:
            continue
        rect = [float(n) for n in annot["/Rect"]]
        w, h = float(pg.mediabox.width), float(pg.mediabox.height)
        page_links.append({"href": href, "label": label, "left": rect[0] / w * 100, "top": (h - rect[3]) / h * 100, "width": (rect[2] - rect[0]) / w * 100, "height": (rect[3] - rect[1]) / h * 100})
    links.append(page_links)
assert not unresolved, unresolved

# Importing and reordering must preserve every unchanged source page exactly.
for old_n, new_i in page_map.items():
    if old_n != 5:
        assert original.pages[old_n - 1].get_contents().get_data() == final.pages[new_i].get_contents().get_data(), old_n
for old_n in range(24, 38):
    assert old_n in page_map
assert len(backups) == 55

page_dir = ROOT / "assets" / "david-pages"
page_dir.mkdir(parents=True, exist_ok=True)
poppler = shutil.which("pdftoppm")
if not poppler:
    bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe"
    if bundled.is_file():
        poppler = str(bundled)
if not poppler:
    raise RuntimeError("pdftoppm is required to build the HTML deck")
subprocess.run([poppler, "-png", "-scale-to", "1600", str(final_path), str(page_dir / "page")], check=True)
pngs = sorted(page_dir.glob("page-*.png"))
assert len(pngs) == len(final.pages)

style = """.source-page{padding:0!important;background:#fff;}.source-page .remark-slide-number{display:none}.pdf-paper{position:absolute;left:0;width:908px}.pdf-paper img{display:block;width:100%;height:100%;max-width:none}.pdf-paper a{position:absolute;display:block;background:transparent}.pdf-paper a:hover{background:rgba(31,95,173,.08)}.pdf-paper a:focus{outline:2px solid #1f5fad}.remark-slide-content.source-page{overflow:hidden}.backup-divider .remark-slide-number{display:none}"""
(ROOT / "source-pages.css").write_text(style, encoding="utf-8")

first_note, question_part = opening_body.strip().split("\n---\n", 1)
title = "class: center, middle, inverse, title-slide\nname: p-001\n\n"
for field, heading in [("title", "#"), ("subtitle", "##"), ("author", "###"), ("institute", "###"), ("date", "###")]:
    title += f".{field}[\n{heading} {meta[field]}\n]\n"
logical_parts = [title + "\n" + first_note]
question_part = question_part.replace("name: motivation", "name: p-002", 1)
logical_parts.append(question_part)
for i in range(2, len(final.pages)):
    name = f"p-{i + 1:03d}"
    if i in [backup_index, extra_index]:
        heading = "Backup slides" if i == backup_index else "Additional source slides"
        if i == backup_index:
            index_page = page_map[38] + 1
            faq_page = page_map[77] + 1
            body_text = f"[Backup index](#p-{index_page:03d})\n\n[FAQ](#p-{faq_page:03d})"
        else:
            body_text = "Original slides retained as return-link destinations"
        logical_parts.append(f"name: {name}\nclass: center, middle, backup-divider\ncount: false\n\n# {heading}\n\n{body_text}\n\n???\n\nAdditional source material.")
        continue
    pg = final.pages[i]
    w, h = float(pg.mediabox.width), float(pg.mediabox.height)
    height = 908 * h / w
    top = (681 - height) / 2
    paper = f'<div class="pdf-paper" style="top:{top:.5f}px;height:{height:.5f}px"><img src="assets/david-pages/{pngs[i].name}" alt="{escape(titles[i], quote=True)}" />'
    for link in links[i]:
        paper += f'<a href="{escape(link["href"], quote=True)}" aria-label="{escape(link["label"], quote=True)}" title="{escape(link["label"], quote=True)}" style="left:{link["left"]:.6f}%;top:{link["top"]:.6f}%;width:{link["width"]:.6f}%;height:{link["height"]:.6f}%"></a>'
    paper += "</div>"
    old_n = next(k for k, v in page_map.items() if v == i)
    count = "\ncount: false" if i > backup_index or old_n == 20 else ""
    note = f"{titles[i]}\n\nSpeaking notes: see david_speaker_notes.pdf, original PDF page {old_n}."
    logical_parts.append(f"name: {name}\nclass: source-page{count}\n\n{paper}\n\n???\n\n{note}")
source_text = "\n\n---\n".join(logical_parts)
render_parts = []
for segment in logical_parts:
    visual, note_text = segment.split("\n???\n", 1)
    builds = re.split(r"\n--\s*\n", visual)
    render_parts.append(builds[0].rstrip() + "\n\n???\n" + note_text.rstrip() + ("\n\n--\n" + "\n--\n".join(builds[1:]) if len(builds) > 1 else ""))

html = '''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>St. Louis 2026</title><link rel="stylesheet" href="libs/remark-css/default.css"><link rel="stylesheet" href="styles.css"><link rel="stylesheet" href="source-pages.css"></head><body><textarea id="source">__SOURCE__</textarea><script src="libs/remark-local.min.js"></script><script>var slideshow=remark.create({ratio:'4:3',countIncrementalSlides:false,slideNumberFormat:'%current% / %total%'});</script></body></html>'''
(ROOT / "slides.html").write_text(html.replace("__SOURCE__", escape("\n\n---\n".join(render_parts), quote=False)), encoding="utf-8")
(ROOT / "slides.Rmd").write_text("---" + header.replace('"styles.css"]', '"styles.css", "source-pages.css"]') + "---\n\n" + first_note + "\n\n---\n" + "\n\n---\n".join(logical_parts[1:]) + "\n", encoding="utf-8")

notes = '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>St. Louis — opening and slide index</title><style>body{font:18px/1.6 Georgia,serif;max-width:900px;margin:40px auto;padding:0 24px}h1,h2{font-family:Arial,sans-serif}li{margin:8px 0}</style></head><body><h1>St. Louis — opening and slide index</h1><h2>Opening</h2>'
opening_note = question_part.split("\n???\n", 1)[1]
for paragraph in opening_note.strip().split("\n\n"):
    escaped = escape(paragraph)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(https?://\S+)", r'<a href="\1">\1</a>', escaped)
    notes += "<p>" + escaped + "</p>"
notes += '<h2>Main talk</h2><ol>'
for i in range(2, backup_index):
    notes += f'<li><a href="slides.html#p-{i+1:03d}">{escape(titles[i])}</a></li>'
notes += '</ol><h2>Backup slides and FAQ</h2><ol>'
for i in range(backup_index + 1, extra_index):
    notes += f'<li><a href="slides.html#p-{i+1:03d}">{escape(titles[i])}</a></li>'
notes += '</ol><p><a href="david_speaker_notes.pdf">David’s original speaking notes</a> use his original slide numbers, which remain visible on the imported pages.</p></body></html>'
(ROOT / "speaker_notes.html").write_text(notes, encoding="utf-8")
backup_anchor = f"p-{backup_index + 1:03d}"
(ROOT / "backup.html").write_text(f'<!DOCTYPE html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=slides.html#{backup_anchor}"><title>Backup slides</title></head><body><a href="slides.html#{backup_anchor}">Open all backup slides and FAQ in the main deck</a></body></html>', encoding="utf-8")
report = {"pdf_pages": len(final.pages), "main_pdf_pages": backup_index, "main_logical_slides": 32, "original_backup_and_faq_pages": len(backups), "additional_return_target_slides": len(extra), "internal_links_checked": sum(len(ls) for ls in links), "unresolved_links": unresolved, "unchanged_original_page_streams_verified": len(page_map) - 1, "modified_source_page": 5, "source_page_to_output_page": {str(k): v + 1 for k, v in page_map.items()}, "backup_divider_page": backup_index + 1, "original_source_hash": hashlib.sha256(SOURCE.read_bytes()).hexdigest()}
(TMP / "validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in report.items() if k != "source_page_to_output_page"}, indent=2))
