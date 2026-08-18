#!/usr/bin/env python3
import os
import sys
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Any

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

GITHUB_USERNAME = "SyntX34"
OUTPUT_PATH = "lang-stats.svg"

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

THEME = {
    "bg_start": "#0f0f17",
    "bg_mid": "#181825",
    "bg_end": "#11111b",
    "card_border": "#313244",
    "text_primary": "#cdd6f4",
    "text_muted": "#6c7086",
    "accent_pink": "#f5c2e7",
    "accent_blue": "#89b4fa",
    "accent_mauve": "#cba6f7",
    "accent_green": "#a6e3a1",
    "accent_yellow": "#f9e2af",
    "bar_track": "#232336",
}


def get_github_token() -> str:
    return (
        os.environ.get("METRICS_TOKEN")
        or os.environ.get("GH_PAT")
        or os.environ.get("GITHUB_TOKEN")
        or ""
    )


def fetch_all_repos(username: str, token: str) -> Tuple[List[Dict[str, Any]], int, int]:
    repos = []
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    page = 1
    has_user_endpoint = bool(token)

    while True:
        if has_user_endpoint:
            url = f"https://api.github.com/user/repos?page={page}&per_page=100&affiliation=owner&sort=updated"
        else:
            url = f"https://api.github.com/users/{username}/repos?page={page}&per_page=100&sort=updated"

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code in (401, 403) and has_user_endpoint:
                has_user_endpoint = False
                page = 1
                continue
            if resp.status_code != 200:
                break
            data = resp.json()
            if not data:
                break
            repos.extend(data)
            page += 1
        except Exception:
            break

    public_count = 0
    private_count = 0
    filtered = []

    for r in repos:
        if r.get("private", False):
            private_count += 1
        else:
            public_count += 1

        if not r.get("fork") and not r.get("archived") and r.get("name") != username:
            filtered.append(r)

    return filtered, public_count, private_count


def fetch_languages(repos: List[Dict[str, Any]], token: str) -> Dict[str, int]:
    lang_data: Dict[str, int] = {}
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    for repo in repos:
        lang_url = repo.get("languages_url")
        if not lang_url:
            continue
        try:
            resp = requests.get(lang_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                for lang, bytes_count in resp.json().items():
                    lang_data[lang] = lang_data.get(lang, 0) + bytes_count
        except Exception:
            pass

    return lang_data


def sort_languages(lang_data: Dict[str, int]) -> List[Tuple[str, int, float]]:
    total = sum(lang_data.values())
    if total == 0:
        return []
    sorted_items = sorted(lang_data.items(), key=lambda x: x[1], reverse=True)
    return [(lang, b, (b / total) * 100) for lang, b in sorted_items]


def get_language_color(lang: str) -> str:
    return LANGUAGE_COLORS.get(lang, "#89b4fa")


def format_bytes(bytes_count: int) -> str:
    if bytes_count >= 1_073_741_824:
        return f"{bytes_count / 1_073_741_824:.2f} GB"
    elif bytes_count >= 1_048_576:
        return f"{bytes_count / 1_048_576:.1f} MB"
    elif bytes_count >= 1024:
        return f"{bytes_count / 1024:.0f} KB"
    return f"{bytes_count} B"


def generate_svg(
    languages: List[Tuple[str, int, float]],
    public_count: int,
    private_count: int,
) -> str:
    displayed_langs = languages[:8]
    card_width = 650
    stack_bar_height = 14
    padding = 24

    total_bytes = sum(b for _, b, _ in languages)
    total_repos = public_count + private_count

    stack_segments = []
    curr_x = padding
    stack_width = card_width - (padding * 2)

    for lang, _, pct in displayed_langs:
        seg_w = (pct / 100) * stack_width
        if seg_w > 0.5:
            color = get_language_color(lang)
            stack_segments.append(
                f'<rect x="{curr_x:.1f}" y="88" width="{seg_w:.1f}" height="{stack_bar_height}" fill="{color}" rx="2"/>'
            )
            curr_x += seg_w

    stack_xml = "\n    ".join(stack_segments)

    col_width = (card_width - (padding * 2) - 16) / 2
    row_elements = []
    y_start = 122

    for i, (lang, bytes_count, pct) in enumerate(displayed_langs):
        col = i % 2
        row_idx = i // 2
        x_base = padding + col * (col_width + 16)
        y_pos = y_start + (row_idx * 40)
        color = get_language_color(lang)

        row_elements.append(
            f'<rect x="{x_base:.1f}" y="{y_pos - 10}" width="{col_width:.1f}" height="32" rx="8" fill="#181825" stroke="#313244" stroke-width="0.75"/>'
        )
        row_elements.append(
            f'<circle cx="{x_base + 12:.1f}" cy="{y_pos + 6}" r="4.5" fill="{color}"/>'
        )
        row_elements.append(
            f'<text x="{x_base + 24:.1f}" y="{y_pos + 10}" font-family="Outfit, -apple-system, BlinkMacSystemFont, sans-serif" font-size="12.5" font-weight="700" fill="{THEME["text_primary"]}">{lang}</text>'
        )
        row_elements.append(
            f'<text x="{x_base + col_width - 65:.1f}" y="{y_pos + 10}" font-family="JetBrains Mono, monospace" font-size="12" font-weight="700" fill="{THEME["accent_pink"]}">{pct:.1f}%</text>'
        )
        bytes_str = format_bytes(bytes_count)
        row_elements.append(
            f'<text x="{x_base + col_width - 10:.1f}" y="{y_pos + 10}" text-anchor="end" font-family="JetBrains Mono, monospace" font-size="10" fill="{THEME["text_muted"]}">{bytes_str}</text>'
        )

    rows_xml = "\n    ".join(row_elements)
    calc_rows = (len(displayed_langs) + 1) // 2
    final_height = y_start + (calc_rows * 40) + 38

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {card_width} {final_height}" width="100%" height="{final_height}" style="max-width: {card_width}px; background: transparent;">
  <defs>
    <linearGradient id="langCardBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{THEME['bg_start']}" stop-opacity="0.95"/>
      <stop offset="50%" stop-color="{THEME['bg_mid']}" stop-opacity="0.98"/>
      <stop offset="100%" stop-color="{THEME['bg_end']}" stop-opacity="0.95"/>
    </linearGradient>

    <linearGradient id="langBorderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{THEME['accent_blue']}" stop-opacity="0.8"/>
      <stop offset="50%" stop-color="{THEME['accent_mauve']}" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="{THEME['accent_pink']}" stop-opacity="0.8"/>
    </linearGradient>

    <style>
      @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700&amp;family=Outfit:wght@500;600;700;800&amp;display=swap');
      .font-title {{ font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
      .font-mono {{ font-family: 'JetBrains Mono', monospace; }}
    </style>
  </defs>

  <rect x="2" y="2" width="{card_width - 4}" height="{final_height - 4}" rx="16" ry="16" fill="url(#langCardBg)" stroke="url(#langBorderGrad)" stroke-width="1.5"/>
  <rect x="10" y="16" width="3" height="{final_height - 32}" rx="1.5" fill="{THEME['accent_mauve']}"/>

  <g transform="translate({padding}, 32)">
    <text class="font-title" font-size="18" font-weight="800" fill="{THEME['text_primary']}">💻 Language Ecosystem</text>
    <text class="font-title" font-size="11.5" font-weight="500" fill="{THEME['text_muted']}" y="18">Aggregated bytes across repositories</text>
  </g>

  <g transform="translate({card_width - padding - 230}, 24)">
    <rect x="0" y="0" width="105" height="24" rx="6" fill="#1e1e2e" stroke="{THEME['card_border']}" stroke-width="1"/>
    <circle cx="12" cy="12" r="3.5" fill="{THEME['accent_green']}"/>
    <text class="font-mono" font-size="10.5" font-weight="700" fill="{THEME['text_primary']}" x="22" y="16">Public: {public_count}</text>

    <rect x="115" y="0" width="115" height="24" rx="6" fill="#1e1e2e" stroke="{THEME['card_border']}" stroke-width="1"/>
    <circle cx="127" cy="12" r="3.5" fill="{THEME['accent_yellow']}"/>
    <text class="font-mono" font-size="10.5" font-weight="700" fill="{THEME['text_primary']}" x="137" y="16">Private: {private_count}</text>
  </g>

  <rect x="{padding}" y="88" width="{stack_width}" height="{stack_bar_height}" rx="4" fill="{THEME['bar_track']}"/>
  <g>
    {stack_xml}
  </g>

  <g>
    {rows_xml}
  </g>

  <line x1="{padding}" y1="{final_height - 24}" x2="{card_width - padding}" y2="{final_height - 24}" stroke="{THEME['card_border']}" stroke-width="0.75" opacity="0.6"/>
  <text class="font-title" font-size="10" fill="{THEME['text_muted']}" x="{padding}" y="{final_height - 10}">
    Analyzed {format_bytes(total_bytes)} of code across {total_repos} repositories
  </text>
  <text class="font-mono" font-size="10" font-weight="700" fill="{THEME['accent_blue']}" x="{card_width - padding}" y="{final_height - 10}" text-anchor="end">
    SyntX34
  </text>
</svg>"""


def main():
    token = get_github_token()
    repos, public_count, private_count = fetch_all_repos(GITHUB_USERNAME, token)

    if not repos:
        svg = generate_svg([], public_count, private_count)
        Path(OUTPUT_PATH).write_text(svg, encoding="utf-8")
        return

    lang_data = fetch_languages(repos, token)
    sorted_langs = sort_languages(lang_data)
    svg = generate_svg(sorted_langs, public_count, private_count)
    Path(OUTPUT_PATH).write_text(svg, encoding="utf-8")
    print("Done")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
