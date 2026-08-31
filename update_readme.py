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

def analyze_repositories(repos: List[Dict]) -> Tuple[Dict, Dict, Dict, Dict]:
    if not repos:
        return None, None, None, None
    now = datetime.now()
    most_starred = max(repos, key=lambda x: x.get('stargazers_count', 0))
    latest = max(repos, key=lambda x: x.get('created_at', ''))
    
    for repo in repos:
        try:
            last_update = datetime.strptime(repo['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
            created_date = datetime.strptime(repo['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            days_since_update = (now - last_update).days
            days_since_created = (now - created_date).days
        except Exception:
            days_since_update = 100
            days_since_created = 100

        base_score = repo.get('stargazers_count', 0) * 3 + repo.get('forks_count', 0) * 2
        if days_since_update <= 30:
            base_score += max(0, 50 - (days_since_update * 1.5))
        if days_since_created <= 90:
            base_score += max(0, 30 - (days_since_created * 0.33))
        if repo.get('description') and len(repo['description']) > 10:
            base_score += 10
        if repo.get('topics'):
            base_score += len(repo['topics']) * 3
        if days_since_update > 365:
            base_score *= 0.8
        
        repo['popularity_score'] = int(base_score)
    
    repos_sorted_by_popularity = sorted(repos, key=lambda x: x.get('popularity_score', 0), reverse=True)
    most_popular = repos_sorted_by_popularity[0]
    if most_popular['name'] == most_starred['name'] and len(repos_sorted_by_popularity) > 1:
        most_popular = repos_sorted_by_popularity[1]
    
    repos_sorted_by_activity = sorted(repos, key=lambda x: x.get('updated_at', ''), reverse=True)
    most_active = repos_sorted_by_activity[0]
    if most_active['name'] == latest['name'] and len(repos_sorted_by_activity) > 1:
        for repo in repos_sorted_by_activity[1:]:
            if repo['name'] != latest['name']:
                most_active = repo
                break
    
    selected_repos = {
        'most_starred': most_starred,
        'latest': latest,
        'most_popular': most_popular,
        'most_active': most_active
    }
    
    if len(set(r['name'] for r in selected_repos.values())) < 4:
        all_methods = [
            lambda r: r.get('stargazers_count', 0),
            lambda r: r.get('created_at', ''),
            lambda r: r.get('popularity_score', 0),
            lambda r: r.get('updated_at', ''),
        ]
        used = set()
        final_selections = {}
        slots = ['most_starred', 'latest', 'most_popular', 'most_active']
        for i, slot in enumerate(slots):
            for r in sorted(repos, key=all_methods[i], reverse=True):
                if r['name'] not in used:
                    final_selections[slot] = r
                    used.add(r['name'])
                    break
        most_starred = final_selections.get('most_starred', most_starred)
        latest = final_selections.get('latest', latest)
        most_popular = final_selections.get('most_popular', most_popular)
        most_active = final_selections.get('most_active', most_active)
    
    return most_starred, most_active, most_popular, latest

def generate_repo_card(username: str, repo: Dict, title: str, emoji: str, theme: str) -> str:
    repo_name = repo['name']
    repo_url = repo['html_url']
    description = repo.get('description') or 'No description available'
    stars = repo.get('stargazers_count', 0)
    forks = repo.get('forks_count', 0)
    language = repo.get('language') or 'Code'
    
    enriched_desc = description
    if len(enriched_desc) > 110:
        truncated = enriched_desc[:107]
        if ' ' in truncated:
            truncated = truncated.rsplit(' ', 1)[0]
        enriched_desc = truncated + "..."
    
    lang_encoded = requests.utils.quote(language)
    repo_name_encoded = requests.utils.quote(repo_name)
    
    return f"""### {emoji} {title}
<div align="center">
  <a href="{repo_url}">
    <img src="https://img.shields.io/badge/{repo_name_encoded}-181825?style=for-the-badge&logo=github&logoColor=white&labelColor=89b4fa" alt="{repo_name}" />
  </a>
  <br/>
  <img src="https://img.shields.io/badge/Stars-⭐%20{stars}-1e1e2e?style=flat-square&color=f5c2e7" alt="stars"/>
  <img src="https://img.shields.io/badge/Forks-🍴%20{forks}-1e1e2e?style=flat-square&color=cba6f7" alt="forks"/>
  <img src="https://img.shields.io/badge/Language-{lang_encoded}-1e1e2e?style=flat-square&color=89b4fa" alt="language"/>
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

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
