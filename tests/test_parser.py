"""Tests for safe arithmetic-expression parsing."""

import unittest

from arithmetic.expression import Binary, Number, format_expression
from arithmetic.parser import ExpressionSyntaxError, parse_expression


class ParserTests(unittest.TestCase):
    """Protect precedence, associativity, grouping, and input rejection."""

    def test_precedence_and_left_associativity(self):
        parsed = parse_expression("1 + 2 × 3 - 4")
        expected = Binary(
            "-",
            Binary("+", Number(1), Binary("×", Number(2), Number(3))),
            Number(4),
        )
        self.assertEqual(parsed, expected)

    def test_parentheses_override_precedence(self):
        parsed = parse_expression("(1 + 2) × 3")
        expected = Binary("×", Binary("+", Number(1), Number(2)), Number(3))
        self.assertEqual(parsed, expected)

    def test_parses_fraction_and_both_mixed_number_separators(self):
        ascii_tree = parse_expression("1'1/2 + 3/4")
        curly_tree = parse_expression("1’1/2 + 3/4")
        self.assertEqual(ascii_tree, curly_tree)
        self.assertEqual(ascii_tree, Binary("+", Number("3/2"), Number("3/4")))

    def test_format_parse_round_trip_preserves_tree(self):
        tree = Binary(
            "÷",
            Binary("+", Number(1), Number(2)),
            Binary("+", Number(3), Number(4)),
        )
        self.assertEqual(parse_expression(format_expression(tree)), tree)

    def test_rejects_trailing_incomplete_or_unsafe_input(self):
        invalid_inputs = (
            "",
            "1 +",
            "(1 + 2",
            "1 2",
            "1 + 2 trailing",
            "__import__('os')",
            "1 / 2",
        )
        for text in invalid_inputs:
            with self.subTest(text=text):
                with self.assertRaises(ExpressionSyntaxError):
                    parse_expression(text)


if __name__ == "__main__":
    unittest.main()
