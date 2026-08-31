#!/usr/bin/env python3
import requests
import re
import os
import sys
from datetime import datetime
from typing import List, Dict, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

GITHUB_USERNAME = "SyntX34"
README_PATH = "README.md"
THEME = "tokyonight"

def get_user_repos(username: str) -> List[Dict]:
    repos = []
    page = 1
    headers = {'Accept': 'application/vnd.github.v3+json'}
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('METRICS_TOKEN')
    if token:
        headers['Authorization'] = f'token {token}'
    
    while True:
        url = f"https://api.github.com/users/{username}/repos?page={page}&per_page=100&sort=updated"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            break
        data = response.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    
    return [
        r for r in repos
        if not r.get('fork') and not r.get('archived') and r.get('name') != username
    ]

def get_repo_release_downloads(username: str, repo_name: str, headers: Dict) -> int:
    try:
        url = f"https://api.github.com/repos/{username}/{repo_name}/releases"
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            releases = resp.json()
            total_downloads = 0
            if isinstance(releases, list):
                for rel in releases:
                    for asset in rel.get("assets", []):
                        total_downloads += asset.get("download_count", 0)
            return total_downloads
    except Exception:
        pass
    return 0

def analyze_repositories(repos: List[Dict]) -> Tuple[Dict, Dict, Dict, Dict]:
    if not repos:
        return None, None, None, None
    
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('METRICS_TOKEN')
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        headers['Authorization'] = f'token {token}'

    # Fetch release download counts for repos with releases
    for r in repos:
        r['release_downloads'] = get_repo_release_downloads(GITHUB_USERNAME, r['name'], headers)

    # 1. Most Starred: repo with highest stargazers_count
    sorted_by_stars = sorted(repos, key=lambda x: (x.get('stargazers_count', 0), x.get('forks_count', 0)), reverse=True)
    most_starred = sorted_by_stars[0]

    # 2. Most Active: repo with recent commits / pushed_at timestamp
    sorted_by_activity = sorted(repos, key=lambda x: x.get('pushed_at', x.get('updated_at', '')), reverse=True)
    most_active = sorted_by_activity[0]
    if most_active['name'] == most_starred['name'] and len(sorted_by_activity) > 1:
        most_active = sorted_by_activity[1]

    # 3. Most Popular: highest downloads + forks + stars
    def pop_score(r):
        return (r.get('release_downloads', 0) * 10) + (r.get('forks_count', 0) * 5) + (r.get('stargazers_count', 0) * 2)

    sorted_by_popularity = sorted(repos, key=pop_score, reverse=True)
    most_popular = sorted_by_popularity[0]
    if most_popular['name'] in (most_starred['name'], most_active['name']) and len(sorted_by_popularity) > 1:
        for candidate in sorted_by_popularity:
            if candidate['name'] not in (most_starred['name'], most_active['name']):
                most_popular = candidate
                break

    # 4. Latest Project: most recently created repo
    sorted_by_created = sorted(repos, key=lambda x: x.get('created_at', ''), reverse=True)
    latest = sorted_by_created[0]
    if latest['name'] in (most_starred['name'], most_active['name'], most_popular['name']) and len(sorted_by_created) > 1:
        for candidate in sorted_by_created:
            if candidate['name'] not in (most_starred['name'], most_active['name'], most_popular['name']):
                latest = candidate
                break

    return most_starred, most_active, most_popular, latest

def format_badge_string(text: str) -> str:
    """Escapes strings for shields.io badges correctly (replace '-' with '--' and '_' with '__')"""
    safe = str(text).replace("-", "--").replace("_", "__")
    return requests.utils.quote(safe)

def generate_repo_card(username: str, repo: Dict, title: str, emoji: str, theme: str) -> str:
    repo_name = repo['name']
    repo_url = repo['html_url']
    description = repo.get('description') or 'No description available'
    stars = repo.get('stargazers_count', 0)
    forks = repo.get('forks_count', 0)
    downloads = repo.get('release_downloads', 0)
    language = repo.get('language') or 'Code'
    
    enriched_desc = description
    if len(enriched_desc) > 110:
        truncated = enriched_desc[:107]
        if ' ' in truncated:
            truncated = truncated.rsplit(' ', 1)[0]
        enriched_desc = truncated + "..."
    
    safe_badge_name = format_badge_string(repo_name)
    safe_lang = format_badge_string(language)
    
    downloads_badge = ""
    if downloads > 0:
        downloads_badge = f"""  <img src="https://img.shields.io/badge/Downloads-📦%20{downloads}-1e1e2e?style=flat-square&color=a6e3a1" alt="downloads"/>\n"""

    return f"""### {emoji} {title}
<div align="center">
  <a href="{repo_url}">
    <img src="https://img.shields.io/badge/{safe_badge_name}-181825?style=for-the-badge&logo=github&logoColor=white&labelColor=89b4fa" alt="{repo_name}" />
  </a>
  <br/>
  <img src="https://img.shields.io/badge/Stars-⭐%20{stars}-1e1e2e?style=flat-square&color=f5c2e7" alt="stars"/>
  <img src="https://img.shields.io/badge/Forks-🍴%20{forks}-1e1e2e?style=flat-square&color=cba6f7" alt="forks"/>
{downloads_badge}  <img src="https://img.shields.io/badge/Language-{safe_lang}-1e1e2e?style=flat-square&color=89b4fa" alt="language"/>
  <p><em>{enriched_desc}</em></p>
</div>
"""

def update_readme(username: str, most_starred: Dict, most_active: Dict, most_popular: Dict, latest: Dict, theme: str):
    featured_section = f"""<!-- FEATURED_REPOS_START -->
<div align="center">

{generate_repo_card(username, most_starred, "Most Starred", "🌟", theme)}
{generate_repo_card(username, most_active, "Most Active", "💻", theme)}
{generate_repo_card(username, most_popular, "Most Popular", "🔥", theme)}
{generate_repo_card(username, latest, "Latest Project", "🆕", theme)}
</div>
<!-- FEATURED_REPOS_END -->"""

    try:
        with open(README_PATH, 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except FileNotFoundError:
        return False
    
    pattern = r'<!-- FEATURED_REPOS_START -->.*?<!-- FEATURED_REPOS_END -->'
    if re.search(pattern, readme_content, re.DOTALL):
        new_content = re.sub(pattern, featured_section, readme_content, flags=re.DOTALL)
        with open(README_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    repos = get_user_repos(GITHUB_USERNAME)
    if not repos:
        return
    most_starred, most_active, most_popular, latest = analyze_repositories(repos)
    if all([most_starred, most_active, most_popular, latest]):
        update_readme(GITHUB_USERNAME, most_starred, most_active, most_popular, latest, THEME)
        print("Featured projects section in README.md updated successfully")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
