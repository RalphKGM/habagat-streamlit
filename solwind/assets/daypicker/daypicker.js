/* SolWind day picker: a quiet date control with a small calendar, typed dates, a few shortcuts
   and keyboard stepping.

   The canonical copy lives in assets/daypicker/; assets/map/daypicker.js must be identical
   (tests/test_app.py checks this, because each Streamlit component serves only its own folder).

   DayPicker.mount(root, {
     daily: {start: "2020-01-01", gen: [MWh/day], wind: [MWh/day], grid: [MWh/day]},
     value: "YYYY-MM-DD", min, max,
     mode: "inline" | "up",      // inline: calendar opens below; up: calendar opens above (Map timeline)
     onPick(date), onHeight(px)  // onHeight lets the host iframe grow while the calendar is open
   })
*/
(function () {
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const MONTH = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const DAY = 864e5;

  const CSS = `
  .dp { position:relative; font:14px/1.35 'Archivo', system-ui, sans-serif; color:#15191C; }
  .dp button, .dp select { font:inherit; color:inherit; background:none; border:0; cursor:pointer; padding:0; }
  .dp-bar { display:inline-flex; align-items:center; gap:2px; border-bottom:1px solid #C9CEC9; }
  .dp-step { width:26px; height:32px; color:#60686E !important; font-size:16px !important; }
  .dp-step:hover { color:#15191C !important; }
  .dp-step:disabled { opacity:.25; cursor:default; }
  .dp-label { height:32px; padding:0 6px; font:500 15px 'Archivo', sans-serif !important; font-variant-numeric:tabular-nums; }
  .dp.open .dp-label, .dp-label:hover { color:#15191C !important; }
  .dp-pop { position:absolute; z-index:20; width:284px; background:#FFFFFF; border:1px solid #E1E4E0; padding:12px 12px 10px; }
  .dp-pop[hidden] { display:none; }
  .dp.inline .dp-pop { left:0; top:40px; }
  .dp.up .dp-pop { left:0; bottom:40px; }
  .dp-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; }
  .dp-head select { appearance:none; -webkit-appearance:none; font:500 14px 'Archivo', sans-serif !important; padding:2px 4px; }
  .dp-head select:hover { color:#15191C !important; }
  .dp-head select option { background:#FFFFFF; color:#15191C; }
  .dp-nav { width:26px; height:26px; color:#60686E !important; font-size:15px !important; }
  .dp-nav:hover { color:#15191C !important; }
  .dp-nav:disabled { opacity:.25; cursor:default; }
  .dp-grid { display:grid; grid-template-columns:repeat(7, 1fr); }
  .dp-wd { font-size:11px; color:#8A9297; text-align:center; padding:2px 0 6px; }
  .dp-day { height:32px; font-size:13px !important; font-variant-numeric:tabular-nums; color:#4A5258 !important; border:1px solid transparent !important; }
  .dp-day:hover { border-color:#C9CEC9 !important; }
  .dp-day.sel { color:#FFFFFF !important; background:#15191C !important; }
  .dp-day.cur { border-color:#60686E !important; }
  .dp-day:disabled { color:#C9CEC9 !important; cursor:default; border-color:transparent !important; }
  .dp-foot { border-top:1px solid #E1E4E0; margin-top:8px; padding-top:8px; display:flex; flex-direction:column; gap:7px; }
  .dp-type { width:100%; height:28px; background:none; border:0; border-bottom:1px solid #C9CEC9; color:#15191C; padding:0 2px; font:13px 'Archivo', sans-serif; outline:none; }
  .dp-type::placeholder { color:#8A9297; }
  .dp-type:focus { border-color:#15191C; }
  .dp-type.bad { border-color:#D64545; }
  .dp-links { display:flex; gap:12px; flex-wrap:wrap; }
  .dp-link { font-size:12.5px !important; color:#60686E !important; }
  .dp-link:hover { color:#15191C !important; }
  `;

  const ms = (s) => Date.parse(s + "T00:00:00Z");
  const iso = (t) => new Date(t).toISOString().slice(0, 10);
  const add = (s, n) => iso(ms(s) + n * DAY);
  const fmt = (s) => { const d = new Date(ms(s)); return `${WD[(d.getUTCDay() + 6) % 7]} ${d.getUTCDate()} ${MON[d.getUTCMonth()]} ${d.getUTCFullYear()}`; };

  function parseTyped(text, ref) {
    const s = text.trim().toLowerCase().replace(/,/g, " ").replace(/\s+/g, " ");
    if (!s) return null;
    const mon = (w) => MONTH.findIndex((n) => n.toLowerCase().startsWith(w)) + 1;
    let m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
    if (m) return mk(+m[1], +m[2], +m[3]);
    m = s.match(/^(\d{1,2})[\/.](\d{1,2})[\/.](\d{4})$/);           // day first: 14/03/2025
    if (m) return mk(+m[3], +m[2], +m[1]);
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
    let value = o.value, cursor = o.value, open = false;

    root.innerHTML = "";
    const el = document.createElement("div");
    el.className = "dp " + (o.mode === "up" ? "up" : "inline");
    root.appendChild(el);

    const shortcuts = () => {
      const best = (score) => { let bi = 0, bv = -Infinity; for (let i = 0; i < n; i++) { const v = score(i); if (v > bv) { bv = v; bi = i; } } return add(start, bi); };
      return [
        ["Windiest", best((i) => D.wind[i])],
        ["Sunniest", best((i) => D.gen[i] - D.wind[i])],
        ["Calmest", best((i) => -D.gen[i])],
        ["Random", add(start, Math.floor(Math.random() * n))],
      ];
    };

    function pick(s) {
      if (!s || s < o.min || s > o.max) return false;
      value = cursor = s;
      setOpen(false); renderBar();
      o.onPick(s);
      return true;
    }
    function setOpen(v) {
      open = v; el.classList.toggle("open", v); pop.hidden = !v;
      if (v) { cursor = value; renderPop(); }
      o.onHeight(v ? el.offsetHeight + pop.offsetHeight + 8 : el.offsetHeight);
    }

    const bar = document.createElement("div"); bar.className = "dp-bar"; el.appendChild(bar);
    function renderBar() {
      bar.innerHTML = `<button class="dp-step" data-s="-1" title="Previous day (←)" ${value <= o.min ? "disabled" : ""}>‹</button>
        <button class="dp-label" title="Choose a day">${fmt(value)}</button>
        <button class="dp-step" data-s="1" title="Next day (→)" ${value >= o.max ? "disabled" : ""}>›</button>`;
      bar.querySelectorAll(".dp-step").forEach((b) => b.onclick = () => pick(add(value, +b.dataset.s)));
      bar.querySelector(".dp-label").onclick = () => setOpen(!open);
    }

    const pop = document.createElement("div"); pop.className = "dp-pop"; pop.hidden = true; el.appendChild(pop);
    function renderPop() {
      const y = +cursor.slice(0, 4), m = +cursor.slice(5, 7) - 1;
      const y0 = +o.min.slice(0, 4), y1 = +o.max.slice(0, 4);
      const pad = (k) => String(k + 1).padStart(2, "0");
      const first = `${y}-${pad(m)}-01`;
      const lead = (new Date(ms(first)).getUTCDay() + 6) % 7;
      let cells = WD.map((w) => `<div class="dp-wd">${w.slice(0, 2)}</div>`).join("") + "<div></div>".repeat(lead);
      for (let d = first; +d.slice(5, 7) === m + 1; d = add(d, 1)) {
        const ok = d >= o.min && d <= o.max;
        cells += `<button class="dp-day${d === value ? " sel" : ""}${d === cursor && d !== value ? " cur" : ""}" data-d="${d}" ${ok ? "" : "disabled"}>${+d.slice(8)}</button>`;
      }
      const monthOk = (k) => `${y}-${pad(k)}-01` <= o.max && `${y}-${pad(k)}-31` >= o.min;
      const prevOk = first > o.min, nextOk = iso(Date.UTC(y, m + 1, 1)) <= o.max;
      pop.innerHTML = `<div class="dp-head">
          <button class="dp-nav" data-m="-1" ${prevOk ? "" : "disabled"} title="Previous month">‹</button>
          <div><select class="dp-mon" aria-label="Month">${MONTH.map((mn, k) => `<option value="${k}" ${k === m ? "selected" : ""} ${monthOk(k) ? "" : "disabled"}>${mn}</option>`).join("")}</select>
          <select class="dp-yr" aria-label="Year">${Array.from({ length: y1 - y0 + 1 }, (_, k) => y0 + k).map((yy) => `<option ${yy === y ? "selected" : ""}>${yy}</option>`).join("")}</select></div>
          <button class="dp-nav" data-m="1" ${nextOk ? "" : "disabled"} title="Next month">›</button></div>
        <div class="dp-grid">${cells}</div>
        <div class="dp-foot"><input class="dp-type" placeholder="Type a date, e.g. 14 Mar 2025" aria-label="Type a date">
          <div class="dp-links">${shortcuts().map(([l, d]) => `<button class="dp-link" data-d="${d}" title="${fmt(d)}">${l}</button>`).join("")}</div></div>`;
      const clampTo = (s) => (s < o.min ? o.min : s > o.max ? o.max : s);
      const go = (yy, mm) => { cursor = clampTo(iso(Date.UTC(yy, mm, 1))); renderPop(); };
      pop.querySelectorAll(".dp-nav").forEach((b) => b.onclick = () => go(y, m + +b.dataset.m));
      pop.querySelector(".dp-mon").onchange = (e) => go(y, +e.target.value);
      pop.querySelector(".dp-yr").onchange = (e) => go(+e.target.value, m);
      pop.querySelectorAll(".dp-day, .dp-link").forEach((b) => b.onclick = () => pick(b.dataset.d));
      const input = pop.querySelector(".dp-type");
      input.onkeydown = (e) => {
        e.stopPropagation();
        if (e.key === "Escape") return setOpen(false);
        if (e.key !== "Enter") return input.classList.remove("bad");
        if (!pick(parseTyped(input.value, value))) input.classList.add("bad");
      };
    }

    // Arrows step the day; with the calendar open they move the highlighted day instead.
    const onKey = (e) => {
      if (e.target && /INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return;
      const moves = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
      if (open) {
        if (e.key === "Escape") return setOpen(false);
        if (e.key === "Enter") { e.preventDefault(); return pick(cursor); }
        if (!(e.key in moves)) return;
        e.preventDefault();
        const c = add(cursor, moves[e.key]);
        cursor = c < o.min ? o.min : c > o.max ? o.max : c;
        renderPop();
      } else if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
        e.preventDefault(); pick(add(value, moves[e.key]));
      }
    };
    if (root._dpKey) document.removeEventListener("keydown", root._dpKey);
    root._dpKey = onKey; document.addEventListener("keydown", onKey);
    if (root._dpDown) document.removeEventListener("mousedown", root._dpDown);
    root._dpDown = (e) => { if (open && !el.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", root._dpDown);

    renderBar();
    o.onHeight(el.offsetHeight);
    return { set(v) { value = cursor = v; renderBar(); } };
  }

  window.DayPicker = { mount, parseTyped };
})();
