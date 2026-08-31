import requests

headers = {'Accept': 'application/vnd.github.v3+json'}
url = 'https://api.github.com/users/SyntX34/repos?per_page=100'
repos = requests.get(url, headers=headers).json()
for r in repos:
    if not r.get('fork') and not r.get('archived') and r.get('name') != 'SyntX34':
        releases_url = f"https://api.github.com/repos/SyntX34/{r['name']}/releases"
        rels = requests.get(releases_url, headers=headers).json()
        downloads = 0
        if isinstance(rels, list):
            for rel in rels:
                for asset in rel.get('assets', []):
                    downloads += asset.get('download_count', 0)
        if downloads > 0 or r.get('forks_count', 0) > 0 or r.get('stargazers_count', 0) > 0:
            print(f"{r['name']} | Stars: {r.get('stargazers_count')} | Forks: {r.get('forks_count')} | Downloads: {downloads} | Pushed: {r.get('pushed_at')}")
