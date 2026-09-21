"""Tests for reproducible performance measurements and report artifacts."""

import tempfile
import unittest
import xml.etree.ElementTree as element_tree
from pathlib import Path

from profile_generation import (
    BenchmarkResult,
    ProfileResult,
    benchmark_sizes,
    profile_hotspots,
    render_svg,
    write_report,
)


class PerformanceReportTests(unittest.TestCase):
    """Protect the machine-readable and human-readable report outputs."""

    def test_benchmark_records_every_requested_size(self):
        rows = benchmark_sizes((10, 20), value_range=10)
        self.assertEqual([row.count for row in rows], [10, 20])
        self.assertTrue(all(row.elapsed_seconds > 0 for row in rows))
        self.assertTrue(all(row.exercises_per_second > 0 for row in rows))

    def test_profile_returns_project_hotspots_in_descending_order(self):
        hotspots = profile_hotspots(count=100, value_range=10)
        self.assertTrue(hotspots)
        self.assertTrue(any("generator.py" in row.function for row in hotspots))
        cumulative_times = [row.cumulative_seconds for row in hotspots]
        self.assertEqual(cumulative_times, sorted(cumulative_times, reverse=True))

    def test_svg_and_markdown_contain_measured_data(self):
        rows = [
            BenchmarkResult(10, 0.01, 1000.0),
            BenchmarkResult(100, 0.05, 2000.0),
            BenchmarkResult(1000, 0.40, 2500.0),
        ]
        hotspots = [
            ProfileResult("generator.py:1(generate_exercises)", 1, 0.2, 0.4),
        ]

        with tempfile.TemporaryDirectory() as directory:
            svg_path = Path(directory, "performance.svg")
            report_path = Path(directory, "performance.md")
            render_svg(rows, svg_path)
            write_report(rows, hotspots, report_path)
            element_tree.parse(str(svg_path))
            svg_text = svg_path.read_text(encoding="utf-8")
            report_text = report_path.read_text(encoding="utf-8")

        self.assertIn("生成耗时", svg_text)
        self.assertIn("1,000", svg_text)
        self.assertIn("| 1,000 | 0.400000 | 2,500.00 |", report_text)
        self.assertIn("generator.py:1(generate_exercises)", report_text)


if __name__ == "__main__":
    unittest.main()
