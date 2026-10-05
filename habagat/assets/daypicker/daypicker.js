/* Habagat day picker: a calendar coloured by each day's energy, a full-range energy ribbon,
   one-click presets, typed dates and keyboard stepping.

   The canonical copy lives in assets/daypicker/; assets/map/daypicker.js must be identical
   (tests/test_app.py checks this, because each Streamlit component serves only its own folder).

   DayPicker.mount(root, {
     daily: {start: "2020-01-01", gen: [MWh/day], wind: [MWh/day], grid: [MWh/day]},
     value: "YYYY-MM-DD", min, max, site: "Laoag",
     mode: "inline" | "up",      // inline: bar + ribbon + calendar opening below; up: compact bar, calendar opens upward
     onPick(date), onHeight(px)  // onHeight: inline mode only, so the host iframe can grow while the calendar is open
   })
*/
(function () {
  const SCALE = ["#123247", "#14566A", "#1A8190", "#3DB6B0", "#9EE3C0", "#FFF1B8"];
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const MONTH_NAMES = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"];
  const WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const DAY = 864e5;

  const CSS = `
  .dp { position:relative; font:14px/1.35 'Barlow', system-ui, sans-serif; color:#EAF2F6; }
  .dp button { font:inherit; color:inherit; background:none; cursor:pointer; }
  .dp-bar { display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
  .dp-step { width:32px; height:34px; border:1px solid #2A4B60; font-size:17px !important; }
  .dp-step:hover, .dp-label:hover { border-color:#EAF2F6; }
  .dp-step:disabled { opacity:.3; cursor:default; }
  .dp-label { height:34px; padding:0 12px; border:1px solid #2A4B60; display:flex; align-items:center; gap:10px; min-width:170px; justify-content:space-between; }
  .dp-label b { font:600 17px/1 'Barlow Condensed', sans-serif; letter-spacing:.03em; text-transform:uppercase; }
  .dp-label i { font-style:normal; color:#8BA6B5; font-size:11px; }
  .dp.open .dp-label { border-color:#FFD166; }
  .dp-chips { display:flex; gap:4px; flex-wrap:wrap; }
  .dp-chip { height:28px; padding:0 9px; border:1px solid #1F3A4D; color:#8BA6B5 !important; font-size:12.5px !important; }
  .dp-chip:hover { border-color:#FFD166; color:#FFD166 !important; }
  .dp-type { height:34px; width:190px; background:none; border:1px solid #2A4B60; color:#EAF2F6; padding:0 10px; font:13px 'Barlow', sans-serif; outline:none; }
  .dp-type:focus { border-color:#FFD166; }
  .dp-type.bad { border-color:#FF5C7A; }
  .dp-ribbon { position:relative; margin-top:10px; height:52px; cursor:pointer; }
  .dp-ribbon canvas { width:100%; height:38px; display:block; }
  .dp-ribbon .yrs { position:relative; height:14px; font:11px 'IBM Plex Mono', monospace; color:#6D8C9E; }
  .dp-ribbon .yrs span { position:absolute; top:1px; padding-left:4px; border-left:1px solid #2A4B60; }
  .dp-tip { position:absolute; pointer-events:none; background:#0A1925; border:1px solid #2A4B60; padding:5px 8px; font-size:12.5px; white-space:nowrap; z-index:5; display:none; }
  .dp-tip b { font-weight:600; }
  .dp-pop { position:absolute; z-index:20; background:#0C1E2B; border:1px solid #2A4B60; box-shadow:0 18px 40px rgba(0,0,0,.45); padding:14px; width:500px; max-width:calc(100vw - 8px); }
  .dp-pop[hidden] { display:none; }
  .dp.inline .dp-pop { left:0; top:44px; }
  .dp.up .dp-pop { left:0; bottom:44px; }
  .dp-head { display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:10px; }
  .dp-years { display:flex; gap:3px; }
  .dp-year { height:28px; padding:0 9px; border:1px solid #1F3A4D; font:500 13px 'IBM Plex Mono', monospace !important; }
  .dp-year.on { border-color:#FFD166; color:#FFD166 !important; }
  .dp-year sup { font-size:9px; color:#8BA6B5; margin-left:2px; }
  .dp-x { width:28px; height:28px; border:1px solid #1F3A4D; color:#8BA6B5 !important; }
  .dp-months { display:grid; grid-template-columns:repeat(12, 1fr); gap:3px; margin-bottom:10px; }
  .dp-month { height:40px; border:1px solid #1F3A4D; display:flex; flex-direction:column; justify-content:flex-end; align-items:center; padding:2px 0 3px; position:relative; font-size:11.5px !important; color:#8BA6B5 !important; }
  .dp-month s { position:absolute; left:3px; right:3px; bottom:17px; text-decoration:none; }
  .dp-month.on { border-color:#FFD166; color:#FFD166 !important; }
  .dp-month:disabled { opacity:.25; cursor:default; }
  .dp-grid { display:grid; grid-template-columns:repeat(7, 1fr); gap:3px; }
  .dp-wd { font:11px 'IBM Plex Mono', monospace; color:#6D8C9E; text-align:center; padding-bottom:2px; }
  .dp-day { height:38px; position:relative; font:500 13px 'IBM Plex Mono', monospace !important; color:#0A1925 !important; border:2px solid transparent; }
  .dp-day.light { color:#EAF2F6 !important; }
  .dp-day u { position:absolute; left:3px; bottom:3px; height:3px; background:#3FD0F0; text-decoration:none; }
  .dp-day.sel { border-color:#FFD166; }
  .dp-day.cur { outline:1px dashed #EAF2F6; outline-offset:1px; }
  .dp-day:disabled { background:transparent !important; color:#2A4B60 !important; cursor:default; }
  .dp-foot { display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:10px; flex-wrap:wrap; }
  .dp-legend { display:flex; align-items:center; gap:6px; font-size:12px; color:#8BA6B5; }
  .dp-legend span { display:inline-block; width:14px; height:10px; }
  .dp-keys { font-size:11.5px; color:#6D8C9E; margin-top:8px; }
  .dp-keys kbd { font:11px 'IBM Plex Mono', monospace; border:1px solid #2A4B60; padding:0 4px; color:#8BA6B5; }
  `;

  const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  function heat(v) {
    v = Math.max(0, Math.min(1, v)) * (SCALE.length - 1);
    const i = Math.min(Math.floor(v), SCALE.length - 2), f = v - i, a = hex(SCALE[i]), b = hex(SCALE[i + 1]);
    return `rgb(${a.map((x, k) => Math.round(x + (b[k] - x) * f)).join(",")})`;
  }
  const ms = (s) => Date.parse(s + "T00:00:00Z");
  const iso = (t) => new Date(t).toISOString().slice(0, 10);
  const add = (s, n) => iso(ms(s) + n * DAY);
  const fmt = (s) => { const d = new Date(ms(s)); return `${WD[(d.getUTCDay() + 6) % 7]} ${String(d.getUTCDate()).padStart(2, "0")} ${MON[d.getUTCMonth()]} ${d.getUTCFullYear()}`; };

  function parseTyped(text, ref) {
    const s = text.trim().toLowerCase().replace(/,/g, " ").replace(/\s+/g, " ");
    if (!s) return null;
    let m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
    if (m) return mk(+m[1], +m[2], +m[3]);
    m = s.match(/^(\d{1,2})[\/.](\d{1,2})[\/.](\d{4})$/);           // day first: 14/03/2025
    if (m) return mk(+m[3], +m[2], +m[1]);
    const mon = (w) => MONTH_NAMES.findIndex((n) => n.startsWith(w)) + 1;
    m = s.match(/^(\d{1,2}) ([a-z]{3,9})(?: (\d{4}))?$/);           // 14 mar 2025
    if (m && mon(m[2])) return mk(m[3] ? +m[3] : +ref.slice(0, 4), mon(m[2]), +m[1]);
    m = s.match(/^([a-z]{3,9}) (\d{1,2})(?: (\d{4}))?$/);           // mar 14 2025
    if (m && mon(m[1])) return mk(m[3] ? +m[3] : +ref.slice(0, 4), mon(m[1]), +m[2]);
    m = s.match(/^([a-z]{3,9}) (\d{4})$/);                          // mar 2025 -> 1st
    if (m && mon(m[1])) return mk(+m[2], mon(m[1]), 1);
    return null;
    function mk(y, mo, d) {
      const out = `${y}-${String(mo).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      return iso(ms(out)) === out ? out : null;
    }
  }

  function mount(root, opts) {
    if (!document.getElementById("dp-css")) {
      const st = document.createElement("style"); st.id = "dp-css"; st.textContent = CSS; document.head.appendChild(st);
    }
    const o = Object.assign({ mode: "inline", onPick() {}, onHeight() {} }, opts);
    const D = o.daily, n = D.gen.length, start = D.start;
    const idx = (s) => Math.round((ms(s) - ms(start)) / DAY);
    const at = (s) => { const i = idx(s); return i >= 0 && i < n ? i : -1; };
    const sorted = D.gen.slice().sort((a, b) => a - b);
    const top = sorted[Math.floor(n * 0.98)] || 1;           // colour scale ignores the few extreme days
    let value = o.value, cursor = o.value, open = false;

    root.innerHTML = "";
    const el = document.createElement("div");
    el.className = "dp " + (o.mode === "up" ? "up" : "inline");
    root.appendChild(el);

    const presets = () => {
      const best = (score) => { let bi = 0, bv = -Infinity; for (let i = 0; i < n; i++) { const v = score(i); if (v > bv) { bv = v; bi = i; } } return add(start, bi); };
      const shift = (years) => { const t = add(value, Math.round(365.25 * years)); return t >= o.min && t <= o.max ? t : null; };
      return [
        ["Windiest", best((i) => D.wind[i])],
        ["Sunniest", best((i) => D.gen[i] - D.wind[i])],
        ["Calmest", best((i) => -D.gen[i])],
        ["Hardest", best((i) => D.grid[i])],
        ["Random", add(start, Math.floor(Math.random() * n))],
        ["−1 yr", shift(-1)],
        ["+1 yr", shift(1)],
      ].filter((p) => p[1]);
    };

    function pick(s, keepOpen) {
      if (!s || s < o.min || s > o.max) return false;
      value = cursor = s;
      if (!keepOpen) setOpen(false);
      renderBar(); drawRibbon(); if (open) renderPop();
      o.onPick(s);
      return true;
    }

    function setOpen(v) {
      open = v; el.classList.toggle("open", v); pop.hidden = !v;
      if (v) { cursor = value; renderPop(); }
      o.onHeight(v ? el.offsetHeight + pop.offsetHeight + 10 : el.offsetHeight);
    }

    // ---- bar ----
    const bar = document.createElement("div"); bar.className = "dp-bar"; el.appendChild(bar);
    function renderBar() {
      const i = at(value), info = i >= 0 ? `${D.gen[i].toFixed(1)} MWh` : "";
      bar.innerHTML = `<button class="dp-step" data-s="-1" title="Previous day (←)" ${value <= o.min ? "disabled" : ""}>‹</button>
        <button class="dp-label" title="Open calendar"><b>${fmt(value)}</b><i>${info} ▾</i></button>
        <button class="dp-step" data-s="1" title="Next day (→)" ${value >= o.max ? "disabled" : ""}>›</button>` +
        (o.mode === "inline"
          ? `<input class="dp-type" placeholder="Type a date: 14 Mar 2025" aria-label="Type a date">
             <div class="dp-chips">${presets().map(([l, d]) => `<button class="dp-chip" data-d="${d}" title="${fmt(d)}">${l}</button>`).join("")}</div>`
          : "");
      bar.querySelectorAll(".dp-step").forEach((b) => b.onclick = () => pick(add(value, +b.dataset.s)));
      bar.querySelector(".dp-label").onclick = () => setOpen(!open);
      bar.querySelectorAll(".dp-chip").forEach((b) => b.onclick = () => pick(b.dataset.d));
      const type = bar.querySelector(".dp-type");
      if (type) bindType(type);
    }
    function bindType(input) {
      input.onkeydown = (e) => {
        e.stopPropagation();
        if (e.key === "Enter") {
          const s = parseTyped(input.value, value);
          if (s && pick(s)) { input.value = ""; input.classList.remove("bad"); } else input.classList.add("bad");
        } else input.classList.remove("bad");
      };
    }

    // ---- ribbon (inline mode): every day of the record as one column ----
    let canvas = null, tip = null, years = null;
    if (o.mode === "inline") {
      const rib = document.createElement("div"); rib.className = "dp-ribbon";
      rib.innerHTML = `<canvas></canvas><div class="yrs"></div><div class="dp-tip"></div>`;
      el.appendChild(rib);
      canvas = rib.querySelector("canvas"); tip = rib.querySelector(".dp-tip"); years = rib.querySelector(".yrs");
      const dayAt = (e) => { const r = canvas.getBoundingClientRect(); return add(start, Math.max(0, Math.min(n - 1, Math.floor((e.clientX - r.left) / r.width * n)))); };
      let drag = false, preview = null;
      canvas.onmousedown = (e) => { drag = true; preview = dayAt(e); drawRibbon(preview); };
      canvas.onmousemove = (e) => {
        const s = dayAt(e), i = at(s), r = canvas.getBoundingClientRect();
        tip.style.display = "block";
        tip.innerHTML = `<b>${fmt(s)}</b> · ${D.gen[i].toFixed(1)} MWh · ${D.gen[i] ? Math.round(100 * D.wind[i] / D.gen[i]) : 0}% wind`;
        tip.style.left = Math.min(e.clientX - r.left + 10, r.width - tip.offsetWidth) + "px"; tip.style.top = "-30px";
        if (drag) { preview = s; drawRibbon(preview); }
      };
      canvas.onmouseleave = () => { tip.style.display = "none"; };
      addEventListener("mouseup", () => { if (drag) { drag = false; if (preview) pick(preview); preview = null; } });
      new ResizeObserver(() => drawRibbon()).observe(canvas);
    }
    function drawRibbon(preview) {
      if (!canvas) return;
      const w = canvas.clientWidth, h = canvas.clientHeight, dpr = devicePixelRatio || 1;
      if (!w) return;
      canvas.width = w * dpr; canvas.height = h * dpr;
      const ctx = canvas.getContext("2d"); ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, w, h);
      // weekly means read better than 2,000+ one-pixel days; hover and clicks still resolve to a single day
      const step = w / n, week = 7;
      for (let i = 0; i < n; i += week) {
        let sum = 0, c = 0;
        for (let k = i; k < Math.min(i + week, n); k++) { sum += D.gen[k]; c++; }
        const v = Math.min(sum / c / top * 1.15, 1);
        ctx.fillStyle = heat(v);
        ctx.fillRect(i * step + .5, h - 3 - v * (h - 5), Math.max(c * step - 1, 1), v * (h - 5) + 3);
      }
      const mark = (s, color) => { const x = (idx(s) + .5) * step; ctx.fillStyle = color; ctx.fillRect(x - 1, 0, 2, h); };
      mark(value, "#FFD166"); if (preview) mark(preview, "#EAF2F6");
      if (years && !years.childElementCount) {
        // years across a long record, months when the range is about one year
        const label = (i, text) => { const sp = document.createElement("span"); sp.style.left = (100 * i / n) + "%"; sp.textContent = text; years.appendChild(sp); };
        if (n > 400) {
          for (let y = +start.slice(0, 4); y <= +o.max.slice(0, 4); y++) { const i = idx(`${y}-01-01`); if (i >= 0 && i < n) label(i, y); }
        } else {
          for (let d = start; at(d) >= 0; d = add(d, 1)) if (d.endsWith("-01") || d === start) label(idx(d), MON[+d.slice(5, 7) - 1] + (d.slice(5, 7) === "01" || d === start ? " " + d.slice(0, 4) : ""));
        }
      }
    }

    // ---- calendar pop-up ----
    const pop = document.createElement("div"); pop.className = "dp-pop"; pop.hidden = true; el.appendChild(pop);
    function renderPop() {
      const y = +cursor.slice(0, 4), m = +cursor.slice(5, 7) - 1;
      const y0 = +o.min.slice(0, 4), y1 = +o.max.slice(0, 4);
      // monthly mean energy for this year's month buttons
      const monthly = MON.map((_, k) => {
        let s = 0, c = 0; const first = `${y}-${String(k + 1).padStart(2, "0")}-01`;
        for (let d = first; d.slice(5, 7) == String(k + 1).padStart(2, "0"); d = add(d, 1)) { const i = at(d); if (i >= 0) { s += D.gen[i]; c++; } }
        return c ? s / c : null;
      });
      const first = `${y}-${String(m + 1).padStart(2, "0")}-01`;
      const lead = (new Date(ms(first)).getUTCDay() + 6) % 7;
      let cells = WD.map((w) => `<div class="dp-wd">${w}</div>`).join("") + "<div></div>".repeat(lead);
      for (let d = first; +d.slice(5, 7) === m + 1; d = add(d, 1)) {
        const i = at(d), ok = i >= 0 && d >= o.min && d <= o.max;
        const v = ok ? Math.min(D.gen[i] / top, 1) : 0, share = ok && D.gen[i] ? D.wind[i] / D.gen[i] : 0;
        cells += `<button class="dp-day${v < .55 ? " light" : ""}${d === value ? " sel" : ""}${d === cursor ? " cur" : ""}" data-d="${d}"
          ${ok ? `style="background:${heat(v)}" title="${fmt(d)} · ${D.gen[i].toFixed(1)} MWh · ${Math.round(share * 100)}% wind"` : "disabled"}>
          ${+d.slice(8)}${ok ? `<u style="width:${Math.round(share * 30)}px"></u>` : ""}</button>`;
      }
      const mmax = Math.max(...monthly.filter((x) => x != null), 1e-9);
      pop.innerHTML = `<div class="dp-head"><div class="dp-years">${Array.from({ length: y1 - y0 + 1 }, (_, k) => y0 + k).map((yy) =>
          `<button class="dp-year${yy === y ? " on" : ""}" data-y="${yy}">${yy}${yy === y1 && o.max.slice(5) !== "12-31" ? `<sup>to ${MON[+o.max.slice(5, 7) - 1]}</sup>` : ""}</button>`).join("")}</div>
          <button class="dp-x" title="Close (Esc)">✕</button></div>
        <div class="dp-months">${MON.map((mn, k) => `<button class="dp-month${k === m ? " on" : ""}" data-m="${k}" ${monthly[k] == null ? "disabled" : ""}>
          ${monthly[k] == null ? "" : `<s style="height:${Math.max(2, 16 * monthly[k] / mmax)}px;background:${heat(monthly[k] / top)}"></s>`}${mn}</button>`).join("")}</div>
        <div class="dp-grid">${cells}</div>
        <div class="dp-foot">
          <div class="dp-legend">${o.site ? o.site + " · " : ""}daily energy <span style="background:${SCALE[0]}"></span><span style="background:${SCALE[2]}"></span><span style="background:${SCALE[4]}"></span><span style="background:${SCALE[5]}"></span> high · <span style="background:#3FD0F0;height:3px"></span> wind share</div>
          ${o.mode === "up" ? `<input class="dp-type" placeholder="Type a date: 14 Mar 2025" aria-label="Type a date" style="width:170px">` : ""}
        </div>
        ${o.mode === "up" ? `<div class="dp-chips" style="margin-top:8px">${presets().map(([l, d]) => `<button class="dp-chip" data-d="${d}" title="${fmt(d)}">${l}</button>`).join("")}</div>` : ""}
        <div class="dp-keys"><kbd>←</kbd><kbd>→</kbd> day · <kbd>↑</kbd><kbd>↓</kbd> week · <kbd>PgUp</kbd><kbd>PgDn</kbd> month · <kbd>Enter</kbd> open day · <kbd>Esc</kbd> close</div>`;
      const clampTo = (s) => (s < o.min ? o.min : s > o.max ? o.max : s);
      pop.querySelectorAll(".dp-year").forEach((b) => b.onclick = () => { cursor = clampTo(b.dataset.y + cursor.slice(4)); renderPop(); });
      pop.querySelectorAll(".dp-month").forEach((b) => b.onclick = () => { cursor = clampTo(`${y}-${String(+b.dataset.m + 1).padStart(2, "0")}-01`); renderPop(); });
      pop.querySelectorAll(".dp-day").forEach((b) => b.onclick = () => pick(b.dataset.d));
      pop.querySelectorAll(".dp-chip").forEach((b) => b.onclick = () => pick(b.dataset.d));
      pop.querySelector(".dp-x").onclick = () => setOpen(false);
      const type = pop.querySelector(".dp-type"); if (type) bindType(type);
    }

    // ---- keyboard: arrows step the day; inside the calendar they move the cursor ----
    const onKey = (e) => {
      if (e.target && /INPUT|TEXTAREA/.test(e.target.tagName)) return;
      const moves = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
      if (open) {
        if (e.key in moves) { cursor = add(cursor, moves[e.key]); }
        else if (e.key === "PageUp" || e.key === "PageDown") {
          const d = new Date(ms(cursor)); d.setUTCMonth(d.getUTCMonth() + (e.key === "PageUp" ? -1 : 1)); cursor = iso(d.getTime());
        } else if (e.key === "Enter") { pick(cursor); e.preventDefault(); return; }
        else if (e.key === "Escape") { setOpen(false); return; }
        else return;
        cursor = cursor < o.min ? o.min : cursor > o.max ? o.max : cursor;
        e.preventDefault(); renderPop();
      } else if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
        e.preventDefault(); pick(add(value, moves[e.key]));
      }
    };
    if (root._dpKey) document.removeEventListener("keydown", root._dpKey);
    root._dpKey = onKey; document.addEventListener("keydown", onKey);
    if (root._dpDown) document.removeEventListener("mousedown", root._dpDown);
    root._dpDown = (e) => { if (open && !el.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", root._dpDown);

    renderBar(); drawRibbon();
    o.onHeight(el.offsetHeight);
    return { set(v) { value = cursor = v; renderBar(); drawRibbon(); } };
  }

  window.DayPicker = { mount, parseTyped };
})();
