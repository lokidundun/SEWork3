"""Measure exercise-generation performance and produce report artifacts."""

from __future__ import annotations

import cProfile
import html
import math
import platform
import pstats
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Sequence

from arithmetic.generator import generate_exercises


DEFAULT_SIZES = (10, 100, 1000, 10000)
DEFAULT_RANGE = 50


@dataclass(frozen=True)
class BenchmarkResult:
    """Elapsed time and throughput for one generation size."""

    count: int
    elapsed_seconds: float
    exercises_per_second: float


@dataclass(frozen=True)
class ProfileResult:
    """One project function extracted from cProfile statistics."""

    function: str
    call_count: int
    total_seconds: float
    cumulative_seconds: float


def benchmark_sizes(
    sizes: Sequence[int],
    value_range: int = DEFAULT_RANGE,
) -> List[BenchmarkResult]:
    """Generate each requested size with a deterministic random seed."""

    results = []
    for count in sizes:
        started = time.perf_counter()
        generate_exercises(count, value_range, random.Random(20260921 + count))
        elapsed = time.perf_counter() - started
        results.append(BenchmarkResult(count, elapsed, count / elapsed))
    return results


def profile_hotspots(
    count: int = 10000,
    value_range: int = DEFAULT_RANGE,
) -> List[ProfileResult]:
    """Return the ten project functions with the highest cumulative time."""

    profiler = cProfile.Profile()
    profiler.enable()
    generate_exercises(count, value_range, random.Random(20260921))
    profiler.disable()

    statistics = pstats.Stats(profiler)
    results = []
    for function_key, values in statistics.stats.items():
        filename, line_number, function_name = function_key
        normalized_filename = filename.replace("\\", "/")
        if "/arithmetic/" not in normalized_filename:
            continue
        _primitive_calls, total_calls, total_time, cumulative_time, _callers = values
        results.append(
            ProfileResult(
                "{}:{}({})".format(Path(filename).name, line_number, function_name),
                total_calls,
                total_time,
                cumulative_time,
            )
        )

    results.sort(key=lambda row: row.cumulative_seconds, reverse=True)
    return results[:10]


def render_svg(rows: Sequence[BenchmarkResult], target: Path) -> None:
    """Render elapsed times as a dependency-free SVG line chart."""

    if not rows:
        raise ValueError("性能图至少需要一个测量点")

    width = 960
    height = 540
    left = 90
    right = 40
    top = 70
    bottom = 80
    plot_width = width - left - right
    plot_height = height - top - bottom
    max_elapsed = max(row.elapsed_seconds for row in rows)
    y_limit = max_elapsed * 1.15 if max_elapsed > 0 else 1.0

    logarithmic_counts = [math.log10(row.count) for row in rows]
    min_log = min(logarithmic_counts)
    max_log = max(logarithmic_counts)

    def x_coordinate(log_count: float) -> float:
        if min_log == max_log:
            return left + plot_width / 2
        return left + (log_count - min_log) / (max_log - min_log) * plot_width

    def y_coordinate(seconds: float) -> float:
        return top + plot_height - seconds / y_limit * plot_height

    points = [
        (x_coordinate(log_count), y_coordinate(row.elapsed_seconds), row)
        for log_count, row in zip(logarithmic_counts, rows)
    ]
    polyline_points = " ".join("{:.2f},{:.2f}".format(x, y) for x, y, _ in points)

    svg = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540">',
        '<rect width="960" height="540" fill="#f8fafc"/>',
        '<text x="480" y="38" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#0f172a">生成耗时随题量增长趋势</text>',
    ]

    for tick in range(6):
        value = y_limit * tick / 5
        y = y_coordinate(value)
        svg.append(
            '<line x1="{left}" y1="{y:.2f}" x2="{right_edge}" y2="{y:.2f}" stroke="#cbd5e1" stroke-width="1"/>'.format(
                left=left,
                y=y,
                right_edge=left + plot_width,
            )
        )
        svg.append(
            '<text x="{x}" y="{y:.2f}" text-anchor="end" font-family="sans-serif" font-size="13" fill="#475569">{value:.4f}</text>'.format(
                x=left - 12,
                y=y + 5,
                value=value,
            )
        )

    svg.extend(
        (
            '<line x1="{0}" y1="{1}" x2="{2}" y2="{1}" stroke="#334155" stroke-width="2"/>'.format(
                left,
                top + plot_height,
                left + plot_width,
            ),
            '<line x1="{0}" y1="{1}" x2="{0}" y2="{2}" stroke="#334155" stroke-width="2"/>'.format(
                left,
                top,
                top + plot_height,
            ),
            '<polyline points="{}" fill="none" stroke="#2563eb" stroke-width="3"/>'.format(
                polyline_points
            ),
        )
    )

    for x, y, row in points:
        count_label = "{:,}".format(row.count)
        time_label = "{:.4f}s".format(row.elapsed_seconds)
        svg.extend(
            (
                '<circle cx="{:.2f}" cy="{:.2f}" r="6" fill="#2563eb"/>'.format(x, y),
                '<text x="{:.2f}" y="{}" text-anchor="middle" font-family="sans-serif" font-size="13" fill="#334155">{}</text>'.format(
                    x,
                    top + plot_height + 26,
                    html.escape(count_label),
                ),
                '<text x="{:.2f}" y="{:.2f}" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#1d4ed8">{}</text>'.format(
                    x,
                    max(top + 14, y - 12),
                    html.escape(time_label),
                ),
            )
        )

    svg.extend(
        (
            '<text x="{:.2f}" y="515" text-anchor="middle" font-family="sans-serif" font-size="15" fill="#334155">题目数量（对数刻度）</text>'.format(
                left + plot_width / 2
            ),
            '<text x="24" y="{:.2f}" text-anchor="middle" font-family="sans-serif" font-size="15" fill="#334155" transform="rotate(-90 24 {:.2f})">生成耗时（秒）</text>'.format(
                top + plot_height / 2,
                top + plot_height / 2,
            ),
            '</svg>',
        )
    )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(svg) + "\n", encoding="utf-8")


def write_report(
    rows: Sequence[BenchmarkResult],
    hotspots: Sequence[ProfileResult],
    target: Path,
) -> None:
    """Write measured environment, scaling data, and cProfile hotspots."""

    report = [
        "# 题目生成性能测量",
        "",
        "- 测量时间（UTC）：{}".format(
            datetime.now(timezone.utc).isoformat(timespec="seconds")
        ),
        "- Python：{}".format(platform.python_version()),
        "- 操作系统：{} {}".format(platform.system(), platform.release()),
        "- 数值范围：`-r {}`".format(DEFAULT_RANGE),
        "- 复现命令：`python profile_generation.py`",
        "",
        "## 规模测试",
        "",
        "| 题目数 | 耗时（秒） | 吞吐量（题/秒） |",
        "| ---: | ---: | ---: |",
    ]
    report.extend(
        "| {:,} | {:.6f} | {:,.2f} |".format(
            row.count,
            row.elapsed_seconds,
            row.exercises_per_second,
        )
        for row in rows
    )
    report.extend(
        (
            "",
            "## cProfile 热点（10000 题）",
            "",
            "| 函数 | 调用次数 | 自身耗时（秒） | 累计耗时（秒） |",
            "| --- | ---: | ---: | ---: |",
        )
    )
    report.extend(
        "| `{}` | {:,} | {:.6f} | {:.6f} |".format(
            row.function,
            row.call_count,
            row.total_seconds,
            row.cumulative_seconds,
        )
        for row in hotspots
    )
    report.extend(
        (
            "",
            "## 已采用的性能策略",
            "",
            "- 构造每棵子树时同步返回精确值，避免生成阶段反复遍历求值。",
            "- 每个候选题只计算一次规范化键，并使用集合完成平均常数时间判重。",
            "- 除法条件不成立时复用已经生成的左右子树，只替换当前运算符。",
            "",
        )
    )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(report), encoding="utf-8")


def main() -> int:
    """Generate the Markdown report and SVG chart from fresh measurements."""

    rows = benchmark_sizes(DEFAULT_SIZES, DEFAULT_RANGE)
    hotspots = profile_hotspots(10000, DEFAULT_RANGE)
    render_svg(rows, Path("docs/images/performance.svg"))
    write_report(rows, hotspots, Path("docs/performance-results.md"))
    print("性能报告: docs/performance-results.md")
    print("性能图: docs/images/performance.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
