import json
import os
import re
import subprocess
from datetime import datetime
import urllib.parse

GITHUB_USERNAME = "amarzeus"
README_PATH = "README.md"
CONFIG_PATH = "profile_config.json"

def run_command(command):
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(result.stderr)
        return None
    return result.stdout

def get_live_data():
    # GraphQL Query for languages, recent repos, followers, and total stars
    query = """
    query {
      user(login: "%s") {
        followers {
          totalCount
        }
        repositories(first: 100, ownerAffiliations: OWNER, orderBy: {field: PUSHED_AT, direction: DESC}) {
          totalCount
          totalDiskUsage
          nodes {
            name
            description
            url
            pushedAt
            stargazerCount
            forkCount
            primaryLanguage {
                name
                color
            }
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node {
                  name
                }
              }
            }
          }
        }
        contributionsCollection {
          contributionCalendar {
            totalContributions
          }
        }
      }
    }
    """ % GITHUB_USERNAME
    
    output = run_command(f"gh api graphql -f query='{query}'")
    if not output:
        return None
    
    data = json.loads(output)
    user_data = data['data']['user']
    repos = user_data['repositories']['nodes']
    
    # Calculate totals
    total_stars = sum([repo['stargazerCount'] for repo in repos])
    total_commits_yr = user_data['contributionsCollection']['contributionCalendar']['totalContributions']
    total_followers = user_data['followers']['totalCount']
    total_repos = user_data['repositories']['totalCount']
    
    # Process Languages
    language_stats = {}
    for repo in repos:
        for edge in repo['languages']['edges']:
            lang_name = edge['node']['name']
            size = edge['size']
            language_stats[lang_name] = language_stats.get(lang_name, 0) + size
            
    sorted_langs = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
    total_size = sum(language_stats.values()) if language_stats else 1
    
    top_langs = []
    for lang, size in sorted_langs[:6]:
        percentage = (size / total_size) * 100
        top_langs.append((lang, int(percentage)))
        
    # Process Active Projects (Top 2 recently pushed, excluding profile repo)
    active_projects = [r for r in repos if r['name'].lower() != GITHUB_USERNAME.lower()][:2]
    
    # If less than 2, pad it out
    while len(active_projects) < 2:
        active_projects.append({"name": "More Coming Soon", "description": "Working on new projects...", "url": f"https://github.com/{GITHUB_USERNAME}", "stargazerCount": 0, "forkCount": 0, "primaryLanguage": None})
        
    return {
        "top_langs": top_langs,
        "active_projects_list": active_projects,
        "stats": {
            "stars": total_stars,
            "commits": total_commits_yr,
            "followers": total_followers,
            "repos": total_repos
        }
    }

def generate_project_cards(projects):
    html = "  <table>\n    <tr>\n"
    for proj in projects:
        name = proj['name']
        desc = proj['description'] or "A cool project."
        url = proj['url']
        stars = proj.get('stargazerCount', 0)
        forks = proj.get('forkCount', 0)
        lang = proj.get('primaryLanguage')
        lang_str = ""
        if lang:
            lang_str = f"<span style='color: {lang['color']};'>●</span> {lang['name']}"
            
        html += f"""      <td width="50%">
        <div style="background: linear-gradient(135deg, #1e1e2e 0%, #2d2b55 100%); border-radius: 10px; padding: 20px; color: white;">
          <h3><a href="{url}" style="color: #6366F1; text-decoration: none;">📁 {name}</a></h3>
          <p style="font-size: 14px; min-height: 40px;">{desc}</p>
          <div style="font-size: 13px; display: flex; justify-content: space-between;">
            <span>{lang_str}</span>
            <span>⭐ {stars} &nbsp;&nbsp; 🍴 {forks}</span>
          </div>
        </div>
      </td>\n"""
    html += "    </tr>\n  </table>"
    return html

def update_readme(live_data):
    # Load config
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
    except:
        config = {
            "focus": "Building next-generation applications",
            "learning": "Advanced System Design",
            "quote": "Keep shipping."
        }
        
    with open(README_PATH, 'r') as f:
        content = f.read()
    
    # 1. Update Skill Meter
    skill_meter_start = "<!-- SKILL-METER:START -->"
    skill_meter_end = "<!-- SKILL-METER:END -->"
    
    colors = ["6366F1", "EC4899", "22D3EE", "F8D866", "F85D7F", "00D4AA"]
    
    skill_table = '<details>\n    <summary>🎯 <strong>Skill Proficiency Levels</strong></summary>\n    <br>\n    <table border="0">\n'
    for i, (lang, percentage) in enumerate(live_data["top_langs"]):
        color = colors[i % len(colors)]
        skill_table += f'      <tr><td><b>{lang}</b></td><td><img src="https://geps.dev/progress/{percentage}?color={color}" /></td></tr>\n'
    skill_table += '    </table>\n  </details>'
    
    content = re.sub(f'{skill_meter_start}.*?{skill_meter_end}', 
                    f'{skill_meter_start}\n  {skill_table}\n  {skill_meter_end}', 
                    content, flags=re.DOTALL)
    
    # 2. Update LIVE-DATA footer
    live_data_start = "<!-- LIVE-DATA:START -->"
    live_data_end = "<!-- LIVE-DATA:END -->"
    
    now = datetime.now().strftime("%-m/%-d/%Y, %-I:%M:%S %p")
    active_names = ", ".join([p['name'] for p in live_data['active_projects_list'] if p['name'] != 'More Coming Soon'])
    
    live_section = f"""  <div align="center">
    <p>🕐 Last Updated: {now}</p>
    <p>💭 Quote: "{config['quote']}"</p>
    <p>🎯 Current Focus: {config['focus']}</p>
    <p>🚀 Active Projects: {active_names}</p>
    <p>💡 Learning: {config['learning']}</p>
  </div>"""
    
    content = re.sub(f'{live_data_start}.*?{live_data_end}', 
                    f'{live_data_start}\n{live_section}\n  {live_data_end}', 
                    content, flags=re.DOTALL)

    # 3. Update Featured Projects
    projects_start = "<!-- PROJECTS:START -->"
    projects_end = "<!-- PROJECTS:END -->"
    
    project_cards_html = generate_project_cards(live_data["active_projects_list"])
    
    if projects_start in content:
        content = re.sub(f'{projects_start}.*?{projects_end}', 
                        f'{projects_start}\n{project_cards_html}\n  {projects_end}', 
                        content, flags=re.DOTALL)
                        
    # 4. Update Quick Stats Overview badges
    stats = live_data['stats']
    quick_stats_start = "<!-- QUICK-STATS:START -->"
    quick_stats_end = "<!-- QUICK-STATS:END -->"
    
    quick_stats = f"""  <p>
    <img src="https://img.shields.io/badge/Total%20Stars-{stats['stars']}-F8D866?style=for-the-badge&logo=github&logoColor=white&labelColor=0D1117" alt="Total Stars">
    <img src="https://img.shields.io/badge/Yearly%20Commits-{stats['commits']}-73C0F4?style=for-the-badge&logo=github&logoColor=white&labelColor=0D1117" alt="Yearly Commits">
    <img src="https://img.shields.io/badge/Focus-{urllib.parse.quote(config['focus'])}-F85D7F?style=for-the-badge&logoColor=white&labelColor=0D1117" alt="Current Focus">
  </p>"""

    if quick_stats_start in content:
        content = re.sub(f'{quick_stats_start}.*?{quick_stats_end}', 
                        f'{quick_stats_start}\n{quick_stats}\n  {quick_stats_end}', 
                        content, flags=re.DOTALL)
                        
    # 5. Update Advanced Analytics Badges
    adv_stats_start = "<!-- ADV-STATS:START -->"
    adv_stats_end = "<!-- ADV-STATS:END -->"
    
    adv_stats = f"""  <table>
    <tr>
      <td><img src="https://img.shields.io/badge/Total%20Commits%20(Year)-{stats['commits']}-orange?style=for-the-badge&logo=github" alt="Commits" /></td>
      <td><img src="https://img.shields.io/badge/Total%20Public%20Repos-{stats['repos']}-blue?style=for-the-badge&logo=github" alt="Repos" /></td>
      <td><img src="https://img.shields.io/badge/Total%20Stars%20Earned-{stats['stars']}-yellow?style=for-the-badge&logo=github" alt="Stars" /></td>
    </tr>
    <tr>
      <td><img src="https://img.shields.io/badge/GitHub%20Followers-{stats['followers']}-green?style=for-the-badge&logo=github" alt="Followers" /></td>
      <td><img src="https://img.shields.io/badge/Main%20Language-{live_data['top_langs'][0][0] if live_data['top_langs'] else 'None'}-red?style=for-the-badge&logo=code" alt="Top Lang" /></td>
      <td><img src="https://img.shields.io/badge/Top%20Project-{urllib.parse.quote(active_names.split(', ')[0]) if active_names else 'None'}-purple?style=for-the-badge&logo=github" alt="Top Project" /></td>
    </tr>
  </table>"""

    if adv_stats_start in content:
        content = re.sub(f'{adv_stats_start}.*?{adv_stats_end}', 
                        f'{adv_stats_start}\n{adv_stats}\n  {adv_stats_end}', 
                        content, flags=re.DOTALL)

    with open(README_PATH, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    data = get_live_data()
    if data:
        update_readme(data)
        print("Successfully updated README.md with dynamically injected live data stats and badges!")
    else:
        print("Failed to fetch live stats.")
