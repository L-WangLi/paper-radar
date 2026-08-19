#!/usr/bin/env python3
"""
Unit tests for the scoring/classification/dedup/ID logic in scripts/fetch_papers.py.

These are the functions that decide which papers a user actually sees each day —
previously untested, so a keyword/weight tweak could silently change what gets
filtered in or out. Stdlib-only (unittest), matching the project's zero-dependency
philosophy.

Run with:
    python3 -m unittest tests.test_fetch_papers -v
or:
    python3 tests/test_fetch_papers.py
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import fetch_papers as fp  # noqa: E402


class ComputeScoreBreakdownTests(unittest.TestCase):
    def test_core_rul_paper_scores_high(self):
        breakdown = fp.compute_score_breakdown(
            title="Remaining Useful Life Prediction of Turbofan Engines via Transformer",
            abstract="We propose a method for RUL prediction on the C-MAPSS dataset.",
            tags=["remaining useful life", "C-MAPSS"],
            date="2026-08-01",
            source="arXiv",
        )
        self.assertGreaterEqual(breakdown["total"], 18)
        self.assertGreater(breakdown["topic"], 0)
        self.assertGreater(breakdown["dataset"], 0)

    def test_unrelated_medical_paper_is_penalized(self):
        breakdown = fp.compute_score_breakdown(
            title="Survival analysis of cancer patients after treatment",
            abstract="A study of mortality prediction and patient survival in oncology.",
            tags=[],
            date="2026-08-01",
            source="CrossRef",
        )
        self.assertEqual(breakdown["topic"], 0)
        self.assertTrue(breakdown["negative_hits"])
        self.assertEqual(breakdown["negative"], -18)

    def test_blank_paper_scores_zero(self):
        breakdown = fp.compute_score_breakdown(title="", abstract="", tags=[])
        self.assertEqual(breakdown["total"], 0)


class ClassifyResearchQuestionTests(unittest.TestCase):
    def test_high_topic_score_is_core_rul_phm(self):
        breakdown = {"topic": 20, "dataset": 0, "time_series": 0, "method": 0}
        self.assertEqual(fp.classify_research_question(breakdown, tags=[]), "core_rul_phm")

    def test_dataset_score_is_benchmark(self):
        breakdown = {"topic": 0, "dataset": 12, "time_series": 0, "method": 0}
        self.assertEqual(fp.classify_research_question(breakdown, tags=[]), "dataset_benchmark")

    def test_blog_is_always_related_news(self):
        breakdown = {"topic": 30, "dataset": 30, "time_series": 30, "method": 30}
        self.assertEqual(
            fp.classify_research_question(breakdown, tags=[], is_blog=True), "related_news"
        )

    def test_low_everything_is_related(self):
        breakdown = {"topic": 0, "dataset": 0, "time_series": 0, "method": 0}
        self.assertEqual(fp.classify_research_question(breakdown, tags=[]), "related")


class NormalizeDateTests(unittest.TestCase):
    def test_valid_date_passes_through(self):
        self.assertEqual(fp.normalize_date("2026-08-01"), "2026-08-01")

    def test_far_future_date_is_rejected(self):
        self.assertEqual(fp.normalize_date("2121-01-01"), "")

    def test_pre_1990_date_is_rejected(self):
        self.assertEqual(fp.normalize_date("1985-01-01"), "")

    def test_empty_input_is_rejected(self):
        self.assertEqual(fp.normalize_date(""), "")

    def test_garbage_input_is_rejected(self):
        self.assertEqual(fp.normalize_date("not-a-date"), "")


class CanonicalPaperIdTests(unittest.TestCase):
    def test_doi_takes_priority(self):
        paper = {"doi": "https://doi.org/10.1000/Test.DOI", "id": "arxiv:2401.00001"}
        self.assertEqual(fp.canonical_paper_id(paper), "doi:10.1000/test.doi")

    def test_arxiv_id_strips_version_suffix(self):
        paper = {"id": "arxiv:2401.12345v2"}
        self.assertEqual(fp.canonical_paper_id(paper), "arxiv:2401.12345")

    def test_arxiv_id_recovered_from_url_when_source_id_is_not_arxiv(self):
        paper = {"id": "s2:abc123", "url": "https://arxiv.org/abs/2401.12345v3"}
        self.assertEqual(fp.canonical_paper_id(paper), "arxiv:2401.12345")

    def test_falls_back_to_normalized_title(self):
        paper = {"id": "rss:deadbeef", "title": "Some Blog Post!"}
        self.assertEqual(fp.canonical_paper_id(paper), "title:someblogpost")


class DeduplicateTests(unittest.TestCase):
    def test_keeps_newer_dated_duplicate(self):
        older = {"title": "Same Paper Title", "date": "2026-01-01", "pdf": ""}
        newer = {"title": "Same Paper Title", "date": "2026-06-01", "pdf": ""}
        result = fp.deduplicate([older, newer])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["date"], "2026-06-01")

    def test_prefers_entry_with_pdf_when_dates_tie(self):
        no_pdf = {"title": "Same Paper Title", "date": "2026-01-01", "pdf": ""}
        with_pdf = {"title": "Same Paper Title", "date": "2026-01-01", "pdf": "https://x/y.pdf"}
        result = fp.deduplicate([no_pdf, with_pdf])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["pdf"], "https://x/y.pdf")

    def test_distinct_titles_are_both_kept(self):
        a = {"title": "Paper A", "date": "2026-01-01", "pdf": ""}
        b = {"title": "Paper B", "date": "2026-01-01", "pdf": ""}
        result = fp.deduplicate([a, b])
        self.assertEqual(len(result), 2)

    def test_blank_title_is_dropped(self):
        result = fp.deduplicate([{"title": "", "date": "2026-01-01", "pdf": ""}])
        self.assertEqual(result, [])

    def test_curated_duplicate_wins_and_absorbs_fetched_fields(self):
        fetched = {
            "title": "Same Paper Title", "date": "2026-06-01",
            "pdf": "https://x/y.pdf", "abstract": "auto-fetched abstract",
        }
        curated = {"title": "Same Paper Title", "date": "", "pdf": "", "curated": True}
        result = fp.deduplicate([fetched, curated])
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["curated"])
        # merged record keeps the richer field from the non-curated duplicate
        self.assertEqual(result[0]["abstract"], "auto-fetched abstract")

    def test_curated_entry_is_not_displaced_by_a_newer_fetched_duplicate(self):
        curated = {"title": "Same Paper Title", "date": "2026-01-01", "pdf": "", "curated": True}
        fetched = {"title": "Same Paper Title", "date": "2026-06-01", "pdf": "https://x/y.pdf"}
        result = fp.deduplicate([curated, fetched])
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["curated"])


class IsRelevantPaperTests(unittest.TestCase):
    def test_strong_rul_paper_is_relevant(self):
        paper = {
            "title": "A Transformer-Based Approach for Remaining Useful Life Prediction",
            "abstract": "We evaluate RUL prediction on the C-MAPSS turbofan degradation dataset.",
            "source": "arXiv",
            "date": "2026-08-01",
        }
        self.assertTrue(fp.is_relevant_paper(paper))

    def test_unrelated_paper_is_not_relevant(self):
        paper = {
            "title": "Deep Learning for Stock Market Prediction",
            "abstract": "We use LSTM to forecast stock prices on financial time series.",
            "source": "CrossRef",
            "date": "2026-08-01",
        }
        self.assertFalse(fp.is_relevant_paper(paper))


class RESEARCH_KEYWORDS_TierTests(unittest.TestCase):
    def test_tiers_combine_to_full_list_without_gaps(self):
        self.assertEqual(
            fp.RESEARCH_KEYWORDS, fp.RESEARCH_KEYWORDS_TIER1 + fp.RESEARCH_KEYWORDS_TIER2
        )
        self.assertEqual(len(fp.RESEARCH_KEYWORDS), len(set(fp.RESEARCH_KEYWORDS)))


if __name__ == "__main__":
    unittest.main()
