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


if __name__ == "__main__":
    unittest.main()
