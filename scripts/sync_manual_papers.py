#!/usr/bin/env python3
"""Merge the curated reading queue into the current Paper Radar snapshot.

This updates local data without re-fetching every remote source. The normal
daily fetch also loads the same manual_papers.json file.
"""

import json

from fetch_papers import (
    DATA_DIR,
    canonical_paper_id,
    deduplicate,
    filter_relevant_papers,
    load_manual_papers,
)


def main():
    latest_file = DATA_DIR / "latest.json"
    if not latest_file.exists():
        raise SystemExit("data/latest.json not found; run fetch_papers.py first")

    data = json.loads(latest_file.read_text("utf-8"))
    existing_research = data.get("research_papers", [])
    manual = load_manual_papers()
    research = filter_relevant_papers(manual + existing_research, min_score=6)
    research = deduplicate(research)

    for paper in research:
        paper["canonical_id"] = canonical_paper_id(paper)

    research.sort(
        key=lambda paper: (
            bool(paper.get("curated")),
            paper.get("added_date", ""),
            paper.get("date", ""),
            paper.get("relevance_score", 0),
        ),
        reverse=True,
    )
    data["research_papers"] = research
    data.setdefault("stats", {})["research"] = len(research)
    data["stats"]["total"] = len(research) + len(data.get("ai_frontier", []))
    data["stats"].setdefault("sources", {})["curated"] = sum(
        1 for paper in research if paper.get("curated")
    )
    latest_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Synced {len(manual)} curated papers into {latest_file}")


if __name__ == "__main__":
    main()
