// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The front page: every braid the studio offers as it comes, in a table to
// filter by what the braid is.  braidpy says it all when the site is built
// (braids.json, braidpy.web.braids); this only shows it.  Each braid opens
// in the studio (make.html), made with the site, so shown at once.

const $ = (id) => document.getElementById(id);

// What each kind of link is called beside it.
const KIND = { book: "Book", article: "Article", video: "Video", page: "Page", post: "Post" };

// Each braid's picture, settled, taken when the site was built
// (web/snapshots.py); a braid without one shows none.
const picture = (key) => `snapshots/${key}.webp`;

const loading = (name) =>
  fetch(name, { cache: "no-cache" })
    .then((response) => (response.ok ? response.json() : null))
    .catch(() => null);

const [braids, catalogue] = await Promise.all([loading("braids.json"), loading("catalogue.json")]);
const rows = (braids ?? []).map((braid) => ({ ...braid, n_loops: braid.loops?.length }));

// The sources, by the names the studio gives them.
const sourceName = (source) => catalogue?.[source]?.title ?? source;
for (const source of [...new Set(rows.map((row) => row.source))]) {
  $("source").append(new Option(sourceName(source), source));
}

function element(tag, props = {}, ...children) {
  const node = Object.assign(document.createElement(tag), props);
  node.append(...children.filter((child) => child !== null && child !== undefined));
  return node;
}

const dash = () => element("span", { className: "muted", title: "Not known yet" }, "—");

function studio(spec) {
  return "make.html#" + new URLSearchParams(Object.entries(spec).map(([k, v]) => [k, String(v)]));
}

function row(braid) {
  const open = studio(braid.spec);
  const image = element("img", {
    src: picture(braid.key),
    alt: "",
    loading: "lazy",
    width: 96,
    height: 128,
  });
  image.addEventListener("error", () => image.replaceWith(element("span", { className: "no-picture" })));
  const links = braid.links.length
    ? element(
        "ul",
        { className: "links" },
        ...braid.links.map((link) =>
          element(
            "li",
            {},
            element("span", { className: `kind kind-${link.kind}` }, KIND[link.kind] ?? link.kind),
            " ",
            link.url
              ? element("a", { href: link.url, rel: "noopener", target: "_blank" }, link.title)
              : link.title,
          ),
        ),
      )
    : dash();
  const loops = braid.loops
    ? element(
        "span",
        { title: braid.loops.length === braid.n_strands ? "A loop per strand: pure" : "" },
        braid.loops.join(" · "),
      )
    : dash();
  return element(
    "tr",
    {},
    element("td", { className: "pic" }, element("a", { href: open, tabIndex: -1 }, image)),
    element(
      "td",
      {},
      element("a", { href: open, className: "title" }, braid.title),
      element("div", { className: "muted" }, sourceName(braid.source)),
    ),
    element("td", { className: "num" }, braid.n_strands ?? dash()),
    element("td", { className: "num" }, loops),
    element("td", { className: "num" }, braid.writhe ?? dash()),
    element("td", { className: "same" }, braid.same?.length ? braid.same.join("; ") : dash()),
    element("td", {}, links),
  );
}

const number = (id) => {
  const value = $(id).value.trim();
  return value === "" ? null : Number(value);
};

// A braid the filter asks a figure of, and that has none, is left out.
function within(value, low, high) {
  if (low === null && high === null) return true;
  if (value === undefined || value === null) return false;
  return (low === null || value >= low) && (high === null || value <= high);
}

function kept(braid) {
  const words = $("search").value.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const text = [braid.title, sourceName(braid.source), ...braid.links.map((l) => l.title), ...(braid.same ?? [])]
    .join(" ")
    .toLowerCase();
  if (!words.every((word) => text.includes(word))) return false;
  if ($("source").value && braid.source !== $("source").value) return false;
  if (!within(braid.n_strands, number("strands_min"), number("strands_max"))) return false;
  if (!within(braid.writhe, number("writhe_min"), number("writhe_max"))) return false;
  const loops = $("loops").value;
  if (loops) {
    if (!braid.loops) return false;
    if (loops === "one" && braid.n_loops !== 1) return false;
    if (loops === "several" && braid.n_loops < 2) return false;
    if (loops === "pure" && braid.n_loops !== braid.n_strands) return false;
  }
  if ($("linked").checked && !braid.links.some((link) => link.url)) return false;
  return true;
}

// Sorted by a column clicked, again the other way; in the studio's order
// to start with.
let sort = null;
function ordered(list) {
  if (!sort) return list;
  const { key, way } = sort;
  return [...list].sort((a, b) => {
    const x = a[key];
    const y = b[key];
    if (x === undefined || x === null) return 1;
    if (y === undefined || y === null) return -1;
    return (typeof x === "string" ? x.localeCompare(y) : x - y) * way;
  });
}

function show() {
  const list = ordered(rows.filter(kept));
  $("braids").tBodies[0].replaceChildren(...list.map(row));
  $("count").textContent = braids
    ? `${list.length} of ${rows.length} braids`
    : "The list of braids could not be loaded.";
}

for (const header of document.querySelectorAll("th[data-sort]")) {
  header.tabIndex = 0;
  const choose = () => {
    const key = header.dataset.sort;
    sort = sort?.key === key ? { key, way: -sort.way } : { key, way: 1 };
    for (const other of document.querySelectorAll("th[data-sort]")) other.removeAttribute("aria-sort");
    header.setAttribute("aria-sort", sort.way > 0 ? "ascending" : "descending");
    show();
  };
  header.addEventListener("click", choose);
  header.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      choose();
    }
  });
}

$("filters").addEventListener("input", show);
$("filters").addEventListener("reset", () => setTimeout(show));
show();
