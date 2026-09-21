"""Tests for valid, bounded, non-repeating exercise generation."""

import random
import unittest

from arithmetic.expression import (
    Binary,
    Number,
    canonical_key,
    constraints_hold,
    evaluate,
    operator_count,
    walk,
)
from arithmetic.generator import QuestionSpaceExhausted, generate_exercises


class GeneratorTests(unittest.TestCase):
    """Protect all structural constraints during random generation."""

    def test_generates_requested_unique_valid_exercises(self):
        exercises = generate_exercises(500, 10, random.Random(20260921))
        keys = {canonical_key(item.expression) for item in exercises}

        self.assertEqual(len(exercises), 500)
        self.assertEqual(len(keys), 500)
        for item in exercises:
            self.assertEqual(item.answer, evaluate(item.expression))
            self.assertTrue(constraints_hold(item.expression))
            self.assertIn(operator_count(item.expression), (1, 2, 3))

    def test_every_division_node_has_strict_proper_fraction_result(self):
        exercises = generate_exercises(500, 20, random.Random(7))
        divisions = []
        for item in exercises:
            for node in walk(item.expression):
                if isinstance(node, Binary) and node.operator == "÷":
                    divisions.append(node)
                    quotient = evaluate(node.left) / evaluate(node.right)
                    self.assertGreater(quotient, 0)
                    self.assertLess(quotient, 1)
        self.assertTrue(divisions)

    def test_leaf_values_and_denominators_stay_in_range(self):
        exercises = generate_exercises(500, 10, random.Random(17))
        fractional_leaf_seen = False
        for item in exercises:
            for node in walk(item.expression):
                if isinstance(node, Number):
                    self.assertGreaterEqual(node.value, 0)
                    self.assertLess(node.value, 10)
                    self.assertLess(node.value.denominator, 10)
                    fractional_leaf_seen |= node.value.denominator != 1
        self.assertTrue(fractional_leaf_seen)

    def test_range_one_can_generate_small_set(self):
        exercises = generate_exercises(10, 1, random.Random(11))
        self.assertEqual(len(exercises), 10)
        self.assertTrue(
            all(
                node.value == 0
                for item in exercises
                for node in walk(item.expression)
                if isinstance(node, Number)
            )
        )

    def test_same_seed_reproduces_same_exercises(self):
        first = generate_exercises(20, 10, random.Random(99))
        second = generate_exercises(20, 10, random.Random(99))
        self.assertEqual(first, second)

    def test_invalid_arguments_are_rejected(self):
        invalid_cases = ((0, 10), (-1, 10), (10, 0), (10, -1))
        for count, value_range in invalid_cases:
            with self.subTest(count=count, value_range=value_range):
                with self.assertRaises(ValueError):
                    generate_exercises(count, value_range)
        with self.assertRaises(ValueError):
            generate_exercises(10, 10, max_stalled_attempts=0)

    def test_exhausted_space_fails_instead_of_looping_forever(self):
        with self.assertRaises(QuestionSpaceExhausted):
            generate_exercises(
                1000,
                1,
                random.Random(1),
                max_stalled_attempts=100,
            )


if __name__ == "__main__":
    unittest.main()
