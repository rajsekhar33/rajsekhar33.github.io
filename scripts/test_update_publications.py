"""Offline tests: run python3 -m unittest discover -s scripts -p 'test_*.py'."""
import copy
import unittest
from unittest.mock import patch

import update_publications as publications


class PublicationSyncTests(unittest.TestCase):
    def setUp(self):
        self.manual = publications.load_manual_publications()[0]
        self.preprint = {
            "bibcode": "2026arXiv260929782M",
            "title": ["Indexed preprint title"],
            "author": ["Mohapatra, Rajsekhar"],
            "year": "2026",
            "pubdate": "2026-09-24",
            "doctype": "eprint",
            "bibstem": ["arXiv"],
            "identifier": ["arXiv:2609.29782v2"],
        }
        # Synthetic journal metadata tests behaviour, not this paper's status.
        self.published = dict(
            self.preprint,
            bibcode="TEST-JOURNAL-BIBCODE",
            doctype="article",
            bibstem=["MNRAS"],
            title=["Published title"],
            identifier=["arXiv:2609.29782"],
        )

    def test_manual_preprint_renders_without_a_bibcode(self):
        rendered = publications.render_entry(self.manual)
        self.assertIn('href="https://arxiv.org/abs/2609.29782"', rendered)
        self.assertIn("arXiv preprint (submitted), 2026", rendered)
        self.assertIn("Mohapatra R, Lancaster L, Fielding D, Quataert E, Bryan GL", rendered)
        self.assertIn("2609.29782", publications.doc_keys(self.manual))

    def test_indexed_preprint_replaces_manual_without_losing_submitted_label(self):
        merged = publications.merge_publications([self.preprint], [self.manual])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["title"], self.preprint["title"])
        self.assertIn("(submitted)", publications.render_entry(merged[0]))
        self.assertIn("ui.adsabs.harvard.edu", publications.publication_link(merged[0]))

    def test_publication_wins_in_either_input_order(self):
        for records in ([self.preprint, self.published], [self.published, self.preprint]):
            with self.subTest(records=records):
                merged = publications.merge_publications(records, [self.manual])
                self.assertEqual(len(merged), 1)
                self.assertEqual(merged[0]["bibcode"], self.published["bibcode"])
                self.assertFalse(publications.is_preprint_doc(merged[0]))
                self.assertNotIn("submitted", publications.render_entry(merged[0]))
                index = publications.index_docs(merged)
                self.assertIs(index[self.preprint["bibcode"]], merged[0])
                self.assertIs(index["2609.29782"], merged[0])

    def test_library_duplicates_also_merge_without_a_manual_record(self):
        merged = publications.merge_publications([self.preprint, self.published], [])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["title"], self.published["title"])

    def test_versioned_urls_normalize_and_merge(self):
        indexed = dict(self.preprint, identifier=["https://arxiv.org/pdf/2609.29782v3.pdf"])
        merged = publications.merge_publications([indexed], [self.manual])
        self.assertEqual(len(merged), 1)

    def test_distinct_papers_remain_and_inputs_are_not_modified(self):
        before = copy.deepcopy(self.manual)
        other = dict(self.preprint, bibcode="OTHER-BIBCODE", identifier=["arXiv:2609.10000"])
        merged = publications.merge_publications([other], [self.manual])
        self.assertEqual(len(merged), 2)
        self.assertEqual(self.manual, before)

    def test_arxiv_link_fallback_without_url(self):
        doc = dict(self.manual)
        doc.pop("url")
        self.assertEqual(publications.publication_link(doc), "https://arxiv.org/abs/2609.29782")

    def test_main_merges_manual_entries_before_both_outputs(self):
        with patch.dict(publications.os.environ, {"ADS_API_TOKEN": "offline-test"}), \
             patch.object(publications, "fetch_library_bibcodes", return_value=["example"]), \
             patch.object(publications, "fetch_metadata", return_value=[self.preprint]), \
             patch.object(publications, "sync_publications_html") as sync_publications, \
             patch.object(publications, "sync_research_html") as sync_research:
            self.assertEqual(publications.main(), 0)
            docs = sync_publications.call_args.args[0]
            self.assertEqual(len(docs), 1)
            self.assertTrue(docs[0]["submitted"])
            sync_research.assert_called_once_with(docs)


if __name__ == "__main__":
    unittest.main()
