"""Tests for exact number parsing and display."""

import unittest
from fractions import Fraction

from arithmetic.numbers import NumberFormatError, format_number, parse_number


class NumberTests(unittest.TestCase):
    """Protect the external number syntax used by exercises and answers."""

    def test_parse_supported_number_forms(self):
        cases = {
            "0": Fraction(0),
            "3/5": Fraction(3, 5),
            "2'3/8": Fraction(19, 8),
            "2’3/8": Fraction(19, 8),
            "  7/24  ": Fraction(7, 24),
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(parse_number(text), expected)

    def test_parse_accepts_equivalent_improper_fraction(self):
        self.assertEqual(parse_number("19/8"), Fraction(19, 8))

    def test_format_reduces_and_uses_mixed_numbers(self):
        cases = {
            Fraction(8, 4): "2",
            Fraction(3, 5): "3/5",
            Fraction(19, 8): "2'3/8",
            Fraction(0): "0",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(format_number(value), expected)

    def test_rejects_invalid_number_text(self):
        for text in ("1/0", "1'3/2", "1'0/2", "", "abc", "-1"):
            with self.subTest(text=text):
                with self.assertRaises(NumberFormatError):
                    parse_number(text)

    def test_format_rejects_negative_values(self):
        with self.assertRaises(ValueError):
            format_number(Fraction(-1, 2))


if __name__ == "__main__":
    unittest.main()
