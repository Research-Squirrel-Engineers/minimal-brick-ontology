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

  // ---- tree -------------------------------------------------------------
  function makeNode(id) {
    var c = C[id], has = c.narrower.length > 0;
    var li = el("li");
    var tw = el("button", { class: "tw" + (has ? "" : " leaf"), "aria-label": "expand", text: "▸", onclick: function () { toggle(id); } });
    var row = el("div", { class: "node", "data-id": id }, tw);
    if (c.scheme === "colour" && id.indexOf("colour/group-") !== 0) row.appendChild(swatch(c));
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
      if (C[id].hex) b.appendChild(swatch(C[id]));
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
      tabs.appendChild(el("button", { "data-s": s.id, text: s.label + " (" + Object.keys(C).filter(function (k) { return C[k].scheme === s.id; }).length + ")", onclick: function () { setScheme(s.id); state.q = ""; document.getElementById("q").value = ""; } }));
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
