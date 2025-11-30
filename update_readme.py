#!/usr/bin/env python3
"""
Auto README Updater - Updates featured repositories automatically
"""

import requests
import re
import os
from typing import List, Dict, Tuple

GITHUB_USERNAME = "SyntX34"
README_PATH = "README.md"
THEME = "tokyonight"

def get_user_repos(username: str) -> List[Dict]:
    """Fetch all public repositories for a user"""
    repos = []
    page = 1
    
    print(f"📦 Fetching repositories for {username}...")
    
    while True:
        url = f"https://api.github.com/users/{username}/repos?page={page}&per_page=100&sort=updated"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            break
            
        data = response.json()
        if not data:
            break
            
        repos.extend(data)
        page += 1
    
    repos = [r for r in repos if not r['fork']]
    
    print(f"✅ Found {len(repos)} repositories")
    return repos

def analyze_repositories(repos: List[Dict]) -> Tuple[Dict, Dict, Dict, Dict]:
    """Analyze and categorize repositories"""
    
    if not repos:
        print("⚠️ No repositories found!")
        return None, None, None, None
    
    most_starred = max(repos, key=lambda x: x['stargazers_count'])
    print(f"⭐ Most Starred: {most_starred['name']} ({most_starred['stargazers_count']} stars)")
    
    latest = max(repos, key=lambda x: x['created_at'])
    print(f"🆕 Latest: {latest['name']}")
    
    most_popular = max(repos, key=lambda x: x['stargazers_count'] + x['forks_count'] + x['watchers_count'])
    print(f"🔥 Most Popular: {most_popular['name']}")
    
    most_active = max(repos, key=lambda x: x['updated_at'])
    print(f"💻 Most Active: {most_active['name']}")
    
    return most_starred, most_active, most_popular, latest

def generate_repo_section(username: str, repo: Dict, title: str, emoji: str, theme: str) -> str:
    """Generate markdown for a repository card"""
    repo_name = repo['name']
    return f"""### {emoji} {title}
[![Repo](https://github-readme-stats.vercel.app/api/pin/?username={username}&repo={repo_name}&theme={theme}&hide_border=true)](https://github.com/{username}/{repo_name})
"""

def update_readme(username: str, most_starred: Dict, most_active: Dict, most_popular: Dict, latest: Dict, theme: str):
    """Update README.md with featured repositories"""
    
    print("\n📝 Generating README section...")
    featured_section = f"""<!-- FEATURED_REPOS_START -->
<div align="center">

{generate_repo_section(username, most_starred, "Most Starred", "🌟", theme)}
{generate_repo_section(username, most_active, "Most Active", "💻", theme)}
{generate_repo_section(username, most_popular, "Most Popular", "🔥", theme)}
{generate_repo_section(username, latest, "Latest Project", "🆕", theme)}
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
    print(f"📊 Summary:")
    print(f"   Most Starred: {most_starred['name']}")
    print(f"   Most Active: {most_active['name']}")
    print(f"   Most Popular: {most_popular['name']}")
    print(f"   Latest: {latest['name']}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure you have 'requests' installed:")
        print("   pip install requests")
