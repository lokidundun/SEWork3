"""Command-line entry point for arithmetic exercise generation."""

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from arithmetic.expression import format_expression
from arithmetic.generator import QuestionSpaceExhausted, generate_exercises
from arithmetic.numbers import format_number


EXERCISE_FILE = "Exercises.txt"
ANSWER_FILE = "Answers.txt"
GRADE_FILE = "Grade.txt"


def build_parser() -> argparse.ArgumentParser:
    """Create the public command-line parser."""

    parser = argparse.ArgumentParser(
        prog="Myapp",
        description="自动生成并批改小学四则运算题目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n  python main.py -n 10 -r 10",
    )
    parser.add_argument(
        "-n",
        type=int,
        default=None,
        metavar="N",
        help="生成题目数量，默认 10",
    )
    parser.add_argument(
        "-r",
        type=int,
        default=None,
        metavar="R",
        help="叶子数值和分母的范围上界，生成模式必须提供",
    )
    return parser


def run_generation(
    arguments: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int:
    """Validate generation options and write exercises with exact answers."""

    count = 10 if arguments.n is None else arguments.n
    if arguments.r is None:
        parser.error("生成题目时必须使用 -r 指定数值范围")
    if count < 1:
        parser.error("-n 必须是正整数")
    if arguments.r < 1:
        parser.error("-r 必须是正整数")

    try:
        exercises = generate_exercises(count, arguments.r)
    except QuestionSpaceExhausted as error:
        print("错误: {}".format(error), file=sys.stderr)
        return 1

    exercise_lines = [
        "{}. {} =".format(index, format_expression(item.expression))
        for index, item in enumerate(exercises, 1)
    ]
    answer_lines = [
        "{}. {}".format(index, format_number(item.answer))
        for index, item in enumerate(exercises, 1)
    ]

    Path(EXERCISE_FILE).write_text(
        "\n".join(exercise_lines) + "\n",
        encoding="utf-8",
    )
    Path(ANSWER_FILE).write_text(
        "\n".join(answer_lines) + "\n",
        encoding="utf-8",
    )
    print("已生成 {} 道题目。".format(count))
    print("题目文件: {}".format(EXERCISE_FILE))
    print("答案文件: {}".format(ANSWER_FILE))
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Parse arguments and run the selected operation."""

    parser = build_parser()
    arguments = parser.parse_args(argv)
    return run_generation(arguments, parser)


if __name__ == "__main__":
    sys.exit(main())
