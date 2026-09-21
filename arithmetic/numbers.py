"""Parse and format non-negative integers, fractions, and mixed numbers."""

import re
from fractions import Fraction


class NumberFormatError(ValueError):
    """Raised when a number does not follow the supported exercise syntax."""


_INTEGER_RE = re.compile(r"\d+")
_FRACTION_RE = re.compile(r"(\d+)/(\d+)")
_MIXED_RE = re.compile(r"(\d+)['’](\d+)/(\d+)")


def parse_number(text: str) -> Fraction:
    """Convert an integer, fraction, or mixed number string to a Fraction."""

    cleaned = text.strip()

    mixed = _MIXED_RE.fullmatch(cleaned)
    if mixed:
        whole, numerator, denominator = map(int, mixed.groups())
        if denominator == 0 or numerator == 0 or numerator >= denominator:
            raise NumberFormatError("带分数的分数部分必须为真分数")
        return Fraction(whole * denominator + numerator, denominator)

    fraction = _FRACTION_RE.fullmatch(cleaned)
    if fraction:
        numerator, denominator = map(int, fraction.groups())
        if denominator == 0:
            raise NumberFormatError("分母不能为 0")
        return Fraction(numerator, denominator)

    if _INTEGER_RE.fullmatch(cleaned):
        return Fraction(int(cleaned))

    raise NumberFormatError("无法识别的数值格式: {!r}".format(text))


def format_number(value: Fraction) -> str:
    """Format a non-negative rational number in the assignment notation."""

    normalized = Fraction(value)
    if normalized < 0:
        raise ValueError("小学四则运算结果不能为负数")

    whole, remainder = divmod(normalized.numerator, normalized.denominator)
    if remainder == 0:
        return str(whole)
    if whole == 0:
        return "{}/{}".format(remainder, normalized.denominator)
    return "{}'{}/{}".format(whole, remainder, normalized.denominator)
