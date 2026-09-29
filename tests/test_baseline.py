import io
import json
import unittest
from unittest.mock import patch

from guarded_catalog import ExactCatalog, tokenize
from guarded_catalog.__main__ import dispatch, main


class CatalogTests(unittest.TestCase):
    def test_normalization_and_empty_singletons(self):
        catalog = ExactCatalog()
        catalog.put("b", "RED, Ball!", 1)
        catalog.put("a", "red ball", 2)
        catalog.put("c", "---")
        catalog.put("d", "")
        self.assertEqual(catalog.exact_plan(), {"groups": [
            {"representative": "b", "members": ["a", "b"]},
            {"representative": "c", "members": ["c"]},
            {"representative": "d", "members": ["d"]},
        ]})

    def test_token_order_and_repetition_matter(self):
        catalog = ExactCatalog()
        for key, text in [("a", "x y"), ("b", "y x"), ("c", "x x y")]:
            catalog.put(key, text)
        self.assertEqual(len(catalog.exact_plan()["groups"]), 3)
        self.assertEqual(tokenize("AéB _ C2\tD"), ["a", "b", "c2", "d"])

    def test_replacement_delete_and_absence(self):
        catalog = ExactCatalog()
        catalog.put("a", "old")
        catalog.put("a", "new", -5, True)
        self.assertEqual(catalog.snapshot(), [{"id": "a", "text": "new", "priority": -5, "protected": True}])
        self.assertTrue(catalog.delete("a"))
        self.assertFalse(catalog.delete("a"))
        self.assertEqual(catalog.snapshot(), [])

    def test_protected_is_metadata_in_original_api(self):
        catalog = ExactCatalog()
        catalog.put("a", "same", 10, True)
        catalog.put("b", "same", -10, True)
        self.assertEqual(catalog.exact_plan()["groups"], [{"representative": "b", "members": ["a", "b"]}])

    def test_rejections_preserve_state(self):
        catalog = ExactCatalog()
        catalog.put("a", "keep")
        before = catalog.snapshot()
        for args in [("a", "bad", True), ("a", "bad", 2**31), ("", "bad"),
                     ("a", "bad", 0, 1), ("a", "\ud800"), (1, "bad"), ("a", [])]:
            with self.assertRaises(ValueError):
                catalog.put(*args)
            self.assertEqual(catalog.snapshot(), before)
        with self.assertRaises(ValueError):
            catalog.delete("a!")
        self.assertEqual(catalog.snapshot(), before)

    def test_snapshot_and_plan_are_isolated(self):
        catalog = ExactCatalog()
        catalog.put("a", "x")
        catalog.snapshot()[0]["text"] = "mutated"
        catalog.exact_plan()["groups"][0]["members"].append("fake")
        self.assertEqual(catalog.snapshot()[0]["text"], "x")
        self.assertEqual(catalog.exact_plan()["groups"][0]["members"], ["a"])

    def test_dispatch_exact_keys(self):
        catalog = ExactCatalog()
        with self.assertRaises(ValueError):
            dispatch(catalog, {"op": "put", "id": "a", "text": "x"})
        with self.assertRaises(ValueError):
            dispatch(catalog, {"op": "snapshot", "extra": 1})
        self.assertEqual(catalog.snapshot(), [])

    def test_cli_preserves_state_after_error(self):
        commands = [
            {"op": "put", "id": "a", "text": "x", "priority": 0, "protected": False},
            {"op": "delete", "id": "a", "extra": 1},
            {"op": "snapshot"},
        ]
        data = "\n".join(json.dumps(command) for command in commands) + "\n"
        stdout = io.StringIO()
        with patch("sys.stdin", io.StringIO(data)), patch("sys.stdout", stdout):
            main()
        output = [json.loads(line) for line in stdout.getvalue().splitlines()]
        self.assertEqual([row["ok"] for row in output], [True, False, True])
        self.assertEqual(output[-1]["result"][0]["id"], "a")


if __name__ == "__main__":
    unittest.main()
