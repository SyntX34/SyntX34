#!/usr/bin/env python3
"""
Auto README Updater - Updates featured repositories automatically
"""

import requests
import re
import os
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

GITHUB_USERNAME = "SyntX34"
README_PATH = "README.md"
THEME = "tokyonight"

def get_user_repos(username: str) -> List[Dict]:
    """Fetch all public repositories for a user"""
    repos = []
    page = 1
    
    print(f"📦 Fetching repositories for {username}...")
    
    headers = {'Accept': 'application/vnd.github.v3+json'}
    github_token = os.environ.get('GITHUB_TOKEN')
    if github_token:
        headers['Authorization'] = f'token {github_token}'
        print("✓ Using GitHub token for API requests")
    
    while True:
        url = f"https://api.github.com/users/{username}/repos?page={page}&per_page=100&sort=updated"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            if response.status_code == 403:
                print("⚠️  Rate limit exceeded. Wait an hour or add GITHUB_TOKEN.")
                if github_token:
                    print("⚠️  Token might not have proper permissions, trying without...")
                    headers.pop('Authorization', None)
                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        continue
            break
            
        data = response.json()
        if not data:
            break
            
        repos.extend(data)
        page += 1
    
    filtered_repos = []
    for repo in repos:
        if repo['fork'] or repo['archived']:
            continue
        if repo['name'] == username:
            continue
        filtered_repos.append(repo)
    
    print(f"✅ Found {len(filtered_repos)} repositories (excluding forks, archived, and profile)")
    
    print("\n📅 All repositories with creation dates:")
    for repo in sorted(filtered_repos, key=lambda x: x['created_at'], reverse=True)[:10]:
        print(f"   {repo['name']}: {repo['created_at'][:10]} (stars: {repo['stargazers_count']})")
    
    return filtered_repos

def analyze_repositories(repos: List[Dict]) -> Tuple[Dict, Dict, Dict, Dict]:
    """Analyze and categorize repositories"""
    
    if not repos:
        print("⚠️ No repositories found!")
        return None, None, None, None
    now = datetime.now()
    most_starred = max(repos, key=lambda x: x['stargazers_count'])
    print(f"\n⭐ Most Starred: {most_starred['name']} ({most_starred['stargazers_count']} stars)")
    latest = max(repos, key=lambda x: x['created_at'])
    print(f"🆕 Latest Project: {latest['name']} (created: {latest['created_at'][:10]})")
    
    for repo in repos:
        last_update = datetime.strptime(repo['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
        created_date = datetime.strptime(repo['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        days_since_update = (now - last_update).days
        days_since_created = (now - created_date).days
        base_score = repo['stargazers_count'] * 3 + repo['forks_count'] * 2
        
        if days_since_update <= 30:
            recency_bonus = max(0, 50 - (days_since_update * 1.5))
            base_score += recency_bonus
        
        if days_since_created <= 90:
            newness_bonus = max(0, 30 - (days_since_created * 0.33))
            base_score += newness_bonus
        
        if repo['description'] and len(repo['description']) > 10:
            base_score += 10
        
        if repo.get('topics'):
            base_score += len(repo['topics']) * 3
        
        if days_since_update > 365:
            base_score *= 0.8
        
        repo['popularity_score'] = int(base_score)
    
    repos_sorted_by_popularity = sorted(repos, key=lambda x: x['popularity_score'], reverse=True)
    most_popular = repos_sorted_by_popularity[0]
    if most_popular['name'] == most_starred['name'] and len(repos_sorted_by_popularity) > 1:
        most_popular = repos_sorted_by_popularity[1]
    
    print(f"🔥 Most Popular: {most_popular['name']} (score: {most_popular['popularity_score']})")
    repos_sorted_by_activity = sorted(repos, key=lambda x: x['updated_at'], reverse=True)
    most_active = repos_sorted_by_activity[0]
    if most_active['name'] == latest['name'] and len(repos_sorted_by_activity) > 1:
        for repo in repos_sorted_by_activity[1:]:
            if repo['name'] != latest['name']:
                most_active = repo
                break
    
    print(f"💻 Most Active: {most_active['name']} (updated: {most_active['updated_at'][:10]})")
    
    selected_repos = {
        'most_starred': most_starred,
        'latest': latest,
        'most_popular': most_popular,
        'most_active': most_active
    }
    
    repo_names = [r['name'] for r in selected_repos.values()]
    unique_names = set(repo_names)
    
    if len(unique_names) < 4:
        print(f"\n⚠️ Found duplicates ({len(unique_names)} unique repos, need 4). Finding alternatives...")
        
        selection_methods = [
            ('most_starred', lambda r: r['stargazers_count'], True),
            ('latest', lambda r: r['created_at'], True),
            ('most_popular', lambda r: r['popularity_score'], True),
            ('most_active', lambda r: r['updated_at'], True), 
        ]
        
        backup_methods = [
            ('forks', lambda r: r['forks_count'], True),
            ('watchers', lambda r: r['watchers_count'], True),
            ('size', lambda r: r['size'], True),
            ('open_issues', lambda r: r['open_issues_count'], True),
        ]
        
        all_methods = selection_methods + backup_methods
        
        used_repos = set()
        final_selections = {}
        
        for i in range(len(all_methods)):
            for method_name, sort_key, reverse in all_methods[i:]:
                sorted_repos = sorted(repos, key=sort_key, reverse=reverse)
                for repo in sorted_repos:
                    if repo['name'] not in used_repos:
                        if 'most_starred' not in final_selections:
                            final_selections['most_starred'] = repo
                        elif 'latest' not in final_selections:
                            final_selections['latest'] = repo
                        elif 'most_popular' not in final_selections:
                            final_selections['most_popular'] = repo
                        elif 'most_active' not in final_selections:
                            final_selections['most_active'] = repo
                        
                        used_repos.add(repo['name'])
                        break

                if len(final_selections) == 4:
                    break
            
            if len(final_selections) == 4:
                break
        
        if len(final_selections) < 4:
            unique_repos = []
            for repo in repos:
                if repo['name'] not in used_repos:
                    unique_repos.append(repo)
                if len(unique_repos) + len(final_selections) >= 4:
                    break
            slots = ['most_starred', 'latest', 'most_popular', 'most_active']
            for slot in slots:
                if slot not in final_selections:
                    if unique_repos:
                        final_selections[slot] = unique_repos.pop(0)
                    else:
                        for repo in repos:
                            if repo['name'] not in [r['name'] for r in final_selections.values()]:
                                final_selections[slot] = repo
                                break
        
        most_starred = final_selections.get('most_starred', most_starred)
        latest = final_selections.get('latest', latest)
        most_popular = final_selections.get('most_popular', most_popular)
        most_active = final_selections.get('most_active', most_active)
        
        print(f"✅ Found unique repos: {', '.join([r['name'] for r in final_selections.values()])}")
    
    print("\n" + "=" * 50)
    print("📊 Final Selection:")
    print(f"   Most Starred: {most_starred['name']} ({most_starred['stargazers_count']} ⭐)")
    print(f"   Latest Project: {latest['name']} (created: {latest['created_at'][:10]})")
    print(f"   Most Popular: {most_popular['name']} (score: {most_popular['popularity_score']})")
    print(f"   Most Active: {most_active['name']} (updated: {most_active['updated_at'][:10]})")
    
    return most_starred, most_active, most_popular, latest

def generate_repo_card(username: str, repo: Dict, title: str, emoji: str, theme: str) -> str:
    """Generate markdown for a repository card with fallback"""
    repo_name = repo['name']
    repo_url = repo['html_url']
    description = repo['description'] or 'No description available'
    stars = repo['stargazers_count']
    forks = repo['forks_count']
    language = repo['language'] or 'Unknown'
    
    import time
    cache_bust = int(time.time() // 3600) 
    
    return f"""### {emoji} {title}
<a href="{repo_url}">
  <img src="https://github-readme-stats.vercel.app/api/pin/?username={username}&repo={repo_name}&theme={theme}&hide_border=true&cache_seconds=86400&v={cache_bust}" alt="{repo_name}" />
</a>

**[{repo_name}]({repo_url})** - ⭐ {stars} | 🍴 {forks} | 📝 {language}
> {description}
"""

def update_readme(username: str, most_starred: Dict, most_active: Dict, most_popular: Dict, latest: Dict, theme: str):
    """Update README.md with featured repositories"""
    
    print("\n📝 Generating README section...")
    
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
        print(f"❌ {README_PATH} not found!")
        return False
    pattern = r'<!-- FEATURED_REPOS_START -->.*?<!-- FEATURED_REPOS_END -->'
    
    if re.search(pattern, readme_content, re.DOTALL):
        new_content = re.sub(pattern, featured_section, readme_content, flags=re.DOTALL)
        
        with open(README_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ README.md updated successfully!")
        return True
    else:
        print("⚠️ Could not find FEATURED_REPOS markers in README.md")
        print("📋 Here's the section to add manually:\n")
        print(featured_section)
        return False

def main():
    """Main function"""
    print("🚀 Auto README Updater")
    print("=" * 50)
    
    repos = get_user_repos(GITHUB_USERNAME)
    
    if not repos:
        print("❌ No repositories found. Exiting...")
        return
    
    most_starred, most_active, most_popular, latest = analyze_repositories(repos)
    
    if not all([most_starred, most_active, most_popular, latest]):
        print("❌ Could not analyze repositories. Exiting...")
        return
    
    print("\n" + "=" * 50)
    update_readme(GITHUB_USERNAME, most_starred, most_active, most_popular, latest, THEME)
    
    print("\n✨ Done! Your README is now up to date.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Make sure you have 'requests' installed:")
        print("   pip install requests")
