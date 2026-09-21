"""Safe recursive-descent parser for generated arithmetic expressions."""

from __future__ import annotations

import re
from typing import List, Optional

from .expression import Binary, Expression, Number
from .numbers import NumberFormatError, parse_number


class ExpressionSyntaxError(ValueError):
    """Raised when expression text does not match the supported grammar."""


_TOKEN_RE = re.compile(
    r"\s*(?:(\d+(?:['’]\d+/\d+|/\d+)?)|([()+\-×÷]))"
)


def _tokenize(text: str) -> List[str]:
    tokens = []
    position = 0
    while position < len(text):
        match = _TOKEN_RE.match(text, position)
        if match is None:
            if text[position:].strip() == "":
                break
            raise ExpressionSyntaxError(
                "表达式第 {} 个字符附近无法识别".format(position + 1)
            )
        tokens.append(match.group(1) or match.group(2))
        position = match.end()
    return tokens


class _Parser:
    def __init__(self, tokens: List[str]) -> None:
        self._tokens = tokens
        self._position = 0

    def parse(self) -> Expression:
        if not self._tokens:
            raise ExpressionSyntaxError("表达式不能为空")
        node = self._parse_sum()
        trailing = self._peek()
        if trailing is not None:
            raise ExpressionSyntaxError("表达式末尾存在多余内容: {!r}".format(trailing))
        return node

    def _peek(self) -> Optional[str]:
        if self._position >= len(self._tokens):
            return None
        return self._tokens[self._position]

    def _take(self) -> str:
        token = self._peek()
        if token is None:
            raise ExpressionSyntaxError("表达式意外结束")
        self._position += 1
        return token

    def _parse_sum(self) -> Expression:
        node = self._parse_product()
        while self._peek() in ("+", "-"):
            operator = self._take()
            node = Binary(operator, node, self._parse_product())
        return node

    def _parse_product(self) -> Expression:
        node = self._parse_factor()
        while self._peek() in ("×", "÷"):
            operator = self._take()
            node = Binary(operator, node, self._parse_factor())
        return node

    def _parse_factor(self) -> Expression:
        token = self._peek()
        if token is None:
            raise ExpressionSyntaxError("缺少数字或左括号")

        if token == "(":
            self._take()
            node = self._parse_sum()
            if self._peek() != ")":
                raise ExpressionSyntaxError("缺少右括号")
            self._take()
            return node

        if token in ("+", "-", "×", "÷", ")"):
            raise ExpressionSyntaxError("此处需要数字或左括号，实际为 {!r}".format(token))

        self._take()
        try:
            return Number(parse_number(token))
        except NumberFormatError as error:
            raise ExpressionSyntaxError(str(error)) from error


def parse_expression(text: str) -> Expression:
    """Parse one expression and reject every trailing token or character."""

    return _Parser(_tokenize(text)).parse()
