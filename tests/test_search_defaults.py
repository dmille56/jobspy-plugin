import argparse
import unittest

from skills.jobspy import search


class SearchDefaultSitesTest(unittest.TestCase):
    def test_uses_default_sites_from_preferences_when_flag_omitted(self):
        args = argparse.Namespace(sites=None)
        prefs = {"default_sites": ["linkedin", "google"]}

        self.assertEqual(search.resolve_sites(args, prefs), ["linkedin", "google"])

    def test_explicit_sites_override_preferences(self):
        args = argparse.Namespace(sites="indeed,zip_recruiter")
        prefs = {"default_sites": ["linkedin", "google"]}

        self.assertEqual(search.resolve_sites(args, prefs), ["indeed", "zip_recruiter"])

    def test_builtin_default_sites_are_used_when_no_preferences_exist(self):
        args = argparse.Namespace(sites=None)

        self.assertEqual(search.resolve_sites(args, {}), search.BUILTIN_DEFAULT_SITES)


if __name__ == "__main__":
    unittest.main()
