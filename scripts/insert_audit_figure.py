"""Insert Fig. 6 (2026 computed vs forecast) into the paper DOCX after the matched-calendar paragraph.

usage: insert_audit_figure.py <in.docx> <out.docx> <figure.png> <height/width ratio> [last-figure scale]
Only word/document.xml, its relationships and one new media file change.
"""
import re, sys, zipfile

src, out, png, ratio = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
z = zipfile.ZipFile(src); files = {n: z.read(n) for n in z.namelist()}
x = files["word/document.xml"].decode(); rels = files["word/_rels/document.xml.rels"].decode()
paras = re.findall(r"<w:p[ >].*?</w:p>", x)
anchor = [p for p in paras if "In the matched calendar window" in p]; assert len(anchor) == 1; anchor = anchor[0]
tpl = [p for p in paras if 'name="ieee_figure_forecast.png"' in p]; assert len(tpl) == 1; tpl = tpl[0]
old_rid = re.search(r'r:embed="([^"]+)"', tpl).group(1); old_cy = re.search(r'<wp:extent cx="\d+" cy="(\d+)"', tpl).group(1)
docpr = re.search(r'<wp:docPr id="\d+" name="[^"]*"/>', tpl).group(0)
new_id = max(int(i) for i in re.findall(r'<wp:docPr id="(\d+)"', x)) + 1
img, rid = "media/image100.png", "rIdAudit2026"
assert "word/" + img not in files and rid not in rels
rels = rels.replace("</Relationships>", f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{img}"/></Relationships>')
cx = 3072384; cy = int(cx * ratio)
fig = (tpl.replace(f'r:embed="{old_rid}"', f'r:embed="{rid}"').replace(f'cy="{old_cy}"', f'cy="{cy}"')
       .replace(docpr, f'<wp:docPr id="{new_id}" name="Picture {new_id}"/>')
       .replace('name="ieee_figure_forecast.png"', 'name="fig_2026_computed_vs_forecast.png"'))
cap = ('<w:p><w:pPr><w:pStyle w:val="figurecaption"/></w:pPr><w:r><w:t>January-June 2026 daily energy computed from 2026 '
       'weather versus XGBoost forecasts issued at 00:00 by models trained only on 2020-2025 data (last target 31 December 2025, 23:00).</w:t></w:r></w:p>')
sentence = ' Fig. 6 compares the 2026 forecasts with output computed from 2026 weather.'
end = "Year-specific weather and refitted weights both differ."
assert anchor.count(end) == 1
new_anchor = anchor.replace(end, end + sentence)
x = x.replace(anchor, new_anchor + fig + cap, 1)
# Make room on the page: show the grid-plan figure (now Fig. 7) at 88% of its size, same aspect ratio.
SCALE = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
if SCALE != 1.0:
    drawings = [p for p in re.findall(r"<w:p[ >].*?</w:p>", x) if "<w:drawing" in p]
    last = drawings[-1]  # the grid-plan adjustment figure is the last figure in the paper
    ex = re.search(r'<wp:extent cx="(\d+)" cy="(\d+)"', last); cx0, cy0 = int(ex.group(1)), int(ex.group(2))
    cx1, cy1 = int(cx0 * SCALE), int(cy0 * SCALE)
    scaled = last.replace(f'cx="{cx0}" cy="{cy0}"', f'cx="{cx1}" cy="{cy1}"')
    assert scaled.count(f'cx="{cx1}" cy="{cy1}"') == 2
    if "<w:jc " not in scaled:
        scaled = scaled.replace("<w:pPr>", '<w:pPr><w:jc w:val="center"/>', 1)
    x = x.replace(last, scaled, 1)
files["word/document.xml"] = x.encode(); files["word/_rels/document.xml.rels"] = rels.encode()
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as o:
    for n in z.namelist():
        o.writestr(z.getinfo(n), files[n])
    o.writestr("word/" + img, open(png, "rb").read())
print("figures before Fig. 6:", x[:x.index(sentence)].count("<w:drawing"), "->", out)
