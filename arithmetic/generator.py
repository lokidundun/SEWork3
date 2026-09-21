"""Generate valid and non-repeating arithmetic expression trees."""

from __future__ import annotations

import random
from dataclasses import dataclass
from fractions import Fraction
from typing import List, Optional, Set, Tuple

from .expression import Binary, CanonicalKey, Expression, Number, canonical_key


_OPERATORS = ("+", "-", "×", "÷")
_OPERATOR_WEIGHTS = (3, 3, 3, 2)
_DIVISION_FALLBACKS = ("+", "-", "×")


class QuestionSpaceExhausted(RuntimeError):
    """Raised when too many attempts fail to find another unique exercise."""


@dataclass(frozen=True)
class GeneratedExercise:
    """One generated expression paired with its already-computed answer."""

    expression: Expression
    answer: Fraction


def _random_operand(value_range: int, rng: random.Random) -> Fraction:
    """Return a natural number or fractional value in [0, value_range)."""

    if value_range >= 3 and rng.random() < 0.4:
        denominator = rng.randint(2, value_range - 1)
        whole = rng.randrange(value_range)
        remainder = rng.randint(1, denominator - 1)
        return Fraction(whole * denominator + remainder, denominator)
    return Fraction(rng.randrange(value_range))


def _build_candidate(
    operator_slots: int,
    value_range: int,
    rng: random.Random,
) -> Tuple[Expression, Fraction]:
    if operator_slots == 0:
        value = _random_operand(value_range, rng)
        return Number(value), value

    left_slots = rng.randint(0, operator_slots - 1)
    right_slots = operator_slots - 1 - left_slots
    left, left_value = _build_candidate(left_slots, value_range, rng)
    right, right_value = _build_candidate(right_slots, value_range, rng)
    operator = rng.choices(_OPERATORS, weights=_OPERATOR_WEIGHTS, k=1)[0]

    if operator == "÷":
        if Fraction(0) < left_value < right_value:
            return Binary("÷", left, right), left_value / right_value
        if Fraction(0) < right_value < left_value:
            return Binary("÷", right, left), right_value / left_value
        operator = rng.choice(_DIVISION_FALLBACKS)

    if operator == "+":
        return Binary("+", left, right), left_value + right_value
    if operator == "×":
        return Binary("×", left, right), left_value * right_value

    if left_value < right_value:
        left, right = right, left
        left_value, right_value = right_value, left_value
    return Binary("-", left, right), left_value - right_value


def generate_exercises(
    count: int,
    value_range: int,
    rng: Optional[random.Random] = None,
    max_stalled_attempts: Optional[int] = None,
) -> List[GeneratedExercise]:
    """Generate the requested number of valid, canonically unique exercises."""

    if count < 1:
        raise ValueError("题目数量必须是正整数")
    if value_range < 1:
        raise ValueError("数值范围必须是正整数")
    if max_stalled_attempts is not None and max_stalled_attempts < 1:
        raise ValueError("最大停滞次数必须是正整数")

    random_source = rng if rng is not None else random.Random()
    stalled_limit = (
        max(10000, count * 2)
        if max_stalled_attempts is None
        else max_stalled_attempts
    )

    exercises = []
    seen: Set[CanonicalKey] = set()
    stalled_attempts = 0

    while len(exercises) < count:
        operator_slots = random_source.randint(1, 3)
        expression, answer = _build_candidate(
            operator_slots,
            value_range,
            random_source,
        )
        key = canonical_key(expression)
        if key in seen:
            stalled_attempts += 1
            if stalled_attempts >= stalled_limit:
                raise QuestionSpaceExhausted(
                    "在 0~{} 的范围内已生成 {} 道不同题目，无法达到 {} 道；"
                    "请增大 -r 或减小 -n。".format(
                        value_range - 1,
                        len(exercises),
                        count,
                    )
                )
            continue

        seen.add(key)
        exercises.append(GeneratedExercise(expression, answer))
        stalled_attempts = 0

    return exercises
