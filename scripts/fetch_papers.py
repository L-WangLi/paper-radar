#!/usr/bin/env python3
"""
Paper Radar - Daily Paper Fetcher
Sources: arXiv, Semantic Scholar, OpenReview, OpenAlex, CrossRef, HuggingFace Daily Papers, Papers with Code, RSS feeds
Outputs date-based JSON files + index.json for the static site.
"""

import json
import hashlib
import os
import re
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================
# Configuration
# ============================================================

RESEARCH_KEYWORDS = [
    # Core RUL / PHM
    "remaining useful life",
    "RUL estimation",
    "RUL prediction",
    "predictive maintenance",
    "condition-based maintenance",
    "condition based maintenance",
    "prognostics health management",
    "prognostics and health management",
    "PHM deep learning",
    "C-MAPSS",
    "N-CMAPSS",
    "turbofan engine degradation",
    "fault diagnosis deep learning",
    "degradation modeling",
    "degradation prediction",
    "condition monitoring deep learning",
    # Knowledge Distillation / Compression
    "knowledge distillation",
    "model compression edge deployment",
    "lightweight deep learning industrial",
    # Time Series / Architecture
    "temporal convolutional network",
    "temporal transformer",
    "multivariate time series forecasting",
    "time series classification",
    # Time Series Methods (transferable to RUL)
    "Mamba state space model time series",
    "time series foundation model",
    "PatchTST",
    "anomaly detection time series industrial",
    "time series transformer",
    # More RUL / PHM specific
    "bearing fault diagnosis deep learning",
    "LSTM remaining useful life",
    "transfer learning fault diagnosis",
    "domain adaptation predictive maintenance",
    "physics-informed neural network degradation",
    "graph neural network fault diagnosis",
    "attention mechanism bearing",
    "vibration signal deep learning",
    # Methods (broad but common in PHM)
    "self-supervised learning prognostics",
    "contrastive learning fault diagnosis",
    "few-shot fault diagnosis",
    "meta learning prognostics",
    "domain generalization fault diagnosis",
    "federated learning predictive maintenance",
    # Datasets / Benchmarks
    "PHM 2008",
    "PHM08",
    "PRONOSTIA",
    "FEMTO",
    "XJTU-SY",
    "IMS bearing",
    "CWRU bearing",
    "Paderborn bearing",
    "SEU bearing",
    "MFPT bearing",
]

AI_FRONTIER_KEYWORDS = [
    "large language model",
    "diffusion model",
    "multimodal foundation model",
    "AI agent reasoning",
    "reinforcement learning human feedback",
    "vision language model",
    "test time compute scaling",
    "model alignment",
]

METHOD_KEYWORDS = [
    "self-supervised learning",
    "contrastive learning",
    "few-shot learning",
    "meta learning",
    "domain generalization",
    "transfer learning",
    "domain adaptation",
    "federated learning",
    "representation learning",
    "anomaly detection",
    "time series forecasting",
    "time series classification",
    "transformer",
    "state space model",
    "graph neural network",
    "physics-informed",
]

DATASET_KEYWORDS = [
    "C-MAPSS",
    "CMAPSS",
    "N-CMAPSS",
    "PHM 2008",
    "PHM08",
    "PRONOSTIA",
    "FEMTO",
    "XJTU-SY",
    "IMS",
    "IMS bearing",
    "CWRU",
    "CWRU bearing",
    "Paderborn",
    "Paderborn bearing",
    "SEU",
    "SEU bearing",
    "MFPT",
    "MFPT bearing",
]

TAG_KEYWORDS = list(dict.fromkeys(RESEARCH_KEYWORDS + METHOD_KEYWORDS + DATASET_KEYWORDS))
SHORT_KEYWORDS = {"RUL", "PHM", "SOH", "CBM"}

RSS_FEEDS = [
    # AI Lab Blogs
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "category": "ai_frontier"},
    {"name": "Anthropic Blog", "url": "https://www.anthropic.com/rss/blog.xml", "category": "ai_frontier"},
    {"name": "DeepMind Blog", "url": "https://deepmind.google/blog/rss.xml", "category": "ai_frontier"},
    {"name": "Google AI Blog", "url": "https://blog.research.google/feeds/posts/default", "category": "ai_frontier"},
    {"name": "Meta AI Blog", "url": "https://ai.meta.com/blog/feed/", "category": "ai_frontier"},
    {"name": "Microsoft Research", "url": "https://www.microsoft.com/en-us/research/feed/", "category": "ai_frontier"},
    # Academic Research Blogs
    {"name": "BAIR Blog", "url": "https://bair.berkeley.edu/blog/feed.xml", "category": "ai_frontier"},
    {"name": "Allen AI (AI2)", "url": "https://allenai.org/blog/rss.xml", "category": "ai_frontier"},
    {"name": "NVIDIA AI Blog", "url": "https://blogs.nvidia.com/blog/category/deep-learning/feed/", "category": "ai_frontier"},
    # AI News & Digests
    {"name": "HuggingFace Blog", "url": "https://huggingface.co/blog/feed.xml", "category": "ai_frontier"},
    {"name": "The Batch (deeplearning.ai)", "url": "https://www.deeplearning.ai/the-batch/feed/", "category": "ai_frontier"},
    {"name": "Import AI", "url": "https://importai.substack.com/feed", "category": "ai_frontier"},
    {"name": "The Gradient", "url": "https://thegradient.pub/rss/", "category": "ai_frontier"},
    {"name": "MIT Technology Review AI", "url": "https://www.technologyreview.com/feed/", "category": "ai_frontier"},
    {"name": "Stanford HAI", "url": "https://hai.stanford.edu/blog/feed", "category": "ai_frontier"},
    # Community
    {"name": "Reddit r/MachineLearning", "url": "https://www.reddit.com/r/MachineLearning/top/.rss?t=week", "category": "ai_frontier"},
    # Additional AI feeds
    {"name": "Amazon Science", "url": "https://www.amazon.science/index.rss", "category": "ai_frontier"},
    {"name": "Planet AI (Aggregator)", "url": "https://planet-ai.net/rss.xml", "category": "ai_frontier"},
    # Chinese AI Media
    {"name": "量子位", "url": "https://www.qbitai.com/feed", "category": "ai_frontier"},
    {"name": "机器之心", "url": "https://www.jiqizhixin.com/rss", "category": "ai_frontier"},
    {"name": "AI科技评论", "url": "https://aitechtalk.com/feed", "category": "ai_frontier"},
    {"name": "36氪 AI", "url": "https://36kr.com/feed", "category": "ai_frontier"},
]

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
SITE_DIR = BASE_DIR / "site"

DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

CACHE_EXPIRY_DAYS = 7


# ============================================================
# Utilities
# ============================================================

def safe_request(url, headers=None, max_retries=3, delay=2):
    """HTTP request with retries."""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "PaperRadar/1.0 (research-tool)")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except Exception as e:
            print(f"  [retry {attempt+1}/{max_retries}] {url[:80]}... → {e}")
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
    return None


def get_cache(key):
    """Read from cache if not expired."""
    cache_file = CACHE_DIR / f"{hashlib.md5(key.encode()).hexdigest()}.json"
    if cache_file.exists():
        data = json.loads(cache_file.read_text("utf-8"))
        cached_time = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        if (datetime.utcnow() - cached_time).days < CACHE_EXPIRY_DAYS:
            return data.get("payload")
    return None


def set_cache(key, payload):
    """Write to cache."""
    cache_file = CACHE_DIR / f"{hashlib.md5(key.encode()).hexdigest()}.json"
    cache_file.write_text(json.dumps({
        "_cached_at": datetime.utcnow().isoformat(),
        "_key": key,
        "payload": payload,
    }, ensure_ascii=False), encoding="utf-8")


def keyword_in_text(text, kw):
    kw_l = kw.lower()
    if kw in SHORT_KEYWORDS or len(kw_l) <= 4:
        return re.search(rf"\\b{re.escape(kw_l)}\\b", text) is not None
    return kw_l in text


def compute_tags(title, abstract):
    """Extract matched keywords as tags (no scoring)."""
    text = (title + " " + abstract).lower()
    matched_tags = []
    for keyword in TAG_KEYWORDS:
        if keyword_in_text(text, keyword):
            matched_tags.append(keyword)
    return list(dict.fromkeys(matched_tags))


def normalize_title(title):
    """Normalize title for deduplication."""
    return re.sub(r"[^a-z0-9]", "", title.lower())


# ============================================================
# Data Sources
# ============================================================

def fetch_arxiv(keywords, max_per_query=25):
    """Fetch from arXiv API."""
    print("\n📚 [arXiv] Fetching...")
    papers = []
    seen = set()

    for kw in keywords:
        cache_key = f"arxiv:{kw}:{datetime.utcnow().strftime('%Y-%m-%d')}"
        cached = get_cache(cache_key)
        if cached:
            print(f"  ✓ '{kw}' (cached, {len(cached)} papers)")
            papers.extend(cached)
            continue

        # Only fetch papers from the last 2 years
        date_from = (datetime.utcnow() - timedelta(days=730)).strftime("%Y%m%d") + "000000"
        query = urllib.parse.quote(f'all:"{kw}" AND submittedDate:[{date_from} TO 99991231235959]')
        url = (
            f"http://export.arxiv.org/api/query?search_query={query}"
            f"&start=0&max_results={max_per_query}"
            f"&sortBy=submittedDate&sortOrder=descending"
        )

        data = safe_request(url)
        if not data:
            continue

        ns = {"a": "http://www.w3.org/2005/Atom"}
        try:
            root = ET.fromstring(data)
        except ET.ParseError:
            continue

        batch = []
        for entry in root.findall("a:entry", ns):
            arxiv_id_raw = entry.find("a:id", ns).text.strip()
            arxiv_id = arxiv_id_raw.split("/abs/")[-1]

            if arxiv_id in seen:
                continue
            seen.add(arxiv_id)

            title = re.sub(r"\s+", " ", entry.find("a:title", ns).text.strip())
            abstract = re.sub(r"\s+", " ", entry.find("a:summary", ns).text.strip())
            authors = [a.find("a:name", ns).text for a in entry.findall("a:author", ns)]
            published = entry.find("a:published", ns).text[:10]
            categories = [c.get("term") for c in entry.findall("a:category", ns)]

            pdf_link = ""
            for link in entry.findall("a:link", ns):
                if link.get("title") == "pdf":
                    pdf_link = link.get("href", "")

            tags = compute_tags(title, abstract)

            batch.append({
                "id": f"arxiv:{arxiv_id}",
                "title": title,
                "abstract": abstract[:600],
                "authors": authors[:5],
                "date": published,
                "source": "arXiv",
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "pdf": pdf_link,
                "categories": categories[:5],
                "relevance_score": 0,
                "tags": tags,
            })

        set_cache(cache_key, batch)
        papers.extend(batch)
        print(f"  ✓ '{kw}': {len(batch)} papers")
        time.sleep(3)  # arXiv rate limit: be polite

    return papers


def fetch_semantic_scholar(keywords, max_per_query=20):
    """Fetch from Semantic Scholar API."""
    print("\n🔬 [Semantic Scholar] Fetching...")
    papers = []
    seen = set()

    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    fields = "title,abstract,authors,year,url,externalIds,publicationDate,venue,citationCount"

    for kw in keywords:
        cache_key = f"s2:{kw}:{datetime.utcnow().strftime('%Y-%m-%d')}"
        cached = get_cache(cache_key)
        if cached:
            print(f"  ✓ '{kw}' (cached, {len(cached)} papers)")
            papers.extend(cached)
            continue

        params = urllib.parse.urlencode({
            "query": kw,
            "limit": max_per_query,
            "fields": fields,
            "sort": "publicationDate:desc",
        })
        url = f"{base_url}?{params}"

        data = safe_request(url, headers={"Accept": "application/json"}, delay=5)
        if not data:
            time.sleep(5)
            continue

        try:
            result = json.loads(data)
        except json.JSONDecodeError:
            continue

        batch = []
        for p in result.get("data", []):
            pid = p.get("paperId", "")
            if pid in seen or not pid:
                continue
            seen.add(pid)

            title = p.get("title", "")
            abstract = p.get("abstract") or ""
            authors = [a.get("name", "") for a in (p.get("authors") or [])[:5]]
            pub_date = p.get("publicationDate") or str(p.get("year", ""))
            venue = p.get("venue") or ""
            citations = p.get("citationCount") or 0
            ext = p.get("externalIds") or {}

            tags = compute_tags(title, abstract)

            batch.append({
                "id": f"s2:{pid[:20]}",
                "title": title,
                "abstract": abstract[:600],
                "authors": authors,
                "date": pub_date[:10] if pub_date else "",
                "source": "Semantic Scholar",
                "url": p.get("url", f"https://www.semanticscholar.org/paper/{pid}"),
                "pdf": f"https://arxiv.org/pdf/{ext.get('ArXiv', '')}" if ext.get("ArXiv") else "",
                "venue": venue,
                "citations": citations,
                "doi": ext.get("DOI", ""),
                "relevance_score": 0,
                "tags": tags,
            })

        set_cache(cache_key, batch)
        papers.extend(batch)
        print(f"  ✓ '{kw}': {len(batch)} papers")
        time.sleep(5)  # S2 rate limit: 1 req per 5s without API key

    return papers


def fetch_openreview(venues=None, max_per_venue=30):
    """Fetch from OpenReview API (ICLR, NeurIPS, ICML submissions)."""
    print("\n📝 [OpenReview] Fetching...")

    if venues is None:
        venues = [
            "ICLR.cc/2026/Conference",
            "ICLR.cc/2025/Conference",
            "NeurIPS.cc/2025/Conference",
            "ICML.cc/2025/Conference",
        ]

    papers = []
    seen = set()

    for venue in venues:
        cache_key = f"openreview:{venue}:{datetime.utcnow().strftime('%Y-%m-%d')}"
        cached = get_cache(cache_key)
        if cached:
            print(f"  ✓ '{venue}' (cached, {len(cached)} papers)")
            papers.extend(cached)
            continue

        # Search for relevant papers in the venue
        search_terms = ["remaining useful life", "knowledge distillation",
                        "predictive maintenance", "time series", "prognostics"]
        batch = []

        for term in search_terms:
            invitation = f"{venue}/-/Submission"
            params = urllib.parse.urlencode({
                "term": term,
                "invitation": invitation,
                "limit": 10,
                "sort": "cdate:desc",
            })
            url = f"https://api2.openreview.net/notes/search?{params}"

            data = safe_request(url, delay=5)
            if not data:
                continue

            try:
                result = json.loads(data)
            except json.JSONDecodeError:
                continue

            for note in result.get("notes", []):
                note_id = note.get("id", "")
                if note_id in seen:
                    continue
                seen.add(note_id)

                content = note.get("content", {})

                # Handle OpenReview v2 format (value inside dict)
                def get_field(field_name):
                    val = content.get(field_name, "")
                    if isinstance(val, dict):
                        return val.get("value", "")
                    return val or ""

                title = get_field("title")
                abstract = get_field("abstract")
                authors_raw = content.get("authors", [])
                if isinstance(authors_raw, dict):
                    authors_raw = authors_raw.get("value", [])
                authors = authors_raw[:5] if isinstance(authors_raw, list) else []

                cdate = note.get("cdate", 0)
                if cdate:
                    date_str = datetime.utcfromtimestamp(cdate / 1000).strftime("%Y-%m-%d")
                else:
                    date_str = ""

                tags = compute_tags(title, abstract)

                batch.append({
                    "id": f"or:{note_id}",
                    "title": title,
                    "abstract": abstract[:600],
                    "authors": authors,
                    "date": date_str,
                    "source": f"OpenReview ({venue.split('/')[0]})",
                    "url": f"https://openreview.net/forum?id={note_id}",
                    "pdf": f"https://openreview.net/pdf?id={note_id}",
                    "venue": venue.split("/")[0],
                    "relevance_score": 0,
                    "tags": tags,
                })

            time.sleep(3)  # OpenReview rate limit

        set_cache(cache_key, batch)
        papers.extend(batch)
        print(f"  ✓ '{venue}': {len(batch)} papers")

    return papers


def fetch_huggingface_daily():
    """Fetch HuggingFace Daily Papers."""
    print("\n🤗 [HuggingFace Daily] Fetching...")

    cache_key = f"hf_daily:{datetime.utcnow().strftime('%Y-%m-%d')}"
    cached = get_cache(cache_key)
    if cached:
        print(f"  ✓ (cached, {len(cached)} papers)")
        return cached

    url = "https://huggingface.co/api/daily_papers"
    data = safe_request(url)
    if not data:
        return []

    try:
        items = json.loads(data)
    except json.JSONDecodeError:
        return []

    papers = []
    for item in items[:30]:
        paper = item.get("paper", {})
        title = paper.get("title", "")
        abstract = paper.get("summary", "") or ""
        authors = []
        for a in (paper.get("authors", []) or [])[:5]:
            name = a.get("name", "") or ""
            if not name:
                user = a.get("user", {}) or {}
                name = user.get("fullname", "") or user.get("name", "")
            if name:
                authors.append(name)

        pub_date = paper.get("publishedAt", "")[:10]
        arxiv_id = paper.get("id", "")
        upvotes = paper.get("upvotes", 0) or item.get("numUpvotes", 0)

        tags = compute_tags(title, abstract)

        papers.append({
            "id": f"hf:{arxiv_id}",
            "title": title,
            "abstract": abstract[:600],
            "authors": authors,
            "date": pub_date,
            "source": "HuggingFace Daily",
            "url": f"https://huggingface.co/papers/{arxiv_id}" if arxiv_id else "",
            "pdf": f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else "",
            "upvotes": upvotes,
            "relevance_score": 0,
            "tags": tags,
            "is_ai_frontier": True,
        })

    set_cache(cache_key, papers)
    print(f"  ✓ {len(papers)} daily papers")
    return papers


def fetch_rss_feeds():
    """Fetch AI blog/news RSS feeds."""
    print("\n📡 [RSS] Fetching blog feeds...")
    items = []

    for feed_info in RSS_FEEDS:
        cache_key = f"rss:{feed_info['name']}:{datetime.utcnow().strftime('%Y-%m-%d')}"
        cached = get_cache(cache_key)
        if cached:
            print(f"  ✓ {feed_info['name']} (cached, {len(cached)} items)")
            items.extend(cached)
            continue

        data = safe_request(feed_info["url"])
        if not data:
            print(f"  ✗ {feed_info['name']}: failed to fetch")
            continue

        batch = []
        try:
            root = ET.fromstring(data)
            # Try RSS 2.0 format
            for item in root.findall(".//item")[:10]:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                desc = (item.findtext("description") or "").strip()
                # Strip HTML tags from description
                desc = re.sub(r"<[^>]+>", "", desc)
                pub_date = (item.findtext("pubDate") or "").strip()

                # Parse date
                date_str = ""
                if pub_date:
                    for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"]:
                        try:
                            date_str = datetime.strptime(pub_date.strip(), fmt).strftime("%Y-%m-%d")
                            break
                        except ValueError:
                            continue

                batch.append({
                    "id": f"rss:{hashlib.md5(link.encode()).hexdigest()[:12]}",
                    "title": title,
                    "abstract": desc[:400],
                    "authors": [feed_info["name"]],
                    "date": date_str,
                    "source": feed_info["name"],
                    "url": link,
                    "pdf": "",
                    "relevance_score": 0,
                    "tags": [],
                    "is_ai_frontier": True,
                    "is_blog": True,
                })

            # Try Atom format if no items found
            if not batch:
                ns = {"a": "http://www.w3.org/2005/Atom"}
                for entry in root.findall("a:entry", ns)[:10]:
                    title = (entry.findtext("a:title", namespaces=ns) or "").strip()
                    link_el = entry.find("a:link", ns)
                    link = link_el.get("href", "") if link_el is not None else ""
                    summary = (entry.findtext("a:summary", namespaces=ns) or
                               entry.findtext("a:content", namespaces=ns) or "").strip()
                    summary = re.sub(r"<[^>]+>", "", summary)
                    updated = (entry.findtext("a:updated", namespaces=ns) or "")[:10]

                    batch.append({
                        "id": f"rss:{hashlib.md5(link.encode()).hexdigest()[:12]}",
                        "title": title,
                        "abstract": summary[:400],
                        "authors": [feed_info["name"]],
                        "date": updated,
                        "source": feed_info["name"],
                        "url": link,
                        "pdf": "",
                        "relevance_score": 0,
                        "tags": [],
                        "is_ai_frontier": True,
                        "is_blog": True,
                    })

        except ET.ParseError:
            print(f"  ✗ {feed_info['name']}: XML parse error")
            continue

        set_cache(cache_key, batch)
        items.extend(batch)
        print(f"  ✓ {feed_info['name']}: {len(batch)} items")

    return items


def fetch_paperswithcode(max_per_term=10):
    """Fetch papers from Papers with Code API (no key required)."""
    print("\n📊 [Papers with Code] Fetching...")

    cache_key = f"pwc:{datetime.utcnow().strftime('%Y-%m-%d')}"
    cached = get_cache(cache_key)
    if cached:
        print(f"  ✓ (cached, {len(cached)} papers)")
        return cached

    search_terms = [
        "remaining-useful-life",
        "fault-diagnosis",
        "predictive-maintenance",
        "time-series-anomaly-detection",
        "knowledge-distillation",
        "condition-monitoring",
        "health-index",
        "bearing-fault-diagnosis",
        "domain-adaptation",
        "self-supervised-learning",
        "contrastive-learning",
    ]

    papers = []
    seen = set()

    for term in search_terms:
        url = (
            f"https://paperswithcode.com/api/v1/papers/"
            f"?q={term}&ordering=-published&page_size={max_per_term}"
        )
        data = safe_request(url, headers={"Accept": "application/json"}, delay=3)
        if not data:
            print(f"  ✗ '{term}': failed")
            continue

        try:
            result = json.loads(data)
        except json.JSONDecodeError:
            continue

        batch = []
        for p in result.get("results", []):
            pid = str(p.get("id", ""))
            if pid in seen or not pid:
                continue
            seen.add(pid)

            title = p.get("title", "")
            abstract = p.get("abstract", "") or ""
            pub_date = (p.get("published", "") or "")[:10]
            url_abs = p.get("url_abs", "") or ""
            url_pdf = p.get("url_pdf", "") or ""

            tags = compute_tags(title, abstract)

            batch.append({
                "id": f"pwc:{pid}",
                "title": title,
                "abstract": abstract[:600],
                "authors": [],
                "date": pub_date,
                "source": "Papers with Code",
                "url": f"https://paperswithcode.com{url_abs}" if url_abs.startswith("/") else url_abs,
                "pdf": url_pdf,
                "relevance_score": 0,
                "tags": tags,
            })

        papers.extend(batch)
        print(f"  ✓ '{term}': {len(batch)} papers")
        time.sleep(3)

    set_cache(cache_key, papers)
    return papers


def fetch_crossref(max_per_kw=15):
    """Fetch papers from CrossRef API (free, no key). Covers Elsevier/IEEE/Springer/Nature."""
    print("\n📗 [CrossRef] Fetching...")

    cache_key = f"crossref:{datetime.utcnow().strftime('%Y-%m-%d')}"
    cached = get_cache(cache_key)
    if cached:
        print(f"  ✓ (cached, {len(cached)} papers)")
        return cached

    two_years_ago = (datetime.utcnow() - timedelta(days=730)).strftime("%Y-%m-%d")
    # Focus on highest-signal RUL/PHM keywords to avoid noise
    target_kws = [
        "remaining useful life",
        "bearing fault diagnosis",
        "predictive maintenance deep learning",
        "prognostics health management",
        "degradation prediction neural network",
        "condition monitoring fault",
    ]

    papers = []
    seen = set()

    for kw in target_kws:
        query = urllib.parse.quote(kw)
        url = (
            f"https://api.crossref.org/works?"
            f"query.bibliographic={query}"
            f"&filter=from-pub-date:{two_years_ago}"
            f"&sort=published&order=desc"
            f"&rows={max_per_kw}"
            f"&select=DOI,title,author,published,abstract,URL,container-title,type"
        )
        headers = {"User-Agent": "PaperRadar/1.0 (academic research tool)"}
        data = safe_request(url, headers=headers, delay=2)
        if not data:
            print(f"  ✗ '{kw}': failed")
            continue

        try:
            result = json.loads(data)
        except json.JSONDecodeError:
            continue

        batch = []
        for item in result.get("message", {}).get("items", []):
            doi = item.get("DOI", "")
            if not doi or doi in seen:
                continue
            seen.add(doi)

            title_parts = item.get("title", [])
            title = title_parts[0] if title_parts else ""
            if not title:
                continue

            authors = []
            for a in item.get("author", [])[:5]:
                name = f"{a.get('given', '')} {a.get('family', '')}".strip()
                if name:
                    authors.append(name)

            pub = item.get("published", {})
            date_parts = pub.get("date-parts", [[]])[0]
            if len(date_parts) >= 3:
                pub_date = f"{date_parts[0]:04d}-{date_parts[1]:02d}-{date_parts[2]:02d}"
            elif len(date_parts) >= 2:
                pub_date = f"{date_parts[0]:04d}-{date_parts[1]:02d}-01"
            elif len(date_parts) == 1:
                pub_date = f"{date_parts[0]:04d}-01-01"
            else:
                pub_date = ""

            abstract = re.sub(r"<[^>]+>", "", item.get("abstract", "") or "")[:600]
            venue_parts = item.get("container-title", [])
            venue = venue_parts[0] if venue_parts else ""
            url_link = item.get("URL", "") or f"https://doi.org/{doi}"

            tags = compute_tags(title, abstract)
            if not tags:
                continue

            batch.append({
                "id": f"doi:{doi}",
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "date": pub_date,
                "source": "CrossRef",
                "url": url_link,
                "pdf": "",
                "relevance_score": 0,
                "tags": tags,
                "venue": venue,
            })

        papers.extend(batch)
        print(f"  ✓ '{kw}': {len(batch)} papers")
        time.sleep(2)

    set_cache(cache_key, papers)
    print(f"  Total: {len(papers)} papers")
    return papers


def _decode_openalex_abstract(inv_idx):
    if not inv_idx:
        return ""
    try:
        max_pos = max(pos for positions in inv_idx.values() for pos in positions)
    except ValueError:
        return ""
    tokens = [""] * (max_pos + 1)
    for word, positions in inv_idx.items():
        for pos in positions:
            if 0 <= pos < len(tokens):
                tokens[pos] = word
    return " ".join(t for t in tokens if t)


def fetch_openalex(keywords, max_per_kw=15):
    """Fetch papers from OpenAlex API (no key required)."""
    print("\n[OpenAlex] Fetching...")
    papers = []
    seen = set()

    base_url = "https://api.openalex.org/works"
    for kw in keywords:
        cache_key = f"openalex:{kw}:{datetime.utcnow().strftime('%Y-%m-%d')}"
        cached = get_cache(cache_key)
        if cached:
            print(f"  ✓ '{kw}' (cached, {len(cached)} papers)")
            papers.extend(cached)
            continue

        params = urllib.parse.urlencode({
            "search": kw,
            "sort": "publication_date:desc",
        })
        url = f"{base_url}?{params}"
        data = safe_request(url, headers={"Accept": "application/json"}, delay=2)
        if not data:
            continue

        try:
            result = json.loads(data)
        except json.JSONDecodeError:
            continue

        batch = []
        for item in (result.get("results") or [])[:max_per_kw]:
            pid = item.get("id", "")
            if not pid or pid in seen:
                continue
            seen.add(pid)

            title = item.get("title", "") or ""
            abstract = _decode_openalex_abstract(item.get("abstract_inverted_index"))
            pub_date = (item.get("publication_date") or "")[:10]
            authors = []
            for a in (item.get("authorships") or [])[:5]:
                name = (a.get("author") or {}).get("display_name", "")
                if name:
                    authors.append(name)
            venue = (item.get("host_venue") or {}).get("display_name", "") or ""
            url_link = (item.get("primary_location") or {}).get("landing_page_url", "") or item.get("doi", "") or pid

            tags = compute_tags(title, abstract)

            batch.append({
                "id": f"openalex:{pid.split('/')[-1]}",
                "title": title,
                "abstract": abstract[:600],
                "authors": authors,
                "date": pub_date,
                "source": "OpenAlex",
                "url": url_link,
                "pdf": "",
                "relevance_score": 0,
                "tags": tags,
                "venue": venue,
                "doi": item.get("doi", ""),
            })

        set_cache(cache_key, batch)
        papers.extend(batch)
        print(f"  ✓ '{kw}': {len(batch)} papers")
        time.sleep(2)

    return papers


def fetch_arxiv_rss(categories=None):
    """Fetch today's new arXiv submissions via RSS and filter by research keywords."""
    if categories is None:
        categories = ["cs.LG", "cs.AI", "eess.SP"]

    print(f"\n📡 [arXiv RSS] Daily new: {', '.join(categories)}")

    cache_key = f"arxiv_rss:{datetime.utcnow().strftime('%Y-%m-%d')}"
    cached = get_cache(cache_key)
    if cached:
        print(f"  ✓ (cached, {len(cached)} papers)")
        return cached

    papers = []
    seen = set()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    ns = {"dc": "http://purl.org/dc/elements/1.1/"}

    for cat in categories:
        url = f"http://arxiv.org/rss/{cat}"
        data = safe_request(url, delay=3)
        if not data:
            print(f"  ✗ {cat}: failed")
            continue

        try:
            root = ET.fromstring(data)
        except ET.ParseError:
            print(f"  ✗ {cat}: XML parse error")
            continue

        channel = root.find("channel")
        if channel is None:
            continue

        cat_count = 0
        for item in channel.findall("item"):
            title_el = item.find("title")
            link_el = item.find("link")
            desc_el = item.find("description")

            title = (title_el.text or "").strip() if title_el is not None else ""
            link = (link_el.text or "").strip() if link_el is not None else ""
            desc = re.sub(r"<[^>]+>", "", desc_el.text or "") if desc_el is not None else ""

            if not title or not link:
                continue

            arxiv_id = link.split("/abs/")[-1] if "/abs/" in link else link.split("/")[-1]
            pid = f"arxiv:{arxiv_id}"
            if pid in seen:
                continue
            seen.add(pid)

            tags = compute_tags(title, desc)
            if not tags:
                continue

            authors = [c.text.strip() for c in item.findall("dc:creator", ns) if c.text]

            papers.append({
                "id": pid,
                "title": title,
                "abstract": desc.strip()[:600],
                "authors": authors[:5],
                "date": today,
                "source": "arXiv",
                "url": link,
                "pdf": link.replace("/abs/", "/pdf/") + ".pdf",
                "relevance_score": 0,
                "tags": tags,
            })
            cat_count += 1

        print(f"  ✓ {cat}: {cat_count} relevant papers")

    set_cache(cache_key, papers)
    return papers


# ============================================================
# Main Pipeline
# ============================================================

def deduplicate(papers):
    """Remove duplicates by normalized title."""
    seen = {}
    unique = []
    for p in papers:
        norm = normalize_title(p["title"])
        if not norm:
            continue
        if norm in seen:
            existing = seen[norm]
            date_new = p.get("date", "") or ""
            date_old = existing.get("date", "") or ""
            if date_new and (not date_old or date_new > date_old):
                unique.remove(existing)
                unique.append(p)
                seen[norm] = p
            elif (p.get("pdf") and not existing.get("pdf")):
                unique.remove(existing)
                unique.append(p)
                seen[norm] = p
        else:
            seen[norm] = p
            unique.append(p)
    return unique


def main():
    print("=" * 60)
    print(f"🛰️  Paper Radar — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    today = datetime.utcnow().strftime("%Y-%m-%d")

    # 1. Fetch from all sources
    arxiv_research = fetch_arxiv(RESEARCH_KEYWORDS, max_per_query=20)
    arxiv_ai = fetch_arxiv(AI_FRONTIER_KEYWORDS, max_per_query=10)
    for p in arxiv_ai:
        p["is_ai_frontier"] = True

    arxiv_rss = fetch_arxiv_rss(["cs.LG", "cs.AI", "eess.SP", "eess.SY", "stat.ML", "cs.RO"])
    crossref_papers = fetch_crossref()
    s2_papers = fetch_semantic_scholar(RESEARCH_KEYWORDS[:10], max_per_query=15)
    openalex_papers = fetch_openalex(RESEARCH_KEYWORDS[:10], max_per_kw=15)
    or_papers = fetch_openreview()
    hf_papers = fetch_huggingface_daily()
    rss_items = fetch_rss_feeds()
    pwc_papers = fetch_paperswithcode()

    # 2. Combine and deduplicate
    all_papers = (arxiv_research + arxiv_ai + arxiv_rss + crossref_papers
                  + s2_papers + openalex_papers + or_papers + hf_papers + rss_items + pwc_papers)
    all_papers = deduplicate(all_papers)

    # 3. Classify — sort by date descending (newest first)
    research_papers = sorted(
        [p for p in all_papers if not p.get("is_ai_frontier")],
        key=lambda x: x.get("date", ""),
        reverse=True,
    )
    ai_frontier = sorted(
        [p for p in all_papers if p.get("is_ai_frontier")],
        key=lambda x: (x.get("date", ""), x.get("upvotes", 0)),
        reverse=True,
    )

    # 4. Build daily data file
    daily_data = {
        "date": today,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "stats": {
            "total": len(all_papers),
            "research": len(research_papers),
            "ai_frontier": len(ai_frontier),
            "sources": {
                "arxiv": len([p for p in all_papers if p["source"] == "arXiv"]),
                "crossref": len([p for p in all_papers if p["source"] == "CrossRef"]),
                "semantic_scholar": len([p for p in all_papers if p["source"] == "Semantic Scholar"]),
                "openalex": len([p for p in all_papers if p["source"] == "OpenAlex"]),
                "openreview": len([p for p in all_papers if "OpenReview" in p["source"]]),
                "huggingface": len([p for p in all_papers if p["source"] == "HuggingFace Daily"]),
                "paperswithcode": len([p for p in all_papers if p["source"] == "Papers with Code"]),
                "rss": len([p for p in all_papers if p.get("is_blog")]),
            },
        },
        "research_papers": research_papers,
        "ai_frontier": ai_frontier,
    }

    # Save daily file
    daily_file = DATA_DIR / f"papers_{today}.json"
    daily_file.write_text(json.dumps(daily_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n💾 Saved daily data → {daily_file.name}")

    # Also save as latest.json for easy access
    latest_file = DATA_DIR / "latest.json"
    latest_file.write_text(json.dumps(daily_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # 5. Update index.json (list of all available dates)
    index_file = DATA_DIR / "index.json"
    if index_file.exists():
        index = json.loads(index_file.read_text("utf-8"))
    else:
        index = {"dates": [], "total_papers_tracked": 0}

    if today not in index["dates"]:
        index["dates"].insert(0, today)
    index["dates"] = index["dates"][:90]  # Keep 90 days
    index["last_updated"] = datetime.utcnow().isoformat() + "Z"
    index["total_papers_tracked"] = index.get("total_papers_tracked", 0) + len(all_papers)

    index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    # Print summary
    print(f"\n{'='*60}")
    print(f"✅ Summary for {today}")
    print(f"   Total papers:    {len(all_papers)}")
    print(f"   Research:        {len(research_papers)}")
    print(f"   AI Frontier:     {len(ai_frontier)}")
    print(f"   Sources: arXiv={daily_data['stats']['sources']['arxiv']}"
          f"  S2={daily_data['stats']['sources']['semantic_scholar']}"
          f"  OA={daily_data['stats']['sources']['openalex']}"
          f"  OR={daily_data['stats']['sources']['openreview']}"
          f"  HF={daily_data['stats']['sources']['huggingface']}"
          f"  PwC={daily_data['stats']['sources']['paperswithcode']}"
          f"  RSS={daily_data['stats']['sources']['rss']}")
    print(f"{'='*60}")

    return daily_data


if __name__ == "__main__":
    main()
