"""Expression-tree model, exact evaluation, formatting, and deduplication."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterator, Tuple, Union

from .numbers import format_number


PRECEDENCE = {"+": 1, "-": 1, "×": 2, "÷": 2}
COMMUTATIVE = frozenset(("+", "×"))


@dataclass(frozen=True)
class Number:
    """A non-operator expression node."""

    value: Fraction

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", Fraction(self.value))


@dataclass(frozen=True)
class Binary:
    """A binary arithmetic operation with explicit left and right children."""

    operator: str
    left: "Expression"
    right: "Expression"

    def __post_init__(self) -> None:
        if self.operator not in PRECEDENCE:
            raise ValueError("未知运算符: {!r}".format(self.operator))


Expression = Union[Number, Binary]
CanonicalKey = Tuple[object, ...]


def evaluate(node: Expression) -> Fraction:
    """Evaluate an expression exactly."""

    if isinstance(node, Number):
        return node.value

    left_value = evaluate(node.left)
    right_value = evaluate(node.right)
    if node.operator == "+":
        return left_value + right_value
    if node.operator == "-":
        return left_value - right_value
    if node.operator == "×":
        return left_value * right_value
    if right_value == 0:
        raise ZeroDivisionError("除数不能为 0")
    return left_value / right_value


def operator_count(node: Expression) -> int:
    """Count binary operators in an expression tree."""

    if isinstance(node, Number):
        return 0
    return 1 + operator_count(node.left) + operator_count(node.right)


def walk(node: Expression) -> Iterator[Expression]:
    """Yield every node in pre-order."""

    yield node
    if isinstance(node, Binary):
        yield from walk(node.left)
        yield from walk(node.right)


def constraints_hold(node: Expression) -> bool:
    """Return whether every subtree obeys the assignment's arithmetic rules."""

    if isinstance(node, Number):
        return node.value >= 0
    if not constraints_hold(node.left) or not constraints_hold(node.right):
        return False

    left_value = evaluate(node.left)
    right_value = evaluate(node.right)
    if node.operator == "-":
        return left_value >= right_value
    if node.operator == "÷":
        if right_value == 0:
            return False
        quotient = left_value / right_value
        return Fraction(0) < quotient < Fraction(1)
    return True


def canonical_key(node: Expression) -> CanonicalKey:
    """Build a key invariant under child swaps at + and × nodes only."""

    if isinstance(node, Number):
        return ("number", node.value.numerator, node.value.denominator)

    left_key = canonical_key(node.left)
    right_key = canonical_key(node.right)
    if node.operator in COMMUTATIVE and right_key < left_key:
        left_key, right_key = right_key, left_key
    return (node.operator, left_key, right_key)


def format_expression(node: Expression) -> str:
    """Render an expression with spaces and only structure-preserving brackets."""

    return _format_expression(node, parent_precedence=0, is_right_child=False)


def _format_expression(
    node: Expression,
    parent_precedence: int,
    is_right_child: bool,
) -> str:
    if isinstance(node, Number):
        return format_number(node.value)

    precedence = PRECEDENCE[node.operator]
    left_text = _format_expression(node.left, precedence, False)
    right_text = _format_expression(node.right, precedence, True)
    text = "{} {} {}".format(left_text, node.operator, right_text)

    needs_parentheses = precedence < parent_precedence
    if is_right_child and precedence == parent_precedence:
        needs_parentheses = True
    return "({})".format(text) if needs_parentheses else text
