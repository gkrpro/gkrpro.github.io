"""
Unit tests for the fetcher parsing logic.

These tests exercise the parsers without making real HTTP calls — they
verify the logic that turns API responses into FetchResult values. The
actual HTTP calls are tested in GitHub Actions where the network is open.

Run: python -m unittest test_fetchers.py
"""

import sys
import unittest
from pathlib import Path

# Make fetchers importable
sys.path.insert(0, str(Path(__file__).parent))

from fetchers.huggingface import _count_markers, CARD_MARKERS, TRAINING_DATA_MARKERS
from fetchers.cop import CoPSignatoryIndex, PROVIDER_TO_SIGNATORY
from fetchers import host_allowed


class TestAllowlist(unittest.TestCase):
    def test_allowed_domains(self):
        self.assertTrue(host_allowed("https://huggingface.co/api/models/foo"))
        self.assertTrue(host_allowed("https://api.github.com/repos/foo/bar"))
        self.assertTrue(host_allowed("https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai"))

    def test_blocked_domains(self):
        self.assertFalse(host_allowed("https://evil.example.com/"))
        self.assertFalse(host_allowed("http://malicious.site/"))
        self.assertFalse(host_allowed(""))
        self.assertFalse(host_allowed(None))

    def test_subdomain_handling(self):
        # Exact match
        self.assertTrue(host_allowed("https://huggingface.co/"))
        # Subdomain of allowed
        self.assertTrue(host_allowed("https://api.github.com/"))
        # Not allowed: similar-looking domains
        self.assertFalse(host_allowed("https://huggingface.co.fake.com/"))


class TestHuggingFaceMarkers(unittest.TestCase):
    def test_model_card_marker_count_substantive(self):
        text = """
        # Model Details
        ## Intended Use
        This model is intended for...
        ## Limitations
        Known limitations include...
        ## Evaluation
        We evaluated the model on...
        ## Training Data
        The model was trained on...
        """
        count = _count_markers(text, CARD_MARKERS)
        self.assertGreaterEqual(count, 5)

    def test_model_card_marker_count_stub(self):
        text = "# Just a model"
        count = _count_markers(text, CARD_MARKERS)
        self.assertEqual(count, 0)

    def test_training_data_detection(self):
        text = "## Training Data\nThe model was trained on the C4 dataset and Common Crawl."
        count = _count_markers(text, TRAINING_DATA_MARKERS)
        self.assertGreater(count, 0)

    def test_no_training_data(self):
        text = "This model is great. Use it carefully."
        count = _count_markers(text, TRAINING_DATA_MARKERS)
        self.assertEqual(count, 0)


class TestCoPParser(unittest.TestCase):
    def test_provider_map_contains_known_signatories(self):
        # Verified against the EU AI Office page as of 2026-05-30
        for known in ["Anthropic", "OpenAI", "Google", "Microsoft", "IBM", "Cohere", "Mistral AI"]:
            self.assertIn(known, PROVIDER_TO_SIGNATORY)
            self.assertIsNotNone(PROVIDER_TO_SIGNATORY[known], f"{known} should map to a canonical signatory")

    def test_provider_map_known_non_signatories(self):
        for non in ["Meta", "DeepSeek", "Alibaba", "xAI"]:
            self.assertIn(non, PROVIDER_TO_SIGNATORY)
            self.assertIsNone(PROVIDER_TO_SIGNATORY[non], f"{non} should map to None")

    def test_html_parse_finds_signatories(self):
        # Simulate a page snippet with multiple signatory names
        html = """
        <ul>
          <li>Accexible</li>
          <li>Anthropic</li>
          <li>Cohere</li>
          <li>Google</li>
          <li>IBM</li>
          <li>Microsoft</li>
          <li>Mistral AI</li>
          <li>OpenAI</li>
        </ul>
        """
        idx = CoPSignatoryIndex(http=None)
        parsed = idx._parse(html)
        self.assertIn("Anthropic", parsed)
        self.assertIn("OpenAI", parsed)
        self.assertIn("Mistral AI", parsed)
        self.assertNotIn("Meta", parsed)
        self.assertNotIn("DeepSeek", parsed)

    def test_html_parse_no_false_positives(self):
        html = "<p>This page has nothing about signatories</p>"
        idx = CoPSignatoryIndex(http=None)
        parsed = idx._parse(html)
        self.assertEqual(parsed, set())


if __name__ == "__main__":
    unittest.main(verbosity=2)
