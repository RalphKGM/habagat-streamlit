"""Screenshot every part of every page of the running app (default http://localhost:8502).

Pages render in a very tall viewport so nothing scrolls. Each page is cut into parts: a heading
always starts a part, controls and text gather above the next chart or table, and a short caption
stays with the chart above it. The map, the day picker, expanders and tabs get their own shots.
Writes PNGs plus parts.json (page, part, heading, file) into the output folder.
Run with the app's venv:  .venv/bin/python scripts/shoot_parts.py OUT_DIR
"""
import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

URL = "http://localhost:8502"
PAGES = ["plant", "designer", "sites", "forecast", "planning", "rolling", "forecast-2026", "methods"]
W, TALL, DSF = 1440, 7000, 2
PAD = 10

CHILDREN_JS = """
() => {
  const main = document.querySelector('[data-testid="stMainBlockContainer"]');
  const root = main.querySelector('[data-testid="stVerticalBlock"]');
  const box = main.getBoundingClientRect();
  const out = [];
  for (const el of root.children) {
    const r = el.getBoundingClientRect();
    if (r.height < 2) continue;
    const h = el.querySelector('h2, h4');
    let kind = 'widget';
    if (el.querySelector('hr') && r.height < 40) kind = 'hr';
    else if (h && r.height < 90) kind = 'heading';
    else if (r.height >= 150) kind = 'big';
    else if (el.querySelector('[data-testid="stMarkdown"], [data-testid="stCaptionContainer"]')
             && !el.querySelector('input, button, [role="slider"], [data-testid="stMetric"], iframe')) kind = 'text';
    out.push({kind, top: r.top + scrollY, bottom: r.bottom + scrollY, text: h ? h.innerText.trim() : ''});
  }
  return {left: box.left, width: box.width, items: out};
}
"""


def group(items):
    parts, cur = [], None
    for it in items:
        if it["kind"] == "hr":
            cur = None
            continue
        start = cur is None or it["kind"] == "heading" or (cur["big"] and it["kind"] in ("widget", "big"))
        if start:
            cur = dict(top=it["top"], bottom=it["bottom"], big=False, heading=it["text"])
            parts.append(cur)
        cur["bottom"] = max(cur["bottom"], it["bottom"])
        cur["big"] |= it["kind"] == "big"
        cur["heading"] = cur["heading"] or it["text"]
    # A row of figures under a chart (no chart of its own, no heading) belongs to the chart above it.
    merged = []
    for p in parts:
        if merged and not p["big"] and not p["heading"]:
            merged[-1]["bottom"] = max(merged[-1]["bottom"], p["bottom"])
        else:
            merged.append(p)
    return merged


async def settle(pg, extra=2500):
    await pg.wait_for_selector('[data-testid="stMainBlockContainer"]', timeout=90000)
    await pg.wait_for_timeout(1200)
    await pg.wait_for_function("!document.querySelector('[data-testid=\"stStatusWidget\"]')", timeout=180000)
    await pg.wait_for_timeout(extra)


class Shots:
    def __init__(self, out: Path):
        self.out, self.parts = out, []

    async def clip(self, pg, page, label, x, y, w, h, heading=""):
        file = self.out / f"{page}__{len([p for p in self.parts if p['page'] == page]):02d}_{label}.png"
        await pg.screenshot(path=str(file), clip={"x": x, "y": y, "width": w, "height": h})
        self.parts.append(dict(page=page, label=label, heading=heading, file=file.name))

    async def element(self, pg, page, label, locator, heading=""):
        b = await locator.bounding_box()
        await self.clip(pg, page, label, b["x"] - PAD, b["y"] - PAD, b["width"] + 2 * PAD, b["height"] + 2 * PAD, heading)


async def page_parts(pg, shots, page):
    data = await pg.evaluate(CHILDREN_JS)
    for i, part in enumerate(group(data["items"])):
        if part["bottom"] - part["top"] < 50:
            continue
        await shots.clip(pg, page, f"part{i}", data["left"], part["top"] - PAD, data["width"],
                         part["bottom"] - part["top"] + 2 * PAD, part["heading"])


async def main(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    shots = Shots(out)
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome")

        # Map: a normal-size window, then its three areas, then the forecast tab of the side panel.
        pg = await browser.new_page(viewport={"width": W, "height": 900}, device_scale_factor=DSF)
        await pg.goto(URL)
        await settle(pg, 7000)
        await shots.clip(pg, "map", "whole", 0, 0, W, 900, "Map")
        frame = None
        for f in pg.frames:
            if await f.query_selector("#mapbox"):
                frame = f
        for sel, label in [("#mapbox", "map_area"), ("#rail", "side_panel")]:
            b = await (await frame.query_selector(sel)).bounding_box()
            await shots.clip(pg, "map", label, b["x"] - 4, b["y"] - 4, b["width"] + 8, b["height"] + 8)
        m = await (await frame.query_selector("#mapbox")).bounding_box()
        t = await (await frame.query_selector("#tl")).bounding_box()
        top = m["y"] + m["height"]
        await shots.clip(pg, "map", "timeline", m["x"], top, m["width"], max(t["y"] + t["height"], 896) - top + 4)
        try:
            await frame.get_by_text("2025 forecast test", exact=False).first.click()
            await pg.wait_for_timeout(1200)
            b = await (await frame.query_selector("#rail")).bounding_box()
            await shots.clip(pg, "map", "side_panel_forecast", b["x"] - 4, b["y"] - 4, b["width"] + 8, b["height"] + 8)
        except Exception as e:  # the tab label may change; the rest of the shots still matter
            print("map forecast tab:", e)
        await pg.close()

        pg = await browser.new_page(viewport={"width": W, "height": TALL}, device_scale_factor=DSF)
        for page in PAGES:
            await pg.goto(f"{URL}/{page}")
            await settle(pg)
            await page_parts(pg, shots, page)

            if page == "plant":  # the shared day picker, opened
                dp = pg.frame_locator("iframe").first
                try:
                    await dp.get_by_text("2022").first.click()
                    await pg.wait_for_timeout(900)
                    el = pg.locator("iframe").first
                    await shots.element(pg, page, "day_picker_open", el, "Day picker")
                    await pg.keyboard.press("Escape")
                except Exception as e:
                    print("day picker:", e)
            if page == "designer":
                for name in ["Engineering assumptions", "Hourly results table and download"]:
                    exp = pg.locator('[data-testid="stExpander"]', has_text=name)
                    await exp.locator("summary").click()
                    await pg.wait_for_timeout(1500)
                    await shots.element(pg, page, name.split()[0].lower(), exp, name)
            if page == "forecast-2026":
                await pg.get_by_role("button", name="Each hour").click()
                await settle(pg, 1500)
                data = await pg.evaluate(CHILDREN_JS)
                part = [g for g in group(data["items"]) if g["heading"] == "Computed vs forecast"][0]
                await shots.clip(pg, page, "each_hour", data["left"], part["top"] - PAD, data["width"],
                                 part["bottom"] - part["top"] + 2 * PAD, "Computed vs forecast, each hour")
            if page == "methods":
                for tab in ["Wind turbine", "Battery", "Forecasting"]:
                    await pg.get_by_role("tab", name=tab).click()
                    await pg.wait_for_timeout(800)
                    await shots.element(pg, page, f"tab_{tab.split()[0].lower()}", pg.locator('[data-testid="stTabs"]'), tab)
            print(page, "done", flush=True)
        await browser.close()
    (out / "parts.json").write_text(json.dumps(shots.parts, indent=1))
    print(len(shots.parts), "shots")


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1])))
