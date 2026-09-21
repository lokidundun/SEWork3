"""Read numbered files and grade answers with exact rational arithmetic."""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from .expression import evaluate
from .numbers import NumberFormatError, parse_number
from .parser import ExpressionSyntaxError, parse_expression


PathInput = Union[str, Path]
_EXERCISE_LINE_RE = re.compile(r"\s*(\d+)\.\s*(.*?)\s*=\s*")
_ANSWER_LINE_RE = re.compile(r"\s*(\d+)\.\s*(.*?)\s*")


class ExerciseFileError(ValueError):
    """Raised when an exercise file cannot be graded safely."""


@dataclass(frozen=True)
class GradeResult:
    """Question numbers split into correct and wrong groups."""

    correct: Tuple[int, ...]
    wrong: Tuple[int, ...]


def _load_exercises(path: PathInput) -> List[Tuple[int, Fraction]]:
    exercises = []
    expected_number = 1
    for line_number, line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(),
        1,
    ):
        if not line.strip():
            continue
        match = _EXERCISE_LINE_RE.fullmatch(line)
        if match is None:
            raise ExerciseFileError("题目文件第 {} 行格式错误".format(line_number))

        question_number = int(match.group(1))
        if question_number != expected_number:
            raise ExerciseFileError(
                "题目文件第 {} 行编号应为 {}，实际为 {}".format(
                    line_number,
                    expected_number,
                    question_number,
                )
            )

        try:
            answer = evaluate(parse_expression(match.group(2)))
        except (ExpressionSyntaxError, ZeroDivisionError) as error:
            raise ExerciseFileError(
                "题目文件第 {} 行表达式错误: {}".format(line_number, error)
            ) from error

        exercises.append((question_number, answer))
        expected_number += 1
    return exercises


def _load_answers(path: PathInput) -> Dict[int, Optional[Fraction]]:
    answers: Dict[int, Optional[Fraction]] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        match = _ANSWER_LINE_RE.fullmatch(line)
        if match is None:
            continue

        question_number = int(match.group(1))
        if question_number in answers:
            answers[question_number] = None
            continue

        try:
            answers[question_number] = parse_number(match.group(2))
        except NumberFormatError:
            answers[question_number] = None
    return answers


def grade_files(exercise_path: PathInput, answer_path: PathInput) -> GradeResult:
    """Compare numbered answers against evaluated numbered exercises."""

    exercises = _load_exercises(exercise_path)
    submitted_answers = _load_answers(answer_path)
    correct = []
    wrong = []

    for question_number, expected_answer in exercises:
        submitted_answer = submitted_answers.get(question_number)
        if submitted_answer == expected_answer:
            correct.append(question_number)
        else:
            wrong.append(question_number)

    return GradeResult(tuple(correct), tuple(wrong))


def format_grade(result: GradeResult) -> str:
    """Render the exact Grade.txt format."""

    correct_numbers = ", ".join(str(number) for number in result.correct)
    wrong_numbers = ", ".join(str(number) for number in result.wrong)
    return (
        "Correct: {} ({})\n".format(len(result.correct), correct_numbers)
        + "Wrong: {} ({})\n".format(len(result.wrong), wrong_numbers)
    )
