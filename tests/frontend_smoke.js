const assert = require("assert");
const fs = require("fs");
const path = require("path");

const html = fs.readFileSync(path.join(__dirname, "..", "site", "index.html"), "utf8");
const match = html.match(/<script>([\s\S]*)<\/script>/);
assert(match, "embedded script should exist");
const source = match[1].replace(/\ninit\(\);\s*$/, "\n");

const storage = new Map();
const localStorage = {
  getItem: key => storage.has(key) ? storage.get(key) : null,
  setItem: (key, value) => storage.set(key, String(value)),
};
const element = () => ({
  textContent: "",
  value: "",
  style: {},
  dataset: {},
  classList: { add() {}, remove() {}, toggle() {} },
  addEventListener() {},
  querySelector() { return element(); },
  querySelectorAll() { return []; },
});
const document = {
  body: element(),
  documentElement: element(),
  getElementById() { return element(); },
  querySelector() { return element(); },
  querySelectorAll() { return []; },
  createElement() { return element(); },
};
const window = {
  addEventListener() {},
  location: { href: "" },
  prompt() { return null; },
  alert() {},
};
const navigator = { clipboard: { writeText: async () => {} } };

const run = new Function("document", "window", "localStorage", "navigator", `${source}
  const paper = {
    id: "arxiv:2401.12345v2",
    title: "A Stable Test Paper",
    authors: ["Ada Lovelace"],
    date: "2026-07-29",
    source: "arXiv",
    url: "https://arxiv.org/abs/2401.12345v2",
    pdf: "https://arxiv.org/pdf/2401.12345v2",
    doi: "https://doi.org/10.1000/test",
    tags: ["time series"],
    abstract: "A test abstract.",
  };
  const id = paperStateId(paper);
  papersMap[id] = paper;
  currentData = { date: "2026-07-29", research_papers: [paper], ai_frontier: [] };
  researchMemory[id] = {
    paper: compactPaper(paper),
    addedAt: new Date().toISOString(),
    rememberedAt: new Date().toISOString(),
  };
  readStatus[id] = {
    status: "read",
    markedAt: new Date().toISOString(),
    history: [{ status: "read", at: new Date().toISOString() }],
  };
  notes[id] = [{ text: "A useful thought.", savedAt: new Date().toISOString() }];
  paperLinks[id] = { zoteroKey: "PXW99EKT" };
  cycleStatus(id, 0);
  const firstStatus = getStatus(id);
  cycleStatus(id, 0);
  const secondStatus = getStatus(id);
  cycleStatus(id, 0);
  const thirdStatus = getStatus(id);
  switchLang("en");
  const weeklyEn = renderWeeklyReview();
  switchLang("zh");
  toggleTheme();
  toggleTheme();
  return {
    id,
    arxivId: paperArxivId(paper),
    markdown: paperToMarkdown(paper),
    ris: buildRis(paper),
    weekly: renderWeeklyReview(),
    weeklyEn,
    statusFlow: [firstStatus, secondStatus, thirdStatus],
    filename: paperNoteFileName(paper),
  };
`);

const result = run(document, window, localStorage, navigator);
assert.strictEqual(result.id, "doi:10.1000/test");
assert.strictEqual(result.arxivId, "2401.12345");
assert(result.markdown.includes('canonical_id: "doi:10.1000/test"'));
assert(result.markdown.includes('arxiv_id: "2401.12345"'));
assert(result.markdown.includes('zotero_key: "PXW99EKT"'));
assert(result.markdown.includes("## 一句话总结"));
assert(result.ris.includes("DO  - 10.1000/test"));
assert(result.ris.includes("AN  - arXiv:2401.12345"));
assert(result.weekly.includes("本周阅读回顾"));
assert(result.weeklyEn.includes("Weekly Reading Review"));
assert(result.weekly.includes('class="num">1</span>'));
assert.deepStrictEqual(result.statusFlow, ["to_read", "reading", "read"]);
assert(result.filename.endsWith(".md"));
console.log("frontend smoke tests OK");
