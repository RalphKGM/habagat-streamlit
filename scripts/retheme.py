"""One-off: move the custom components from the old dark theme to the SolWind light datasheet theme."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = {
    # surfaces and rules
    "#0C1E2B": "#FFFFFF", "#0A1925": "#FFFFFF", "#06121B": "#FFFFFF", "#081520": "#FFFFFF", "#0B1C28": "#FFFFFF",
    "#0E2535": "#FFFFFF", "#0F2433": "#F4F5F3", "#132D3F": "#F0F2EF", "#1B3547": "#E9ECE8", "#163447": "#E9ECE8",
    "#132C3D": "#E6E9E5", "#1A3B50": "#E1E5E0", "#10283A": "#EEF0EE", "#123247": "#E4E8EA",
    "#1F3A4D": "#E1E4E0", "#2A4B60": "#C9CEC9",
    # ink
    "#EAF2F6": "#15191C", "#D5E3EA": "#2B3135", "#C9D8E0": "#4A5258", "#8BA6B5": "#60686E",
    "#5F7F91": "#8A9297", "#5E7787": "#9AA1A6", "#6D8C9E": "#8A9297", "#6F8796": "#A3AAAE",
    # data
    "#FFD166": "#15191C", "#FF8A5B": "#E8A317", "#E06A3F": "#B57A00", "#3FD0F0": "#2F6FDE",
    "#6EE7B7": "#3BA272", "#FF5C7A": "#D64545", "#C3A6FF": "#7C5CDB",
}
RGBA = {"rgba(10,25,37,.85)": "rgba(255,255,255,.94)", "rgba(160,225,245,0.45)": "rgba(31,63,110,0.30)"}
FONTS = [
    ("https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Condensed:wght@500;600&family=IBM+Plex+Mono:wght@400;500&display=swap",
     "https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"),
    ("'Barlow Condensed'", "'Archivo'"), ("Barlow Condensed", "Archivo"), ("'Barlow'", "'Archivo'"), ("Barlow", "Archivo"),
    ("'IBM Plex Mono'", "'JetBrains Mono'"), ("IBM Plex Mono", "JetBrains Mono"),
]
PER_FILE = {"solwind/assets/plant.html": {"#FFD166": "#E8A317"}}


def remap(path: str) -> None:
    p = ROOT / path
    s = p.read_text()
    table = {**BASE, **PER_FILE.get(path, {})}
    s = re.sub(r"#[0-9A-Fa-f]{6}\b", lambda m: table.get(m.group(0).upper(), m.group(0)), s)
    for a, b in RGBA.items():
        s = s.replace(a, b)
    for a, b in FONTS:
        s = s.replace(a, b)
    s = re.sub(r"\s*text-transform:\s*uppercase;?", "", s)
    s = s.replace("color-scheme:dark", "color-scheme:light")
    p.write_text(s)
    print("rethemed", path)


for f in ["solwind/assets/map/index.html", "solwind/assets/plant.html", "solwind/assets/replay.html",
          "solwind/assets/daypicker/index.html", "solwind/assets/daypicker/daypicker.js", "solwind/assets/map/daypicker.js"]:
    remap(f)
