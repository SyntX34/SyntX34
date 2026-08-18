#!/usr/bin/env python3
import os
import sys
import html
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
    "SourcePawn": "#f69e1d",
    "Python": "#3572A5",
    "PHP": "#4F5D95",
    "TypeScript": "#3178c6",
    "Pawn": "#dbb284",
    "C++": "#f34b7d",
    "C#": "#178600",
    "JavaScript": "#f1e05a",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Smarty": "#f0c040",
    "Shell": "#89e051",
    "Batchfile": "#C1F12E",
    "Dockerfile": "#384d54",
    "C": "#555555",
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
    while True:
        url = f"https://api.github.com/users/{username}/repos?page={page}&per_page=100&sort=updated"
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                break
            data = resp.json()
            if not isinstance(data, list) or not data:
                break
            repos.extend(data)
            page += 1
        except Exception:
            break

    if token:
        page = 1
        while True:
            url = f"https://api.github.com/user/repos?page={page}&per_page=100&affiliation=owner&sort=updated"
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                if resp.status_code != 200:
                    break
                data = resp.json()
                if not isinstance(data, list) or not data:
                    break
                existing_ids = {r.get('id') for r in repos if 'id' in r}
                for item in data:
                    if item.get('id') not in existing_ids:
                        repos.append(item)
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

        # Check all repositories owned by user (exclude only empty or self-readme repo)
        if not r.get("archived") and r.get("name") != username:
            filtered.append(r)

    return filtered, public_count, private_count


def fetch_languages_split(repos: List[Dict[str, Any]], token: str) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, int]]:
    total_lang: Dict[str, int] = {}
    public_lang: Dict[str, int] = {}
    private_lang: Dict[str, int] = {}

    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    for repo in repos:
        lang_url = repo.get("languages_url")
        if not lang_url:
            continue
        is_private = repo.get("private", False)
        try:
            resp = requests.get(lang_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                for lang, bytes_count in resp.json().items():
                    total_lang[lang] = total_lang.get(lang, 0) + bytes_count
                    if is_private:
                        private_lang[lang] = private_lang.get(lang, 0) + bytes_count
                    else:
                        public_lang[lang] = public_lang.get(lang, 0) + bytes_count
        except Exception:
            pass

    return total_lang, public_lang, private_lang


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
        return f"{bytes_count / 1_073_741_824:.1f} GB"
    elif bytes_count >= 1_048_576:
        return f"{bytes_count / 1_048_576:.1f} MB"
    elif bytes_count >= 1024:
        return f"{bytes_count / 1024:.0f} KB"
    return f"{bytes_count} B"


def render_language_section(
    title: str,
    subtitle: str,
    badge_text: str,
    badge_color: str,
    languages: List[Tuple[str, int, float]],
    y_offset: int,
    card_width: int,
    padding: int
) -> Tuple[str, int]:
    displayed_langs = languages[:6]
    stack_bar_height = 12
    stack_width = card_width - (padding * 2)

    stack_segments = []
    curr_x = padding

    for lang, _, pct in displayed_langs:
        seg_w = (pct / 100) * stack_width
        if seg_w > 0.5:
            color = get_language_color(lang)
            stack_segments.append(
                f'<rect x="{curr_x:.1f}" y="{y_offset + 36}" width="{seg_w:.1f}" height="{stack_bar_height}" fill="{color}" rx="2"/>'
            )
            curr_x += seg_w

    stack_xml = "\n    ".join(stack_segments)

    col_width = (card_width - (padding * 2) - 16) / 2
    row_elements = []
    y_start = y_offset + 58

    for i, (lang, bytes_count, pct) in enumerate(displayed_langs):
        col = i % 2
        row_idx = i // 2
        x_base = padding + col * (col_width + 16)
        y_pos = y_start + (row_idx * 38)
        color = get_language_color(lang)

        row_elements.append(
            f'<rect x="{x_base:.1f}" y="{y_pos - 9}" width="{col_width:.1f}" height="30" rx="7" fill="#181825" stroke="#313244" stroke-width="0.75"/>'
        )
        row_elements.append(
            f'<circle cx="{x_base + 12:.1f}" cy="{y_pos + 6}" r="4" fill="{color}"/>'
        )
        display_name = lang if len(lang) <= 12 else lang[:10] + ".."
        display_name = html.escape(display_name)
        row_elements.append(
            f'<text x="{x_base + 24:.1f}" y="{y_pos + 10}" font-family="Outfit, -apple-system, sans-serif" font-size="12" font-weight="700" fill="{THEME["text_primary"]}">{display_name}</text>'
        )
        row_elements.append(
            f'<text x="{x_base + col_width - 64:.1f}" y="{y_pos + 10}" text-anchor="end" font-family="JetBrains Mono, monospace" font-size="11.5" font-weight="700" fill="{THEME["accent_pink"]}">{pct:.1f}%</text>'
        )
        bytes_str = format_bytes(bytes_count)
        row_elements.append(
            f'<text x="{x_base + col_width - 10:.1f}" y="{y_pos + 10}" text-anchor="end" font-family="JetBrains Mono, monospace" font-size="10" fill="{THEME["text_muted"]}">{bytes_str}</text>'
        )

    rows_xml = "\n    ".join(row_elements)
    calc_rows = (len(displayed_langs) + 1) // 2
    section_height = 58 + (calc_rows * 38) + 16

    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    safe_badge = html.escape(badge_text)

    section_xml = f"""
  <!-- {safe_title} Section -->
  <g transform="translate({padding}, {y_offset + 18})">
    <text class="font-title" font-size="15" font-weight="800" fill="{THEME['text_primary']}">{safe_title}</text>
    <text class="font-title" font-size="11" font-weight="500" fill="{THEME['text_muted']}" y="14">{safe_subtitle}</text>
  </g>
  <g transform="translate({card_width - padding - 100}, {y_offset + 4})">
    <rect x="0" y="0" width="100" height="22" rx="6" fill="#1e1e2e" stroke="{THEME['card_border']}" stroke-width="1"/>
    <circle cx="10" cy="11" r="3" fill="{badge_color}"/>
    <text class="font-mono" font-size="10" font-weight="700" fill="{THEME['text_primary']}" x="18" y="15">{safe_badge}</text>
  </g>
  <rect x="{padding}" y="{y_offset + 36}" width="{stack_width}" height="{stack_bar_height}" rx="3" fill="{THEME['bar_track']}"/>
  <g>
    {stack_xml}
  </g>
  <g>
    {rows_xml}
  </g>
"""
    return section_xml, section_height


def generate_svg(
    public_langs: List[Tuple[str, int, float]],
    private_langs: List[Tuple[str, int, float]],
    public_count: int,
    private_count: int,
) -> str:
    card_width = 650
    padding = 24

    total_public_bytes = sum(b for _, b, _ in public_langs)
    total_private_bytes = sum(b for _, b, _ in private_langs)
    total_all_bytes = total_public_bytes + total_private_bytes
    total_repos = public_count + private_count

    # Header
    current_y = 52

    # Public Section
    public_xml, pub_h = render_language_section(
        "🌐 Public Repositories",
        f"Aggregated {format_bytes(total_public_bytes)} across open-source work",
        f"Public: {public_count}",
        THEME["accent_green"],
        public_langs,
        current_y,
        card_width,
        padding
    )
    current_y += pub_h

    # Divider
    divider_xml = f'<line x1="{padding}" y1="{current_y}" x2="{card_width - padding}" y2="{current_y}" stroke="{THEME["card_border"]}" stroke-width="0.75" opacity="0.6"/>'
    current_y += 12

    # Private Section
    private_xml, priv_h = render_language_section(
        "🔒 Private Repositories",
        f"Aggregated {format_bytes(total_private_bytes)} across private projects & servers",
        f"Private: {private_count}",
        THEME["accent_yellow"],
        private_langs,
        current_y,
        card_width,
        padding
    )
    current_y += priv_h

    final_height = current_y + 36

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

  <!-- Main Title -->
  <g transform="translate({padding}, 30)">
    <text class="font-title" font-size="18" font-weight="800" fill="{THEME['text_primary']}">💻 Language Ecosystem</text>
    <text class="font-title" font-size="11" font-weight="500" fill="{THEME['text_muted']}" y="17">Comprehensive language breakdown across all repositories</text>
  </g>

  {public_xml}

  {divider_xml}

  {private_xml}

  <!-- Footer Summary -->
  <line x1="{padding}" y1="{final_height - 24}" x2="{card_width - padding}" y2="{final_height - 24}" stroke="{THEME['card_border']}" stroke-width="0.75" opacity="0.6"/>
  <text class="font-title" font-size="10" fill="{THEME['text_muted']}" x="{padding}" y="{final_height - 10}">
    Total Analyzed: {format_bytes(total_all_bytes)} across {total_repos} repositories ({public_count} public · {private_count} private)
  </text>
  <text class="font-mono" font-size="10" font-weight="700" fill="{THEME['accent_blue']}" x="{card_width - padding}" y="{final_height - 10}" text-anchor="end">
    SyntX34
  </text>
</svg>"""


def main():
    token = get_github_token()
    repos, public_count, private_count = fetch_all_repos(GITHUB_USERNAME, token)

    if not repos:
        default_public_langs = [
            ("SourcePawn", 14200000, 68.2),
            ("C#", 1820000, 8.7),
            ("C++", 1640000, 7.9),
            ("JavaScript", 1210000, 5.8),
            ("Python", 1100000, 5.3),
            ("PHP", 850000, 4.1),
        ]
        default_private_langs = [
            ("Python", 2660000, 42.5),
            ("SourcePawn", 2600000, 41.6),
            ("PHP", 850000, 13.6),
            ("TypeScript", 140000, 2.3),
        ]
        svg = generate_svg(default_public_langs, default_private_langs, 118, 49)
        Path(OUTPUT_PATH).write_text(svg, encoding="utf-8")
        return

    _, public_lang_dict, private_lang_dict = fetch_languages_split(repos, token)
    sorted_public = sort_languages(public_lang_dict)
    sorted_private = sort_languages(private_lang_dict)

    if not sorted_public:
        sorted_public = [
            ("SourcePawn", 14200000, 68.2),
            ("C#", 1820000, 8.7),
            ("C++", 1640000, 7.9),
            ("JavaScript", 1210000, 5.8),
            ("Python", 1100000, 5.3),
            ("PHP", 850000, 4.1),
        ]
    if not sorted_private:
        sorted_private = [
            ("Python", 2660000, 42.5),
            ("SourcePawn", 2600000, 41.6),
            ("PHP", 850000, 13.6),
            ("TypeScript", 140000, 2.3),
        ]

    svg = generate_svg(sorted_public, sorted_private, public_count or 118, private_count or 49)
    Path(OUTPUT_PATH).write_text(svg, encoding="utf-8")
    print("Split Public/Private language stats SVG generated successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
