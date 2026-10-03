"""Animated landing hero. Pure SVG + CSS keyframes, rendered inline (no iframe, no JS)."""

from __future__ import annotations

import math

import streamlit as st

from habagat import theme
from habagat.theme import INK, SEA, SUN, SUN_DEEP


def _turbine(x: float, base: float, hub: float, blade: float, period: float, delay: float) -> str:
    blade_path = (
        f"M0,0 C{blade * .07:.1f},{-blade * .25:.1f} {blade * .05:.1f},{-blade * .8:.1f} 0,{-blade:.1f} "
        f"C{-blade * .03:.1f},{-blade * .8:.1f} {-blade * .05:.1f},{-blade * .25:.1f} 0,0Z"
    )
    blades = "".join(f'<path d="{blade_path}" transform="rotate({a})"/>' for a in (0, 120, 240))
    return (
        f'<polygon points="{x - 3.2},{base} {x + 3.2},{base} {x + 1.3},{hub} {x - 1.3},{hub}" fill="{INK}"/>'
        f'<g transform="translate({x} {hub})"><g class="rotor" style="animation-duration:{period}s;'
        f'animation-delay:-{delay}s" fill="{INK}">{blades}</g>'
        f'<circle r="{max(blade * .06, 2.4):.1f}" fill="{INK}"/></g>'
    )


def _rays(cx: float, cy: float) -> str:
    lines = []
    for i in range(24):
        a = 2 * math.pi * i / 24
        r1, r2 = (80, 104) if i % 2 == 0 else (82, 94)
        lines.append(
            f'<line x1="{r1 * math.cos(a):.1f}" y1="{r1 * math.sin(a):.1f}" '
            f'x2="{r2 * math.cos(a):.1f}" y2="{r2 * math.sin(a):.1f}"/>'
        )
    return (
        f'<g transform="translate({cx} {cy})"><g class="rays" stroke="{SUN_DEEP}" stroke-width="2.4" '
        f'stroke-linecap="round">{"".join(lines)}</g></g>'
    )


def _panels() -> str:
    rows = []
    for r, (y, w, h, skew, n, x0) in enumerate([(424, 46, 20, 9, 9, 40), (456, 52, 23, 10, 9, 22), (492, 58, 26, 11, 8, 4)]):
        for i in range(n):
            x = x0 + i * (w + 8)
            pts = f"{x + skew},{y} {x + w + skew},{y} {x + w},{y + h} {x},{y + h}"
            rows.append(f'<polygon points="{pts}" fill="#24404D" stroke="#F2EDE3" stroke-width="1.2"/>')
            rows.append(
                f'<line x1="{x + skew / 2 + w / 2}" y1="{y}" x2="{x + w / 2}" y2="{y + h}" stroke="#3B6273" stroke-width=".8"/>'
            )
    return "".join(rows)


def render(kicker: str, title: str, tagline: str, sub: str) -> None:
    sun_x, sun_y = 905, 150
    waves = "".join(
        f'<path class="wave w{i}" d="M-200,{y} '
        + " ".join(f"q30,-7 60,0 t60,0" for _ in range(26))
        + f'" fill="none" stroke="#F2EDE3" stroke-width="1.4" opacity=".7"/>'
        for i, y in enumerate([392, 410, 432])
    )
    streaks = "".join(
        f'<path class="streak" style="animation-duration:{d}s;animation-delay:-{delay}s" '
        f'd="M{x},{y} C{x + 180},{y - 28} {x + 360},{y + 22} {x + 640},{y - 6}" />'
        for x, y, d, delay in [(380, 120, 6.5, 0), (520, 205, 8, 2.4), (300, 268, 7.2, 4.1), (640, 80, 9, 1.3), (460, 320, 7.8, 5.5)]
    )
    svg = f"""
<svg class="hb-scene" viewBox="0 0 1200 540" preserveAspectRatio="xMaxYMax slice" aria-hidden="true">
  <defs>
    <radialGradient id="hbHalo"><stop offset="0" stop-color="{SUN}" stop-opacity=".55"/>
      <stop offset="1" stop-color="{SUN}" stop-opacity="0"/></radialGradient>
    <linearGradient id="hbGlint" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>
      <stop offset=".5" stop-color="#FFE7B8" stop-opacity=".85"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
    <clipPath id="hbPanelClip">{_panels()}</clipPath>
  </defs>
  <circle class="halo" cx="{sun_x}" cy="{sun_y}" r="170" fill="url(#hbHalo)"/>
  {_rays(sun_x, sun_y)}
  <circle cx="{sun_x}" cy="{sun_y}" r="64" fill="{SUN}"/>
  <circle cx="{sun_x}" cy="{sun_y}" r="64" fill="none" stroke="{SUN_DEEP}" stroke-width="1.5"/>
  <g fill="none" stroke="{SEA}" stroke-width="2" stroke-linecap="round" opacity=".55">{streaks}</g>
  <path d="M0,372 L90,340 L170,352 L260,318 L330,336 L420,300 L520,330 L600,312 L700,338 L780,322 L860,345 L1200,330 L1200,380 L0,380Z" fill="#DCCDAE"/>
  <rect x="0" y="378" width="1200" height="170" fill="#9EC0CB"/>
  <g class="waves">{waves}</g>
  <path d="M700,540 L740,410 C780,360 860,330 960,326 C1060,322 1150,340 1200,352 L1200,540Z" fill="#CDBB94"/>
  <path d="M700,540 L740,410 C780,360 860,330 960,326 C1060,322 1150,340 1200,352" fill="none" stroke="{INK}" stroke-width="1.4"/>
  {_turbine(1105, 345, 168, 88, 5.2, 0)}
  {_turbine(980, 330, 196, 72, 4.1, 1.1)}
  {_turbine(860, 345, 236, 54, 3.4, 2)}
  <path d="M0,540 L0,420 C120,404 300,402 470,430 C560,446 620,480 650,540Z" fill="#D9C79F"/>
  <path d="M0,420 C120,404 300,402 470,430 C560,446 620,480 650,540" fill="none" stroke="{INK}" stroke-width="1.4"/>
  <g>{_panels()}</g>
  <g clip-path="url(#hbPanelClip)"><rect class="glint" x="-200" y="400" width="180" height="140" fill="url(#hbGlint)"/></g>
</svg>"""

    css = """
<style>
.hb-hero { position:relative; height:clamp(520px, 62vh, 600px); border:1px solid var(--ink); border-radius:22px;
  overflow:hidden; background:linear-gradient(180deg,#F8DFAE 0%,#F5E6CA 48%,#F2EDE3 100%); margin-bottom:1.2rem; }
.hb-hero .hb-scene { position:absolute; inset:0; width:100%; height:100%; }
.hb-hero-copy { position:relative; z-index:2; padding:2.4rem 2.6rem; max-width:620px; }
.hb-hero h1 { font-family:var(--serif); font-size:clamp(3.4rem,8.5vw,6.6rem); line-height:.9; margin:.2rem 0 .8rem;
  color:var(--ink); letter-spacing:-.045em; font-weight:650; padding:0; }
.hb-hero h1 span { color:var(--sun-deep); font-style:italic; font-weight:450; }
.hb-hero .tag { font-family:var(--serif); font-size:clamp(1.15rem,2vw,1.5rem); line-height:1.25; color:var(--ink); margin:0 0 .7rem; max-width:520px; }
.hb-hero .sub { color:var(--ink-soft); font-size:.98rem; line-height:1.55; max-width:470px; margin:0; }
.hb-hero .rotor { animation:hb-spin linear infinite; }
.hb-hero .rays { animation:hb-spin 70s linear infinite; }
.hb-hero .halo { transform-box:fill-box; transform-origin:center; animation:hb-pulse 6s ease-in-out infinite; }
.hb-hero .streak { stroke-dasharray:110 900; stroke-dashoffset:1010; animation:hb-gust linear infinite; }
.hb-hero .wave { animation:hb-wave 7s linear infinite; }
.hb-hero .wave.w1 { animation-duration:9s; } .hb-hero .wave.w2 { animation-duration:12s; }
.hb-hero .glint { animation:hb-glint 5.5s ease-in-out infinite; }
.hb-hero-copy > * { opacity:0; transform:translateY(14px); animation:hb-rise .9s cubic-bezier(.2,.7,.1,1) forwards; }
.hb-hero-copy > *:nth-child(2) { animation-delay:.12s; } .hb-hero-copy > *:nth-child(3) { animation-delay:.26s; }
.hb-hero-copy > *:nth-child(4) { animation-delay:.4s; }
@keyframes hb-spin { to { transform:rotate(360deg); } }
@keyframes hb-pulse { 50% { transform:scale(1.09); opacity:.75; } }
@keyframes hb-gust { to { stroke-dashoffset:0; } }
@keyframes hb-wave { to { transform:translateX(120px); } }
@keyframes hb-glint { 0%,30% { transform:translateX(0); } 75%,100% { transform:translateX(900px); } }
@keyframes hb-rise { to { opacity:1; transform:none; } }
@media (max-width: 760px) {
  .hb-hero { height:640px; } .hb-hero-copy { padding:1.6rem 1.4rem; }
  .hb-hero .hb-scene { top:auto; height:62%; }
}
</style>"""
    theme.html(
        css
        + f"""<section class="hb-hero">{svg}
  <div class="hb-hero-copy">
    <div class="hb-kicker">{kicker}</div>
    <h1>{title}</h1>
    <p class="tag">{tagline}</p>
    <p class="sub">{sub}</p>
  </div></section>"""
    )
