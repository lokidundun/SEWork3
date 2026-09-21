"""Tests for exact grading of numbered exercise and answer files."""

import tempfile
import unittest
from pathlib import Path

from arithmetic.grader import ExerciseFileError, GradeResult, format_grade, grade_files


class GraderTests(unittest.TestCase):
    """Protect result classification and malformed-input behavior."""

    @staticmethod
    def _write(directory, name, text):
        path = Path(directory, name)
        path.write_text(text, encoding="utf-8")
        return path

    def test_correct_wrong_missing_and_invalid_answers(self):
        with tempfile.TemporaryDirectory(prefix="批改-") as directory:
            exercises = self._write(
                directory,
                "Exercises.txt",
                "1. 1/6 + 1/8 =\n"
                "2. 3 - 1 =\n"
                "3. 1 ÷ 2 =\n"
                "4. 1 + 1 =\n",
            )
            answers = self._write(
                directory,
                "Answers.txt",
                "1. 7/24\n"
                "2. 3\n"
                "3. not-a-number\n",
            )
            result = grade_files(exercises, answers)

        self.assertEqual(result.correct, (1,))
        self.assertEqual(result.wrong, (2, 3, 4))
        self.assertEqual(
            format_grade(result),
            "Correct: 1 (1)\nWrong: 3 (2, 3, 4)\n",
        )

    def test_numerically_equivalent_answer_forms_are_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            exercises = self._write(directory, "e.txt", "1. 1'1/2 + 1/2 =\n")
            answers = self._write(directory, "a.txt", "1. 4/2\n")
            result = grade_files(exercises, answers)
        self.assertEqual(result, GradeResult(correct=(1,), wrong=()))

    def test_extra_answer_numbers_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            exercises = self._write(directory, "e.txt", "1. 1 + 1 =\n")
            answers = self._write(directory, "a.txt", "1. 2\n9. 100\n")
            result = grade_files(exercises, answers)
        self.assertEqual(result, GradeResult(correct=(1,), wrong=()))

    def test_duplicate_answer_number_is_wrong(self):
        with tempfile.TemporaryDirectory() as directory:
            exercises = self._write(directory, "e.txt", "1. 1 + 1 =\n")
            answers = self._write(directory, "a.txt", "1. 2\n1. 2\n")
            result = grade_files(exercises, answers)
        self.assertEqual(result, GradeResult(correct=(), wrong=(1,)))

    def test_broken_or_nonsequential_exercise_file_is_rejected(self):
        invalid_files = (
            "1. 1 + =\n",
            "1. 1 + 1 =\n3. 2 + 2 =\n",
            "not numbered\n",
        )
        for contents in invalid_files:
            with self.subTest(contents=contents):
                with tempfile.TemporaryDirectory() as directory:
                    exercises = self._write(directory, "e.txt", contents)
                    answers = self._write(directory, "a.txt", "1. 2\n")
                    with self.assertRaises(ExerciseFileError):
                        grade_files(exercises, answers)

    def test_empty_result_uses_empty_parentheses(self):
        self.assertEqual(
            format_grade(GradeResult(correct=(), wrong=())),
            "Correct: 0 ()\nWrong: 0 ()\n",
        )


if __name__ == "__main__":
    unittest.main()
