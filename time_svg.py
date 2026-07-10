#!/usr/bin/env python3
"""
Digital clock SVG generator - Shows current Nepal Standard Time (NPT, UTC+5:45)
Generates a beautiful clock SVG that gets committed to the repo via GitHub Actions.
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path

# Nepal Standard Time is UTC+5:45
NPT_OFFSET = timedelta(hours=5, minutes=45)
NPT_TZ = timezone(NPT_OFFSET)

OUTPUT_PATH = "nepal-clock.svg"

# Color scheme matching the tokyonight theme
COLORS = {
    "bg": "#1e1e2e",
    "text_primary": "#f5c2e7",  # pink
    "text_secondary": "#89b4fa",  # blue
    "text_accent": "#cba6f7",    # mauve
}

def get_nepal_time() -> datetime:
    """Get current Nepal Standard Time."""
    return datetime.now(NPT_TZ)


def format_digital_time(dt: datetime) -> tuple:
    """Format time as HH:MM:SS and return components."""
    hour = dt.strftime("%H")
    minute = dt.strftime("%M")
    second = dt.strftime("%S")
    ampm = dt.strftime("%p")
    return hour, minute, second, ampm


def format_date(dt: datetime) -> str:
    """Format date as e.g. 'Friday, July 10, 2026'"""
    return dt.strftime("%A, %B %d, %Y")


def generate_clock_svg() -> str:
    """Generate a clean digital clock SVG with Nepal time."""
    now = get_nepal_time()
    _, minute, second, ampm = format_digital_time(now)
    date_str = format_date(now)

    # 12-hour format (without leading zero, e.g. "1" instead of "01")
    h12 = now.strftime("%I").lstrip("0") or "12"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="420" height="130" viewBox="0 0 420 130">
  <defs>
    <style>
      .bg {{ fill: {COLORS['bg']}; }}
      .time {{ font-family: 'JetBrains Mono', 'Courier New', monospace; font-size: 52px; font-weight: 700; fill: {COLORS['text_primary']}; }}
      .secs {{ font-family: 'JetBrains Mono', 'Courier New', monospace; font-size: 52px; font-weight: 600; fill: {COLORS['text_accent']}; }}
      .ampm {{ font-family: 'JetBrains Mono', 'Courier New', monospace; font-size: 22px; font-weight: 700; fill: {COLORS['text_secondary']}; }}
      .date {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 14px; fill: {COLORS['text_secondary']}; }}
      .label {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 11px; fill: #6c7086; }}
    </style>
  </defs>
  
  <!-- Background -->
  <rect class="bg" x="0" y="0" width="420" height="130" rx="12" ry="12" />
  
  <!-- Nepal flag indicator -->
  <rect x="0" y="0" width="6" height="130" rx="3" ry="3" fill="{COLORS['text_primary']}" opacity="0.6"/>
  
  <!-- Top row: Timezone label left, LIVE indicator right -->
  <text class="label" x="20" y="22">Nepal Standard Time (UTC+5:45)</text>
  <circle cx="370" cy="18" r="4" fill="#a6e3a1" opacity="0.9">
    <animate attributeName="opacity" values="0.3;1;0.3" dur="2s" repeatCount="indefinite" />
  </circle>
  <text class="label" x="349" y="22">LIVE</text>
  
  <!-- Main digital time: HH:MM:SS AM/PM -->
  <!-- HH:MM (large) -->
  <text class="time" x="20" y="80">{h12}:{minute}</text>
  <!-- :SS (same size as time, different color) -->
  <text class="secs" x="228" y="80">:{second}</text>
  <!-- AM/PM (smaller, raised higher to align with top of digits) -->
  <text class="ampm" x="310" y="68">{ampm}</text>
  
  <!-- Bottom row: Date -->
  <text class="date" x="20" y="112">{date_str}</text>
  
  <!-- Nepal flag emoji -->
  <text font-size="20" x="375" y="108">🇳🇵</text>
</svg>"""

    return svg


def save_svg(svg_content: str, path: str = OUTPUT_PATH):
    """Save SVG content to file."""
    output_path = Path(path)
    output_path.write_text(svg_content, encoding="utf-8")
    print(f"✅ Clock SVG saved to {output_path.resolve()}")
    print(f"   Time: {get_nepal_time().strftime('%I:%M:%S %p')}")
    print(f"   Date: {format_date(get_nepal_time())}")


if __name__ == "__main__":
    try:
        svg = generate_clock_svg()
        save_svg(svg)
        print("✨ Clock updated successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
