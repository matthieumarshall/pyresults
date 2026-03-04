"""HTML output generator implementation.

Generates a self-contained, interactive HTML file that mimics the PDF output
layout while adding interactivity such as hovering over a team's round score
to see a tooltip listing the contributing athletes and their positions.
"""

import html
import logging
from pathlib import Path

import pandas as pd

from pyresults.config import CompetitionConfig

from .interfaces import IOutputGenerator
from .score_data_provider import CategoryDisplayData, ScoreDataProvider

logger = logging.getLogger(__name__)

# Mapping from display round column names back to the raw round identifiers
# used in the per-round file paths.
_DISPLAY_TO_ROUND_NUM: dict[str, str] = {
    "R 1": "r1",
    "R 2": "r2",
    "R 3": "r3",
    "R 4": "r4",
    "R 5": "r5",
}

# Same ordering sets as PdfOutputGenerator
_ADULT_WOMEN_CODES = {
    "U20W",
    "SW",
    "WV40",
    "WV50",
    "WV60",
    "WV70",
    "Team Women",
    "WomensOverall",
}
_ADULT_MEN_CODES = {
    "U20M",
    "SM",
    "MV40",
    "MV50",
    "MV60",
    "MV70",
    "Team Men",
    "MensOverall",
}


class HtmlOutputGenerator(IOutputGenerator):
    """Generates an interactive HTML file from pre-computed score data.

    This class is a pure rendering layer.  All score computation and data
    preparation is handled by ``ScoreDataProvider``; this generator only
    converts the resulting DataFrames into styled, interactive HTML tables.

    Interactive features:
    - Hovering over a team's round-score cell shows a tooltip listing the
      athletes who contributed to that score and their finishing positions.
    - Hovering over a team's total score cell shows a summary of all
      contributing athletes grouped by round.
    - A sticky navigation sidebar lets users jump directly to any category.
    """

    def __init__(self, config: CompetitionConfig, output_path: Path, max_rows: int | None = None):
        """Initialise HTML generator.

        Args:
            config: Competition configuration
            output_path: Path where the HTML file should be saved
            max_rows: If set, limit each category table to this many rows
        """
        self.config = config
        self.output_path = output_path
        self.max_rows = max_rows
        self.data_provider = ScoreDataProvider(config)

    # ------------------------------------------------------------------
    # IOutputGenerator interface
    # ------------------------------------------------------------------

    def generate(self) -> None:
        """Generate HTML file with all score tables."""
        logger.info(f"Generating HTML output to {self.output_path}")

        all_data = self.data_provider.get_all_category_data()
        logger.debug(f"Found {len(all_data)} categories to include in HTML")

        # Use the same category ordering as the PDF generator
        all_data = self._reorder_categories(all_data)

        html_content = self._build_html(all_data)

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.output_path.write_text(html_content, encoding="utf-8")
            logger.info(f"Successfully saved HTML file to {self.output_path}")
        except Exception as e:
            logger.error(f"Failed to save HTML file to {self.output_path}: {e}")
            raise OSError(f"Failed to save HTML file to {self.output_path}: {e}") from e

    # ------------------------------------------------------------------
    # Ordering helpers (mirrors PdfOutputGenerator)
    # ------------------------------------------------------------------

    def _reorder_categories(self, data: list[CategoryDisplayData]) -> list[CategoryDisplayData]:
        """Reorder categories: youth first, then adult women, then adult men."""
        youth: list[CategoryDisplayData] = []
        adult_women: list[CategoryDisplayData] = []
        adult_men: list[CategoryDisplayData] = []

        for item in data:
            if item.category_code in _ADULT_WOMEN_CODES:
                adult_women.append(item)
            elif item.category_code in _ADULT_MEN_CODES:
                adult_men.append(item)
            else:
                youth.append(item)

        return youth + adult_women + adult_men

    # ------------------------------------------------------------------
    # Runner / tooltip data loading
    # ------------------------------------------------------------------

    def _load_runner_data(self, actual_code: str) -> dict[str, dict[str, list[str]]]:
        """Load per-round runner data for a team category.

        Args:
            actual_code: The category code without the ``"Team "`` prefix
                         (e.g. ``"U13B"``, ``"Men"``, ``"Women"``).

        Returns:
            Nested mapping ``team_name -> round_display_name -> [runner_str, ...]``.
            For example::

                {
                    "Oxford AC A": {
                        "R 1": ["Alice Smith (3)", "Bob Jones (5)"],
                        "R 2": ["Alice Smith (2)"],
                    }
                }

            Only rounds/teams for which per-round data files exist are
            included; missing entries simply have no tooltip.
        """
        result: dict[str, dict[str, list[str]]] = {}

        for round_num in self.config.round_numbers:
            display_name = f"R {round_num[1:]}"  # "r1" -> "R 1"
            path = self.config.data_base_path / round_num / "teams" / f"{actual_code}.csv"
            if not path.exists():
                continue
            try:
                df = pd.read_csv(path)
            except Exception as exc:
                logger.debug(f"Could not read {path}: {exc}")
                continue

            for _, row in df.iterrows():
                team = str(row.get("Team", ""))
                if not team or team.lower() == "nan":
                    continue
                runners: list[str] = []
                for i in range(1, 30):
                    col = f"Runner{i}"
                    if col not in df.columns:
                        break
                    val = row.get(col)
                    if pd.notna(val) and str(val).strip():
                        runners.append(str(val))
                if runners:
                    result.setdefault(team, {})[display_name] = runners

        return result

    # ------------------------------------------------------------------
    # HTML generation
    # ------------------------------------------------------------------

    def _make_section_id(self, data: CategoryDisplayData) -> str:
        """Generate a URL-safe section id for a category."""
        raw = data.title
        safe = "".join(c if c.isalnum() else "-" for c in raw)
        return safe.strip("-")

    def _build_html(self, all_data: list[CategoryDisplayData]) -> str:
        """Build the complete self-contained HTML document."""
        # Pre-build navigation and section fragments
        nav_items: list[str] = []
        sections: list[str] = []

        for category_data in all_data:
            section_id = self._make_section_id(category_data)
            nav_items.append(
                f'  <li><a href="#{section_id}">{html.escape(category_data.title)}</a></li>'
            )
            sections.append(self._build_section(category_data, section_id))

        nav_html = "\n".join(nav_items)
        sections_html = "\n\n".join(sections)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Oxfordshire Cross Country League 2025-2026</title>
  <style>
{_CSS}
  </style>
</head>
<body>
  <div class="page-wrapper">

    <aside class="sidebar">
      <div class="sidebar-header">
        <span class="sidebar-title">Categories</span>
      </div>
      <nav>
        <ul>
{nav_html}
        </ul>
      </nav>
    </aside>

    <main class="content">
      <header class="page-header">
        <h1>Oxfordshire Cross Country League 2025-2026</h1>
      </header>

{sections_html}

    </main>
  </div>

  <div id="tooltip" class="tooltip" role="tooltip" aria-hidden="true"></div>

  <script>
{_JS}
  </script>
</body>
</html>"""

    def _build_section(self, data: CategoryDisplayData, section_id: str) -> str:
        """Build the HTML for a single category section."""
        df = data.dataframe.copy()

        # Apply the same row-limiting logic as PdfOutputGenerator
        if self.max_rows is not None:
            df = df.head(self.max_rows)
        elif data.category_code in ("SM", "SW"):
            if "Score" in df.columns:
                df = df[df["Score"] != ""].copy()
        else:
            df = df.head(50)

        # Load runner data for team categories so we can attach tooltips
        runner_data: dict[str, dict[str, list[str]]] = {}
        if data.is_team:
            actual_code = data.category_code.removeprefix("Team ")
            runner_data = self._load_runner_data(actual_code)

        table_html = self._build_table(df, data, runner_data)

        return (
            f'      <section id="{section_id}" class="category-section">\n'
            f"        <h2>{html.escape(data.title)}</h2>\n"
            f'        <div class="table-wrapper">\n'
            f"{table_html}\n"
            f"        </div>\n"
            f"      </section>"
        )

    def _build_table(
        self,
        df: pd.DataFrame,
        data: CategoryDisplayData,
        runner_data: dict[str, dict[str, list[str]]],
    ) -> str:
        """Build an HTML table for a category DataFrame."""
        if df.empty:
            return '          <p class="no-data">No data available.</p>'

        round_cols = [c for c in df.columns if c in _DISPLAY_TO_ROUND_NUM]
        score_col_present = "Score" in df.columns

        lines: list[str] = ["          <table>", "            <thead>", "              <tr>"]

        for col in df.columns:
            lines.append(f"                <th>{html.escape(str(col))}</th>")
        lines.append("              </tr>")
        lines.append("            </thead>")
        lines.append("            <tbody>")

        for _, row in df.iterrows():
            team_name = str(row.get("Team", "")) if data.is_team else ""
            lines.append("              <tr>")
            for col in df.columns:
                cell_value = self._format_cell(row[col])
                escaped = html.escape(cell_value)

                extra_attrs = ""
                extra_class = ""

                if data.is_team and team_name:
                    tooltip_content = ""

                    if col in round_cols and team_name in runner_data:
                        runners = runner_data[team_name].get(col, [])
                        if runners:
                            tooltip_content = self._round_tooltip(col, runners)

                    elif col == "Score" and score_col_present and team_name in runner_data:
                        tooltip_content = self._total_score_tooltip(runner_data[team_name])

                    if tooltip_content:
                        safe_tooltip = html.escape(tooltip_content, quote=True)
                        extra_attrs = f' data-tooltip="{safe_tooltip}"'
                        extra_class = " has-tooltip"

                is_score_col = col in (*round_cols, "Score")
                td_class = f'class="score-col{extra_class}"' if is_score_col else ""
                td_open = f"<td {td_class}{extra_attrs}>" if td_class or extra_attrs else "<td>"
                lines.append(f"                {td_open}{escaped}</td>")

            lines.append("              </tr>")

        lines.append("            </tbody>")
        lines.append("          </table>")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Tooltip content helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _round_tooltip(round_col: str, runners: list[str]) -> str:
        """Format tooltip content for a single-round team score cell."""
        runner_list = "\n".join(f"• {r}" for r in runners)
        return f"{round_col} contributors:\n{runner_list}"

    @staticmethod
    def _total_score_tooltip(round_runners: dict[str, list[str]]) -> str:
        """Format tooltip content for the total score cell.

        Shows all rounds that have runner data, each with its athletes.
        """
        if not round_runners:
            return ""
        parts: list[str] = []
        for round_col in sorted(round_runners):
            runners = round_runners[round_col]
            runner_list = ", ".join(runners)
            parts.append(f"{round_col}: {runner_list}")
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Cell formatting helper (mirrors PdfOutputGenerator._format_cell)
    # ------------------------------------------------------------------

    @staticmethod
    def _format_cell(value) -> str:
        """Format a single cell value for HTML display."""
        if pd.isna(value):
            return ""
        try:
            num = float(value)
            return str(int(num)) if num == int(num) else str(value)
        except (ValueError, TypeError):
            return str(value)


# ---------------------------------------------------------------------------
# Embedded CSS
# ---------------------------------------------------------------------------

_CSS = """
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: Arial, Helvetica, sans-serif;
      font-size: 14px;
      background: #f5f5f5;
      color: #222;
    }

    /* ---- Layout ---- */
    .page-wrapper {
      display: flex;
      min-height: 100vh;
    }

    .sidebar {
      width: 220px;
      flex-shrink: 0;
      background: #2c3e50;
      color: #ecf0f1;
      position: sticky;
      top: 0;
      height: 100vh;
      overflow-y: auto;
    }

    .sidebar-header {
      padding: 16px;
      background: #1a252f;
      font-weight: bold;
      font-size: 13px;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }

    .sidebar nav ul {
      list-style: none;
      padding: 8px 0;
    }

    .sidebar nav ul li a {
      display: block;
      padding: 8px 16px;
      color: #bdc3c7;
      text-decoration: none;
      font-size: 13px;
      transition: background 0.15s, color 0.15s;
    }

    .sidebar nav ul li a:hover {
      background: #34495e;
      color: #ffffff;
    }

    .content {
      flex: 1;
      padding: 24px 32px;
      overflow-x: auto;
    }

    /* ---- Page header ---- */
    .page-header {
      margin-bottom: 24px;
    }

    .page-header h1 {
      font-size: 22px;
      color: #2c3e50;
      border-bottom: 2px solid #2c3e50;
      padding-bottom: 8px;
    }

    /* ---- Category sections ---- */
    .category-section {
      margin-bottom: 40px;
    }

    .category-section h2 {
      font-size: 17px;
      color: #2c3e50;
      margin-bottom: 10px;
      padding: 6px 0 6px 10px;
      border-left: 4px solid #2980b9;
      background: #ecf0f1;
    }

    .table-wrapper {
      overflow-x: auto;
    }

    .no-data {
      color: #888;
      font-style: italic;
      padding: 8px 0;
    }

    /* ---- Tables ---- */
    table {
      border-collapse: collapse;
      width: auto;
      min-width: 400px;
      background: #ffffff;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    thead tr {
      background: #2c3e50;
      color: #ffffff;
    }

    th {
      padding: 8px 12px;
      text-align: center;
      font-size: 12px;
      font-weight: bold;
      white-space: nowrap;
      letter-spacing: 0.03em;
    }

    td {
      padding: 6px 12px;
      border-bottom: 1px solid #e8e8e8;
      white-space: nowrap;
    }

    tbody tr:nth-child(even) {
      background: #f9f9f9;
    }

    tbody tr:hover {
      background: #eaf4fb;
    }

    /* First column (Pos) */
    td:first-child, th:first-child {
      text-align: center;
      width: 40px;
    }

    /* Name / Team / Club columns */
    td:nth-child(2) {
      text-align: left;
      max-width: 220px;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* Score and round columns */
    .score-col {
      text-align: center;
      font-variant-numeric: tabular-nums;
    }

    /* Cells with an available tooltip */
    .has-tooltip {
      cursor: help;
      text-decoration: underline dotted #2980b9;
      color: #2471a3;
    }

    .has-tooltip:hover {
      color: #1a5276;
    }

    /* ---- Floating tooltip ---- */
    .tooltip {
      position: absolute;
      z-index: 9999;
      background: #2c3e50;
      color: #ecf0f1;
      border-radius: 6px;
      padding: 10px 14px;
      font-size: 13px;
      line-height: 1.6;
      white-space: pre-line;
      max-width: 340px;
      pointer-events: none;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
"""

# ---------------------------------------------------------------------------
# Embedded JavaScript
# ---------------------------------------------------------------------------

_JS = """
  (function () {
    var tooltip = document.getElementById('tooltip');
    var OFFSET_X = 16;
    var OFFSET_Y = 12;

    function showTooltip(e) {
      var content = this.getAttribute('data-tooltip');
      if (!content) return;
      tooltip.textContent = content;
      tooltip.style.display = 'block';
      tooltip.setAttribute('aria-hidden', 'false');
      positionTooltip(e);
    }

    function moveTooltip(e) {
      positionTooltip(e);
    }

    function hideTooltip() {
      tooltip.style.display = 'none';
      tooltip.setAttribute('aria-hidden', 'true');
    }

    function positionTooltip(e) {
      var x = e.pageX + OFFSET_X;
      var y = e.pageY + OFFSET_Y;
      // Keep tooltip within viewport horizontally
      var maxX = window.scrollX + window.innerWidth - tooltip.offsetWidth - 8;
      if (x > maxX) x = e.pageX - tooltip.offsetWidth - OFFSET_X;
      tooltip.style.left = x + 'px';
      tooltip.style.top  = y + 'px';
    }

    document.querySelectorAll('[data-tooltip]').forEach(function (el) {
      el.addEventListener('mouseenter', showTooltip);
      el.addEventListener('mousemove',  moveTooltip);
      el.addEventListener('mouseleave', hideTooltip);
      el.addEventListener('focus',      showTooltip);
      el.addEventListener('blur',       hideTooltip);
    });
  }());
"""
