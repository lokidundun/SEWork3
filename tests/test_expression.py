"""Tests for expression-tree semantics and canonical duplicate keys."""

import unittest
from fractions import Fraction

from arithmetic.expression import (
    Binary,
    Number,
    canonical_key,
    constraints_hold,
    evaluate,
    format_expression,
    operator_count,
    walk,
)


class ExpressionTests(unittest.TestCase):
    """Protect exact evaluation, grouping, constraints, and deduplication."""

    def test_evaluate_all_operators_exactly(self):
        cases = (
            (Binary("+", Number(Fraction(1, 6)), Number(Fraction(1, 8))), Fraction(7, 24)),
            (Binary("-", Number(3), Number(Fraction(1, 2))), Fraction(5, 2)),
            (Binary("×", Number(Fraction(2, 3)), Number(Fraction(9, 4))), Fraction(3, 2)),
            (Binary("÷", Number(Fraction(3, 5)), Number(Fraction(9, 10))), Fraction(2, 3)),
        )
        for tree, expected in cases:
            with self.subTest(operator=tree.operator):
                self.assertEqual(evaluate(tree), expected)

    def test_division_by_zero_is_rejected(self):
        with self.assertRaises(ZeroDivisionError):
            evaluate(Binary("÷", Number(1), Number(0)))

    def test_operator_count_and_walk_cover_nested_tree(self):
        tree = Binary("×", Binary("+", Number(1), Number(2)), Number(3))
        self.assertEqual(operator_count(tree), 2)
        self.assertEqual(len(list(walk(tree))), 5)

    def test_format_preserves_precedence_and_right_grouping(self):
        cases = (
            (Binary("+", Number(3), Binary("+", Number(2), Number(1))), "3 + (2 + 1)"),
            (Binary("×", Binary("+", Number(1), Number(2)), Number(3)), "(1 + 2) × 3"),
            (Binary("+", Number(1), Binary("×", Number(2), Number(3))), "1 + 2 × 3"),
            (Binary("÷", Number(8), Binary("×", Number(2), Number(2))), "8 ÷ (2 × 2)"),
        )
        for tree, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(format_expression(tree), expected)

    def test_commutative_keys_match_without_flattening_association(self):
        first = Binary("+", Number(3), Binary("+", Number(2), Number(1)))
        swapped = Binary("+", Binary("+", Number(1), Number(2)), Number(3))
        different = Binary("+", Binary("+", Number(3), Number(2)), Number(1))
        self.assertEqual(canonical_key(first), canonical_key(swapped))
        self.assertNotEqual(canonical_key(first), canonical_key(different))

        multiplication = Binary("×", Number(6), Number(8))
        reversed_multiplication = Binary("×", Number(8), Number(6))
        self.assertEqual(canonical_key(multiplication), canonical_key(reversed_multiplication))

    def test_constraint_check_visits_every_nested_node(self):
        valid = Binary("+", Binary("-", Number(3), Number(1)), Binary("÷", Number(1), Number(2)))
        invalid_subtraction = Binary("+", Number(1), Binary("-", Number(1), Number(2)))
        invalid_division = Binary("×", Number(2), Binary("÷", Number(2), Number(1)))
        zero_division = Binary("+", Number(1), Binary("÷", Number(0), Number(2)))
        self.assertTrue(constraints_hold(valid))
        self.assertFalse(constraints_hold(invalid_subtraction))
        self.assertFalse(constraints_hold(invalid_division))
        self.assertFalse(constraints_hold(zero_division))

    def test_unknown_operator_is_rejected(self):
        with self.assertRaises(ValueError):
            Binary("%", Number(1), Number(2))


if __name__ == "__main__":
    unittest.main()
