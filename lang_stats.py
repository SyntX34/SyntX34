#!/usr/bin/env python3
"""
Language Statistics SVG Generator
Fetches language data from all user repos via GitHub API and generates
a beautiful SVG showing language distribution with colored progress bars,
percentages, and byte counts.

Data source: GitHub API /repos/{owner}/{repo}/languages
This returns bytes of code per language for each repo, which is then
aggregated across ALL repos (not just the most recent).
"""

import os
import requests
from pathlib import Path
from typing import Dict, List, Tuple

GITHUB_USERNAME = "SyntX34"
OUTPUT_PATH = "lang-stats.svg"

# Official GitHub language colors
LANGUAGE_COLORS = {
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Python": "#3572A5",
    "C#": "#178600",
    "C++": "#f34b7d",
    "C": "#555555",
    "PHP": "#4F5D95",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "SCSS": "#c6538c",
    "Less": "#1d365d",
    "CMake": "#DA3434",
    "Makefile": "#427819",
    "Shell": "#89e051",
    "PowerShell": "#012456",
    "Batchfile": "#C1F12E",
    "Dockerfile": "#384d54",
    "Java": "#b07219",
    "Ruby": "#701516",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "Dart": "#00B4AB",
    "Lua": "#000080",
    "Perl": "#0298c3",
    "Haskell": "#5e5086",
    "R": "#198CE7",
    "Objective-C": "#438eff",
    "Vue": "#41b883",
    "Svelte": "#ff3e00",
    "Scala": "#c22d40",
    "Elixir": "#6e4a7e",
    "Clojure": "#db5855",
    "Erlang": "#B83998",
    "SourcePawn": "#f69e1d",
    "HLSL": "#aabbcc",
    "GLSL": "#5686a5",
    "ShaderLab": "#222c37",
    "ASP.NET": "#9400ff",
    "Visual Basic": "#945db7",
    "F#": "#b845fc",
    "CoffeeScript": "#244776",
    "TeX": "#3D6117",
    "Markdown": "#083fa1",
    "YAML": "#cb171e",
    "JSON": "#292929",
    "XML": "#0060ac",
    "SQL": "#e38c00",
    "Assembly": "#6E4C13",
    "Solidity": "#AA6746",
    "Jupyter Notebook": "#DA5B0B",
}

# TokyoNight color scheme (matching README)
BG_COLOR = "#1e1e2e"
CARD_BG = "#181825"
TEXT_PRIMARY = "#cdd6f4"
TEXT_SECONDARY = "#a6adc8"
TEXT_MUTED = "#6c7086"
ACCENT_PINK = "#f5c2e7"
ACCENT_BLUE = "#89b4fa"
ACCENT_MAUVE = "#cba6f7"
ACCENT_GREEN = "#a6e3a1"
BORDER_COLOR = "#313244"
LABEL_COLOR = "#45475a"


def get_github_token() -> str:
    """Get GitHub token from environment."""
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("METRICS_TOKEN") or ""


def fetch_all_repos(username: str, token: str) -> List[Dict]:
    """Fetch all non-fork, non-archived repos for a user."""
    repos = []
    page = 1
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    print(f"📦 Fetching repos for {username}...")
    while True:
        url = f"https://api.github.com/users/{username}/repos?page={page}&per_page=100&sort=updated"
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"⚠️  API error: {resp.status_code} - {resp.text[:100]}")
            break
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        page += 1

    # Filter: exclude forks, archived, and the profile repo itself
    filtered = [
        r for r in repos
        if not r.get("fork") and not r.get("archived") and r["name"] != username
    ]
    print(f"✅ Found {len(filtered)} repos (filtered from {len(repos)})")
    return filtered


def fetch_languages(repos: List[Dict], token: str) -> Dict[str, int]:
    """Fetch language breakdown for each repo and aggregate."""
    lang_data: Dict[str, int] = {}
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    for repo in repos:
        name = repo["name"]
        lang_url = repo["languages_url"]
        try:
            resp = requests.get(lang_url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    langs = ", ".join(data.keys())
                    print(f"  📁 {name}: {langs}")
                    for lang, bytes_count in data.items():
                        lang_data[lang] = lang_data.get(lang, 0) + bytes_count
                else:
                    print(f"  📁 {name}: (no language data)")
            else:
                print(f"  ⚠️  {name}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")

    return lang_data


def sort_languages(lang_data: Dict[str, int]) -> List[Tuple[str, int, float]]:
    """Sort languages by bytes descending, return list of (name, bytes, percentage)."""
    total = sum(lang_data.values())
    if total == 0:
        return []

    sorted_items = sorted(lang_data.items(), key=lambda x: x[1], reverse=True)
    result = []
    for lang, bytes_count in sorted_items:
        pct = (bytes_count / total) * 100
        result.append((lang, bytes_count, pct))
    return result


def get_language_color(lang: str) -> str:
    """Get the official GitHub color for a language."""
    return LANGUAGE_COLORS.get(lang, "#6c7086")


def format_bytes(bytes_count: int) -> str:
    """Format byte count to human-readable string."""
    if bytes_count >= 1_000_000:
        return f"{bytes_count / 1_000_000:.1f}MB"
    elif bytes_count >= 1_000:
        return f"{bytes_count / 1_000:.0f}KB"
    else:
        return f"{bytes_count}B"


def generate_svg(languages: List[Tuple[str, int, float]]) -> str:
    """Generate a beautiful SVG showing language distribution."""
    max_langs = 10
    languages = languages[:max_langs]

    rows = len(languages)
    row_height = 40
    header_height = 50
    padding = 20
    bar_width = 260
    label_width = 140
    dot_size = 10
    total_width = 480
    total_height = header_height + rows * row_height + padding * 2

    # Build rows
    rows_svg = []
    y_start = header_height

    for i, (lang, bytes_count, pct) in enumerate(languages):
        y = y_start + i * row_height
        color = get_language_color(lang)

        # Row background (alternating)
        if i % 2 == 0:
            rows_svg.append(
                f'  <rect x="0" y="{y - 8}" width="{total_width}" height="{row_height}" '
                f'rx="6" ry="6" fill="{CARD_BG}" opacity="0.5"/>'
            )

        # Colored dot
        rows_svg.append(
            f'  <circle cx="30" cy="{y + 8}" r="{dot_size // 2}" fill="{color}"/>'
        )

        # Language name
        rows_svg.append(
            f'  <text x="45" y="{y + 12}" font-family="-apple-system, BlinkMacSystemFont, '
            f'\'Segoe UI\', Helvetica, Arial, sans-serif" font-size="13" '
            f'font-weight="600" fill="{TEXT_PRIMARY}">{lang}</text>'
        )

        # Progress bar background
        bar_x = 160
        bar_y = y
        bar_h = 6
        rows_svg.append(
            f'  <rect x="{bar_x}" y="{bar_y + 2}" width="{bar_width}" height="{bar_h}" '
            f'rx="3" ry="3" fill="{BORDER_COLOR}"/>'
        )

        # Progress bar fill
        fill_width = int(bar_width * pct / 100)
        if fill_width > 0:
            rows_svg.append(
                f'  <rect x="{bar_x}" y="{bar_y + 2}" width="{fill_width}" '
                f'height="{bar_h}" rx="3" ry="3" fill="{color}" opacity="0.9"/>'
            )

        # Percentage text
        pct_text = f"{pct:.1f}%"
        rows_svg.append(
            f'  <text x="{bar_x + bar_width + 10}" y="{y + 11}" '
            f'font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif" '
            f'font-size="13" font-weight="700" fill="{ACCENT_PINK}">{pct_text}</text>'
        )

        # Bytes text
        bytes_text = format_bytes(bytes_count)
        rows_svg.append(
            f'  <text x="{bar_x + bar_width + 70}" y="{y + 11}" '
            f'font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif" '
            f'font-size="11" fill="{TEXT_MUTED}">{bytes_text}</text>'
        )

    rows_xml = "\n".join(rows_svg)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{total_height + 20}" viewBox="0 0 {total_width} {total_height + 20}">
  <defs>
    <style>
      .header {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; }}
    </style>
  </defs>

  <!-- Background -->
  <rect x="0" y="0" width="{total_width}" height="{total_height + 20}" rx="12" ry="12" fill="{BG_COLOR}"/>

  <!-- Header -->
  <text x="20" y="28" class="header" font-size="16" font-weight="700" fill="{TEXT_PRIMARY}">💻 Most Used Languages</text>
  <text x="20" y="44" class="header" font-size="11" fill="{TEXT_MUTED}">Based on all repositories — updated via GitHub Actions</text>

  <!-- Separator line -->
  <line x1="20" y1="{y_start - 2}" x2="{total_width - 20}" y2="{y_start - 2}" stroke="{BORDER_COLOR}" stroke-width="1"/>

  <!-- Language rows -->
{rows_xml}

  <!-- Footer with total count -->
  <text x="20" y="{total_height + 10}" class="header" font-size="10" fill="{TEXT_MUTED}">
    Total languages: {len(languages)} · Data sourced from GitHub API (bytes of code per repository)
  </text>
</svg>"""

    return svg


def main():
    """Main function."""
    print("=" * 55)
    print("   Language Statistics SVG Generator")
    print("=" * 55)

    token = get_github_token()
    if token:
        print("🔑 Using GitHub token for API requests")
    else:
        print("⚠️  No token found. Rate limits will be low (60 req/hr)")

    # Fetch repos
    repos = fetch_all_repos(GITHUB_USERNAME, token)
    if not repos:
        print("❌ No repositories found. Exiting.")
        # Still generate an SVG with a message
        svg = generate_svg([])
        Path(OUTPUT_PATH).write_text(svg, encoding="utf-8")
        print(f"⚠️  Empty SVG written to {OUTPUT_PATH}")
        return

    # Fetch language data
    print(f"\n🔍 Fetching language data for {len(repos)} repos...")
    lang_data = fetch_languages(repos, token)

    if not lang_data:
        print("❌ No language data found. Exiting.")
        svg = generate_svg([])
        Path(OUTPUT_PATH).write_text(svg, encoding="utf-8")
        return

    # Sort and calculate
    sorted_langs = sort_languages(lang_data)

    # Print summary
    print(f"\n📊 Language Summary (Top {len(sorted_langs)}):")
    print("-" * 50)
    total_bytes = sum(v for _, v, _ in sorted_langs)
    for lang, bytes_count, pct in sorted_langs[:10]:
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"  {lang:14s} {bar} {pct:5.1f}%  ({format_bytes(bytes_count)})")
    print("-" * 50)
    print(f"  Total: {format_bytes(total_bytes)} across {len(sorted_langs)} languages")

    # Generate SVG
    print("\n🎨 Generating SVG...")
    svg = generate_svg(sorted_langs)

    # Save
    output_path = Path(OUTPUT_PATH)
    output_path.write_text(svg, encoding="utf-8")
    print(f"✅ Language stats SVG saved to {output_path.resolve()}")

    # Verify
    file_size = output_path.stat().st_size
    print(f"   File size: {file_size:,} bytes")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
