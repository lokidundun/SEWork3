"""Integration tests for the command-line entry point."""

import io
import os
import tempfile
import unittest
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path

from arithmetic.expression import evaluate
from arithmetic.numbers import parse_number
from arithmetic.parser import parse_expression
from main import main


@contextmanager
def temporary_working_directory(prefix="四则运算-"):
    """Run a test in a temporary current directory and always restore it."""

    previous = Path.cwd()
    with tempfile.TemporaryDirectory(prefix=prefix) as directory:
        os.chdir(directory)
        try:
            yield Path(directory)
        finally:
            os.chdir(previous)


class GenerationCliTests(unittest.TestCase):
    """Protect generation flags and the public text-file contract."""

    def test_generation_writes_numbered_utf8_files(self):
        with temporary_working_directory():
            with redirect_stdout(io.StringIO()):
                exit_code = main(["-n", "5", "-r", "10"])
            exercise_lines = Path("Exercises.txt").read_text(encoding="utf-8").splitlines()
            answer_lines = Path("Answers.txt").read_text(encoding="utf-8").splitlines()

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(exercise_lines), 5)
        self.assertEqual(len(answer_lines), 5)
        for index, (exercise_line, answer_line) in enumerate(
            zip(exercise_lines, answer_lines),
            1,
        ):
            self.assertTrue(exercise_line.startswith("{}. ".format(index)))
            self.assertTrue(exercise_line.endswith(" ="))
            self.assertTrue(answer_line.startswith("{}. ".format(index)))

            expression_text = exercise_line.split(". ", 1)[1][:-2]
            answer_text = answer_line.split(". ", 1)[1]
            self.assertEqual(
                evaluate(parse_expression(expression_text)),
                parse_number(answer_text),
            )

    def test_generation_defaults_to_ten_exercises(self):
        with temporary_working_directory():
            with redirect_stdout(io.StringIO()):
                exit_code = main(["-r", "10"])
            exercise_lines = Path("Exercises.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(exercise_lines), 10)

    def test_generation_requires_range(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                main(["-n", "2"])
        self.assertEqual(raised.exception.code, 2)

    def test_generation_rejects_invalid_numeric_arguments(self):
        cases = (
            ["-n", "0", "-r", "10"],
            ["-n", "-1", "-r", "10"],
            ["-n", "abc", "-r", "10"],
            ["-r", "0"],
            ["-r", "-1"],
            ["-r", "abc"],
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                with redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:
                        main(arguments)
                self.assertEqual(raised.exception.code, 2)

    def test_exhausted_generation_keeps_existing_output_files(self):
        with temporary_working_directory():
            Path("Exercises.txt").write_text("old exercises\n", encoding="utf-8")
            Path("Answers.txt").write_text("old answers\n", encoding="utf-8")
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                exit_code = main(["-n", "1000", "-r", "1"])
            exercise_text = Path("Exercises.txt").read_text(encoding="utf-8")
            answer_text = Path("Answers.txt").read_text(encoding="utf-8")

        self.assertEqual(exit_code, 1)
        self.assertEqual(exercise_text, "old exercises\n")
        self.assertEqual(answer_text, "old answers\n")


class GradingCliTests(unittest.TestCase):
    """Protect grading-mode dispatch and safe Grade.txt writes."""

    def test_grading_writes_exact_result_from_unicode_paths(self):
        with temporary_working_directory(prefix="批改命令-") as directory:
            input_directory = directory / "中文输入"
            input_directory.mkdir()
            exercises = input_directory / "题目.txt"
            answers = input_directory / "作答.txt"
            exercises.write_text(
                "1. 1/6 + 1/8 =\n2. 3 - 1 =\n3. 1 ÷ 2 =\n",
                encoding="utf-8",
            )
            answers.write_text("1. 7/24\n2. 3\n3. 1/2\n", encoding="utf-8")

            with redirect_stdout(io.StringIO()):
                exit_code = main(["-e", str(exercises), "-a", str(answers)])
            grade_text = Path("Grade.txt").read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertEqual(grade_text, "Correct: 2 (1, 3)\nWrong: 1 (2)\n")

    def test_grading_requires_both_file_arguments(self):
        for arguments in (["-e", "e.txt"], ["-a", "a.txt"]):
            with self.subTest(arguments=arguments):
                error_output = io.StringIO()
                with redirect_stderr(error_output):
                    with self.assertRaises(SystemExit) as raised:
                        main(arguments)
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("-e 和 -a 必须同时提供", error_output.getvalue())

    def test_grading_rejects_generation_arguments(self):
        cases = (
            ["-e", "e.txt", "-a", "a.txt", "-n", "2"],
            ["-e", "e.txt", "-a", "a.txt", "-r", "10"],
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                error_output = io.StringIO()
                with redirect_stderr(error_output):
                    with self.assertRaises(SystemExit) as raised:
                        main(arguments)
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("批改模式不能与生成参数混用", error_output.getvalue())

    def test_broken_exercise_does_not_replace_existing_grade(self):
        with temporary_working_directory():
            Path("Exercises.txt").write_text("1. 1 + =\n", encoding="utf-8")
            Path("Answers.txt").write_text("1. 1\n", encoding="utf-8")
            Path("Grade.txt").write_text("previous result\n", encoding="utf-8")
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                exit_code = main(["-e", "Exercises.txt", "-a", "Answers.txt"])
            grade_text = Path("Grade.txt").read_text(encoding="utf-8")

        self.assertEqual(exit_code, 1)
        self.assertEqual(grade_text, "previous result\n")

    def test_missing_input_file_returns_error_without_grade(self):
        with temporary_working_directory():
            Path("Answers.txt").write_text("1. 1\n", encoding="utf-8")
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                exit_code = main(["-e", "missing.txt", "-a", "Answers.txt"])
            grade_exists = Path("Grade.txt").exists()

        self.assertEqual(exit_code, 1)
        self.assertFalse(grade_exists)


if __name__ == "__main__":
    unittest.main()
