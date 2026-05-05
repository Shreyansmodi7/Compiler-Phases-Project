import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app import app  # noqa: E402


SAMPLE_CODE = """#include <stdio.h>
int main() {
    int i = 1;
    int total = 0;
    while(i <= 3) {
        total = total + i;
        i++;
    }
    printf("Total = %d\\n", total);
    return 0;
}
"""


class CompilerApiTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def post_source(self, endpoint, source_code=SAMPLE_CODE):
        return self.client.post(endpoint, json={"source_code": source_code})

    def test_health_endpoint(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_tokenize_valid_c_program(self):
        response = self.post_source("/tokenize")
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(data["error"])
        self.assertGreater(data["total"], 0)
        self.assertIn("KEYWORD", data["summary"])
        self.assertIn("IDENTIFIER", data["summary"])

    def test_tokenize_reports_invalid_characters(self):
        response = self.post_source("/tokenize", "int main() { int x = 5 @ 2; }")
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(data["error"])
        self.assertEqual(data["errors"][0]["character"], "@")

    def test_tokenize_recognizes_float_literals(self):
        response = self.post_source("/tokenize", "float price = 12.50;")
        tokens = response.get_json()["tokens"]

        self.assertIn({"type": "FLOAT", "value": "12.50", "line": 1, "col": 15}, tokens)

    def test_icdg_generates_tac_and_tables(self):
        code = """int main() {
    int n = 3;
    for(i = 1; i <= n; i++) {
        printf("%d", i);
    }
    return 0;
}
"""
        response = self.post_source("/icdg", code)
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(data["error"])
        self.assertIn("goto", data["tac"])
        self.assertGreater(data["instruction_count"], 0)
        self.assertGreater(len(data["quadruples"]), 0)
        self.assertGreater(len(data["triples"]), 0)
        self.assertGreater(len(data["indirect_triples"]), 0)

    def test_optimize_removes_duplicate_adjacent_instructions(self):
        code = """int main() {
    int x = 1;
    int x = 1;
    return 0;
}
"""
        response = self.post_source("/optimize", code)
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(data["error"])
        self.assertGreaterEqual(data["removed"], 1)
        self.assertLess(data["optimized_count"], data["original_count"])

    def test_codegen_generates_assembly(self):
        response = self.post_source("/codegen", SAMPLE_CODE)
        data = response.get_json()
        assembly = "\n".join(row["Code"] for row in data["assembly"])

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(data["error"])
        self.assertIn("PUSH RBP", assembly)
        self.assertIn("CALL printf", assembly)
        self.assertIn("RET", assembly)

    def test_empty_source_returns_bad_request(self):
        response = self.post_source("/tokenize", "")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "No code")


if __name__ == "__main__":
    unittest.main()
