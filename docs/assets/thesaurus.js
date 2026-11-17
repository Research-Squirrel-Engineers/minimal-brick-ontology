/* Click-through hierarchical thesaurus. Plain DOM, no dependencies. */
(function () {
  "use strict";
  var D = window.MBO_DATA, C = D.concepts, S = D.sources;
  var state = { scheme: D.schemes[0].id, sel: null, q: "", ver: "" };
  var nodes = {};            // id -> {li, kids(ul), open}
  var memo = {};

  function el(tag, attrs) {
    var e = document.createElement(tag);
    attrs = attrs || {};
    Object.keys(attrs).forEach(function (k) {
      if (k === "class") e.className = attrs[k];
      else if (k === "text") e.textContent = attrs[k];
      else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), attrs[k]);
      else e.setAttribute(k, attrs[k]);
    });
    for (var i = 2; i < arguments.length; i++) {
      var kid = arguments[i];
      if (kid == null) continue;
      e.appendChild(kid.nodeType ? kid : document.createTextNode(kid));
    }
    return e;
  }
  function byLabel(a, b) { return C[a].label.toLowerCase() < C[b].label.toLowerCase() ? -1 : C[a].label.toLowerCase() > C[b].label.toLowerCase() ? 1 : 0; }
  function count(id) {
    if (memo[id] !== undefined) return memo[id];
    var n = C[id].narrower, t = 0;
    for (var i = 0; i < n.length; i++) t += C[n[i]].narrower.length ? count(n[i]) : 1;
    return (memo[id] = t);
  }
  function swatch(c) {
    return el("span", { class: "sw" + (c.hex ? "" : " none"), style: c.hex ? "background:#" + c.hex : "" });
  }
  function badge(v) { return el("span", { class: "badge b-" + v, text: v }); }

  // ---- icons (inline SVG, generated from the data; flat house colours) ----
  var NS = "http://www.w3.org/2000/svg", FILL = "#e2e8f0", STUD = "#ffffff", INK = "#000000";
  function sv(tag, a, kids) {
    var e = document.createElementNS(NS, tag);
    Object.keys(a || {}).forEach(function (k) { e.setAttribute(k, a[k]); });
    (kids || []).forEach(function (k) { e.appendChild(k); });
    return e;
  }
  function shape(tag, a, fill) { a = a || {}; a.fill = fill || FILL; a.stroke = INK; a["stroke-width"] = a["stroke-width"] || 1; a["stroke-linejoin"] = "round"; return sv(tag, a); }
  function pr(c, label) { for (var i = 0; i < c.props.length; i++) if (c.props[i][0].indexOf(label) === 0) return c.props[i][1]; return null; }
  function rootCat(id) {
    var p = chain(id);
    for (var i = p.length - 1; i >= 0; i--) if (/^part\/(brick|plate|tile|baseplate|minifig-)/.test(p[i])) return p[i];
    return null;
  }
  // oblique front view: body, top face, right face, studs on the top face
  function blockIcon(L, W, hp, studs, round) {
    var Lc = Math.max(1, Math.min(L, 8)), Wc = Math.max(1, Math.min(W, 4));
    var p = Math.min(4.4, 34 / Lc), q = 2.2, qy = 1.3, bh = Math.min(hp, 3) * 3.6;
    var tw = Lc * p + Wc * q, x0 = (48 - tw) / 2, yb = 15 + (bh + Wc * qy) / 2, yt = yb - bh;
    var g = [];
    if (round) {
      var cx = 24, rx = 8, ry = 4.2;
      g.push(shape("path", { d: "M" + (cx - rx) + " " + (yt) + "L" + (cx - rx) + " " + yb + "A" + rx + " " + ry + " 0 0 0 " + (cx + rx) + " " + yb + "L" + (cx + rx) + " " + yt + "Z" }));
      g.push(shape("ellipse", { cx: cx, cy: yt, rx: rx, ry: ry }));
      g.push(shape("ellipse", { cx: cx, cy: yt - 0.8, rx: 3, ry: 1.7 }, STUD));
      return g;
    }
    var rx0 = x0 + Lc * p, bx = Wc * q, by = Wc * qy;
    g.push(shape("rect", { x: x0, y: yt, width: Lc * p, height: bh }));
    g.push(shape("polygon", { points: rx0 + "," + yt + " " + (rx0 + bx) + "," + (yt - by) + " " + (rx0 + bx) + "," + (yb - by) + " " + rx0 + "," + yb }, "#cbd5e1"));
    g.push(shape("polygon", { points: x0 + "," + yt + " " + rx0 + "," + yt + " " + (rx0 + bx) + "," + (yt - by) + " " + (x0 + bx) + "," + (yt - by) }, "#f1f5f9"));
    if (studs) for (var j = Wc - 1; j >= 0; j--) for (var i = 0; i < Lc; i++)
      g.push(shape("ellipse", { cx: x0 + (i + .5) * p + (j + .5) * q, cy: yt - (j + .5) * qy - .4, rx: Math.min(1.5, p * .34), ry: .9 }, STUD));
    return g;
  }
  function minifigGlyph(kind) {
    var f = function (t, a, c) { return shape(t, a, c); };
    switch (kind) {
      case "head": return [f("rect", { x: 21, y: 3, width: 6, height: 3 }, STUD), f("rect", { x: 16, y: 6, width: 16, height: 17, rx: 5 }), f("circle", { cx: 21, cy: 13, r: 1 }, INK), f("circle", { cx: 27, cy: 13, r: 1 }, INK), f("path", { d: "M20 18Q24 21 28 18", fill: "none" })];
      case "torso": return [f("rect", { x: 21, y: 3, width: 6, height: 3 }, STUD), f("rect", { x: 17, y: 6, width: 14, height: 19 }), f("rect", { x: 10, y: 6, width: 7, height: 10, rx: 2 }, "#cbd5e1"), f("rect", { x: 31, y: 6, width: 7, height: 10, rx: 2 }, "#cbd5e1")];
      case "hips": return [f("rect", { x: 14, y: 9, width: 20, height: 11 }), f("path", { d: "M24 20V13", fill: "none" }), f("rect", { x: 20, y: 6, width: 8, height: 3 }, STUD)];
      case "leg": return [f("rect", { x: 18, y: 3, width: 12, height: 20 }), f("rect", { x: 16, y: 23, width: 16, height: 5, rx: 1 }, "#cbd5e1")];
      case "arm": return [f("polygon", { points: "18,4 27,4 31,22 22,22" }), f("rect", { x: 20, y: 22, width: 10, height: 4, rx: 2 }, "#cbd5e1")];
      case "hand": return [f("path", { d: "M30 9A8 8 0 1 0 30 21L26 18A3.5 3.5 0 1 1 26 12Z" })];
      case "headwear": return [f("path", { d: "M12 20Q12 6 24 6Q36 6 36 20Z" }), f("rect", { x: 8, y: 20, width: 32, height: 4, rx: 2 }, "#cbd5e1")];
      default: return [f("circle", { cx: 24, cy: 8, r: 4.5 }), f("rect", { x: 18, y: 13, width: 12, height: 8 }), f("rect", { x: 18, y: 21, width: 5.5, height: 7 }, "#cbd5e1"), f("rect", { x: 24.5, y: 21, width: 5.5, height: 7 }, "#cbd5e1")];
    }
  }
  function glyph(id, c) {
    if (c.scheme === "feature") {
      if (/stud$/.test(id)) return [shape("rect", { x: 14, y: 14, width: 20, height: 12 }), shape("ellipse", { cx: 24, cy: 14, rx: 10, ry: 4 }, "#f1f5f9"), shape("rect", { x: 19, y: 7, width: 10, height: 7, rx: 1 }, STUD), shape("ellipse", { cx: 24, cy: 7, rx: 5, ry: 2 }, STUD)];
      if (/tube$/.test(id)) return [shape("rect", { x: 8, y: 6, width: 32, height: 20 }), shape("circle", { cx: 24, cy: 16, r: 6 }, STUD), shape("circle", { cx: 24, cy: 16, r: 2.6 })];
      return [shape("path", { d: "M8 26V12Q8 6 14 6H34Q40 6 40 12V26Z" }), shape("path", { d: "M14 26V13H34V26", fill: "#fff" })];
    }
    if (c.scheme === "unit") {
      var t = [shape("rect", { x: 5, y: 9, width: 38, height: 13, rx: 1.5 }, "#fde68a")];
      for (var i = 0; i < 8; i++) t.push(sv("path", { d: "M" + (9 + i * 4.6) + " 9v" + (i % 2 ? 4 : 6), stroke: INK, "stroke-width": 1, fill: "none" }));
      return t;
    }
    if (c.scheme === "identifier-system") return [shape("path", { d: "M6 6H24L42 15L24 24H6Z" }, "#fde68a"), shape("circle", { cx: 12, cy: 15, r: 2 }, STUD), sv("path", { d: "M22 11l-2 8M28 11l-2 8M18 13h12M17 17h12", stroke: INK, "stroke-width": 1, fill: "none" })];
    if (c.scheme === "colour") {
      if (id.indexOf("colour/group-") !== 0) return null;
      var cols = /transparent/.test(id) ? ["#bfdbfe", "#bbf7d0", "#fecaca", "#fef08a"] : /metallic/.test(id) ? ["#d4d4d8", "#a8a29e", "#fcd34d", "#94a3b8"] : /special/.test(id) ? ["#c4b5fd", "#f9a8d4", "#fdba74", "#86efac"] : ["#1f2937", "#dc2626", "#2563eb", "#facc15"];
      return [shape("rect", { x: 11, y: 4, width: 12, height: 11 }, cols[0]), shape("rect", { x: 25, y: 4, width: 12, height: 11 }, cols[1]), shape("rect", { x: 11, y: 17, width: 12, height: 11 }, cols[2]), shape("rect", { x: 25, y: 17, width: 12, height: 11 }, cols[3])];
    }
    if (c.scheme === "part") {
      var cat = rootCat(id) || "";
      if (/minifig-?part$/.test(cat) || id === "part/minifig-part") return minifigGlyph("");
      var m = /minifig-(\w+)$/.exec(id.indexOf("part/minifig-") === 0 ? id : cat);
      if (m) return minifigGlyph(m[1]);
      var st = pr(c, "Studs"), hh = pr(c, "Height in plates"), L = 2, W = 4, hp = 3, studs = true, round = /round/i.test(c.label);
      var kind = cat.replace("part/", "");
      if (kind === "plate") { L = 4; W = 2; hp = 1; }
      if (kind === "tile") { L = 2; W = 2; hp = 1; studs = false; }
      if (kind === "baseplate") { L = 8; W = 4; hp = 1; }
      if (kind === "brick") { L = 4; W = 2; hp = 3; }
      var mm = st && /(\d+)\s*x\s*(\d+)/.exec(st);
      if (mm) { L = Math.max(+mm[1], +mm[2]); W = Math.min(+mm[1], +mm[2]); }
      if (hh && !isNaN(+hh)) hp = +hh; else if (kind === "brick") hp = 3;
      if (id.indexOf("part/") === 0 && C[id].narrower.length) { L = kind === "baseplate" ? 8 : 4; W = 2; if (kind === "baseplate") W = 4; }
      return blockIcon(L, W, hp, studs && kind !== "tile", round && !!mm && L === 1 && W === 1);
    }
    return null;
  }
  var SCHEME_ICON = { colour: "colour/group-solid", part: "part/brick", feature: "feature/stud", unit: "unit/stud-pitch", "identifier-system": "identifier-system/design-id" };
  function icon(id, big) {
    var c = C[id], g = c && glyph(id, c);
    if (!g) return null;
    return sv("svg", { "class": "ic" + (big ? " big" : ""), viewBox: "0 0 48 30", "aria-hidden": "true", preserveAspectRatio: "xMidYMid meet" }, g);
  }

  // ---- tree -------------------------------------------------------------
  function makeNode(id) {
    var c = C[id], has = c.narrower.length > 0;
    var li = el("li");
    var tw = el("button", { class: "tw" + (has ? "" : " leaf"), "aria-label": "expand", text: "▸", onclick: function () { toggle(id); } });
    var row = el("div", { class: "node", "data-id": id }, tw);
    if (c.scheme === "colour" && id.indexOf("colour/group-") !== 0) row.appendChild(swatch(c));
    else { var ic = icon(id); if (ic) row.appendChild(ic); }
    row.appendChild(el("button", { class: "lbl", text: c.label, onclick: function () { select(id, true); } }));
    if (has) row.appendChild(el("span", { class: "cnt", text: "(" + count(id) + ")" }));
    li.appendChild(row);
    nodes[id] = { li: li, row: row, tw: tw, kids: null, open: false };
    return li;
  }
  function toggle(id, force) {
    var n = nodes[id]; if (!n || !C[id].narrower.length) return;
    var open = force === undefined ? !n.open : force;
    if (open && !n.kids) {
      n.kids = el("ul");
      C[id].narrower.forEach(function (k) { n.kids.appendChild(makeNode(k)); });
      n.li.appendChild(n.kids);
    }
    if (n.kids) n.kids.style.display = open ? "" : "none";
    n.open = open; n.tw.textContent = open ? "▾" : "▸";
  }
  function renderTree() {
    nodes = {}; memo = {};
    var box = document.getElementById("tree"); box.innerHTML = "";
    var ul = el("ul", { class: "tree" });
    var sc = D.schemes.filter(function (s) { return s.id === state.scheme; })[0];
    sc.top.slice().sort(byLabel).forEach(function (id) { ul.appendChild(makeNode(id)); });
    box.appendChild(ul);
  }
  function chain(id) { var p = [], c = id, guard = 0; while (c && guard++ < 20) { p.unshift(c); c = C[c].broader[0]; } return p; }
  function reveal(id) {
    var p = chain(id);
    if (C[id].scheme !== state.scheme) { setScheme(C[id].scheme); }
    for (var i = 0; i < p.length - 1; i++) toggle(p[i], true);
  }

  // ---- detail -----------------------------------------------------------
  function select(id, fromTree) {
    state.sel = id;
    if (!fromTree) reveal(id);
    document.querySelectorAll(".node.sel").forEach(function (n) { n.classList.remove("sel"); });
    if (nodes[id]) { nodes[id].row.classList.add("sel"); if (!fromTree) nodes[id].row.scrollIntoView({ block: "nearest" }); }
    history.replaceState(null, "", "#" + id);
    renderDetail(id);
  }
  function chips(ids) {
    var w = el("div", { class: "chips" });
    ids.slice(0, 200).forEach(function (k) { w.appendChild(el("button", { class: "chip", text: C[k].label, onclick: function () { select(k); } })); });
    if (ids.length > 200) w.appendChild(el("span", { class: "muted", text: "… and " + (ids.length - 200) + " more" }));
    return w;
  }
  function renderDetail(id) {
    var c = C[id], d = document.getElementById("detail"); d.innerHTML = "";
    var bigIc = icon(id, true); if (bigIc) d.appendChild(bigIc);
    d.appendChild(el("h2", { text: c.label }));
    var meta = el("div", {}, badge(c.verification || "derived"), " ", el("span", { class: "muted", text: " " + D.schemes.filter(function (s) { return s.id === c.scheme; })[0].label }));
    d.appendChild(meta);
    if (c.labelDe) d.appendChild(el("div", { class: "muted", text: "DE: " + c.labelDe }));
    d.appendChild(el("div", { class: "path", text: chain(id).map(function (x) { return C[x].label; }).join("  ›  ") }));
    if (c.scheme === "colour") d.appendChild(el("div", { class: "bigsw" + (c.hex ? "" : " sw none"), style: c.hex ? "background:#" + c.hex : "" }));
    if (c.alt.length) d.appendChild(el("p", {}, el("strong", { text: "Also called: " }), c.alt.join("; ")));
    if (c.definition) d.appendChild(el("p", { text: c.definition }));
    if (c.note) d.appendChild(el("blockquote", { text: c.note }));
    if (c.props.length) {
      var t = el("table");
      c.props.forEach(function (p) { t.appendChild(el("tr", {}, el("th", { text: p[0] }), el("td", { text: p[1] }))); });
      d.appendChild(t);
    }
    d.appendChild(el("h3", { text: "IRI" }));
    d.appendChild(el("div", {}, el("a", { href: c.iri, text: c.iri }), " ",
      el("button", { class: "copy", text: "Copy", onclick: function (e) { if (navigator.clipboard) navigator.clipboard.writeText(c.iri); e.target.textContent = "Copied"; } })));
    if (c.broader.length) { d.appendChild(el("h3", { text: "Broader" })); d.appendChild(chips(c.broader)); }
    if (c.narrower.length) { d.appendChild(el("h3", { text: "Narrower (" + c.narrower.length + ")" })); d.appendChild(chips(c.narrower)); }
    if (c.sources.length) {
      d.appendChild(el("h3", { text: "Sources" }));
      var ul = el("ul");
      c.sources.forEach(function (sid) {
        var s = S[sid];
        ul.appendChild(el("li", {}, el("a", { href: s.url, text: s.title }), " ", el("span", { class: "muted", text: "[" + s.kind + "]" })));
      });
      d.appendChild(ul);
    }
  }

  // ---- search -----------------------------------------------------------
  function search(q) {
    var res = [], ql = q.toLowerCase();
    Object.keys(C).forEach(function (id) {
      var c = C[id];
      if (state.ver && c.verification !== state.ver) return;
      var hay = (c.label + " " + c.alt.join(" ") + " " + c.props.map(function (p) { return p[1]; }).join(" ") + " " + (c.hex ? "#" + c.hex : "")).toLowerCase();
      if (hay.indexOf(ql) >= 0) res.push(id);
    });
    return res.sort(byLabel);
  }
  function refresh() {
    var box = document.getElementById("tree"), q = state.q.trim();
    if (q.length < 2 && !state.ver) { renderTree(); if (state.sel && C[state.sel].scheme === state.scheme) reveal(state.sel); return; }
    var hits = search(q.length < 2 ? "" : q);
    box.innerHTML = "";
    box.appendChild(el("div", { class: "muted", text: hits.length + " hits" + (hits.length > 300 ? " (first 300 shown)" : "") }));
    hits.slice(0, 300).forEach(function (id) {
      var b = el("button", { class: "hit", onclick: function () { state.q = ""; document.getElementById("q").value = ""; state.ver = ""; document.getElementById("ver").value = ""; select(id); } });
      if (C[id].hex) b.appendChild(swatch(C[id])); else { var hi = icon(id); if (hi) b.appendChild(hi); }
      b.appendChild(document.createTextNode(" " + C[id].label + " "));
      b.appendChild(el("span", { class: "path", text: chain(id).slice(0, -1).map(function (x) { return C[x].label; }).join(" › ") }));
      box.appendChild(b);
    });
  }

  // ---- shell ------------------------------------------------------------
  function setScheme(s) {
    state.scheme = s;
    document.querySelectorAll(".tabs button").forEach(function (b) { b.classList.toggle("on", b.getAttribute("data-s") === s); });
    renderTree();
  }
  function init() {
    var tabs = document.getElementById("tabs");
    D.schemes.forEach(function (s) {
      var ti = SCHEME_ICON[s.id] && C[SCHEME_ICON[s.id]] ? icon(SCHEME_ICON[s.id]) : null;
      var tb = el("button", { "data-s": s.id, onclick: function () { setScheme(s.id); state.q = ""; document.getElementById("q").value = ""; } });
      if (ti) tb.appendChild(ti);
      tb.appendChild(document.createTextNode(" " + s.label + " (" + Object.keys(C).filter(function (k) { return C[k].scheme === s.id; }).length + ")"));
      tabs.appendChild(tb);
    });
    document.getElementById("q").addEventListener("input", function (e) { state.q = e.target.value; refresh(); });
    document.getElementById("ver").addEventListener("change", function (e) { state.ver = e.target.value; refresh(); });
    document.getElementById("expand").addEventListener("click", function () {
      var total = Object.keys(C).filter(function (k) { return C[k].scheme === state.scheme; }).length;
      if (total > 1500) { alert("Too many concepts to expand at once; use search or expand single branches."); return; }
      var guard = 0; (function walk(ids) { ids.forEach(function (id) { if (C[id].narrower.length && guard++ < 3000) { toggle(id, true); walk(C[id].narrower); } }); })(D.schemes.filter(function (s) { return s.id === state.scheme; })[0].top);
    });
    document.getElementById("collapse").addEventListener("click", function () { renderTree(); });
    function fromHash() {
      var h = decodeURIComponent(location.hash.slice(1));
      if (h && C[h]) { setScheme(C[h].scheme); select(h); } else { setScheme(state.scheme); }
    }
    window.addEventListener("hashchange", function () { var h = decodeURIComponent(location.hash.slice(1)); if (h && C[h] && h !== state.sel) { setScheme(C[h].scheme); select(h); } });
    fromHash();
  }
  init();
})();
