import json
import os
import re
import subprocess
from datetime import datetime
import urllib.parse
import urllib.request

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
    
    total_stars = sum([repo['stargazerCount'] for repo in repos])
    total_commits_yr = user_data['contributionsCollection']['contributionCalendar']['totalContributions']
    total_followers = user_data['followers']['totalCount']
    total_repos = user_data['repositories']['totalCount']
    
    language_stats = {}
    for repo in repos:
        for edge in repo['languages']['edges']:
            lang_name = edge['node']['name']
            size = edge['size']
            language_stats[lang_name] = language_stats.get(lang_name, 0) + size
            
    sorted_langs = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
    total_size = sum(language_stats.values()) if language_stats else 1
    
    top_langs = []
    # Use enumerate to safely iterate the max top 6 instead of slicing dict views directly
    for i, (lang, size) in enumerate(sorted_langs):
        if i >= 6:
            break
        percentage = (size / total_size) * 100
        top_langs.append((lang, int(percentage)))
        
    active_projects = []
    # Safely build active projects without slicing a comprehension directly
    count = 0
    for r in repos:
        if isinstance(r, dict) and r.get('name', '').lower() != GITHUB_USERNAME.lower():
            active_projects.append(r)
            count += 1
            if count >= 2:
                break
    
    while len(active_projects) < 2:
        active_projects.append({"name": "More Coming Soon", "description": "Working on new projects...", "url": f"https://github.com/{GITHUB_USERNAME}", "stargazerCount": 0, "forkCount": 0, "primaryLanguage": None})
        
    return {
        "top_langs": top_langs,
        "active_projects_list": active_projects,
        "stats": {
            "stars": int(total_stars),
            "commits": int(total_commits_yr),
            "followers": int(total_followers),
            "repos": int(total_repos)
        }
    }

def generate_project_cards(projects):
    html = '  <p align="center">\n'
    for proj in projects:
        name = proj['name']
        if name == 'More Coming Soon':
            continue
        # Use GitHub's official OpenGraph image as a reliable, high-quality repository card since github-readme-stats is down
        html += f'    <a href="{proj["url"]}"><img src="https://opengraph.githubassets.com/1/{GITHUB_USERNAME}/{urllib.parse.quote(name)}" alt="{name}" width="400"/></a>\n'
    html += '  </p>'
    return html

def safe_shield_text(text):
    return text.replace('-', '--').replace('_', '__')

def download_svg(url, filename):
    print(f"Downloading {filename}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 200:
                content = response.read().decode('utf-8')
                if "<svg" in content:
                    with open(filename, 'w') as f:
                        f.write(content)
                    print(f"Success: {filename}")
                else:
                    print(f"Warning: Response is not valid SVG for {filename}")
    except Exception as e:
        print(f"Failed to download {filename}: {e}")

import random

def get_latest_activity():
    query = """
    query {
      user(login: "%s") {
        repositories(first: 5, orderBy: {field: PUSHED_AT, direction: DESC}) {
          nodes {
            name
            url
            pushedAt
          }
        }
      }
    }
    """ % GITHUB_USERNAME
    
    output = run_command(f"gh api graphql -f query='{query}'")
    if not output:
        return []
    
    try:
        data = json.loads(output)
        repos = data['data']['user']['repositories']['nodes']
        activity = []
        for repo in repos:
            date_str = repo['pushedAt'][:10]
            activity.append(f"Push to [{repo['name']}]({repo['url']}) - {date_str}")
        return activity
    except:
        return []

def update_readme(live_data):
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), '../profile_config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {
            "focus": "Building next-generation AI-powered development tools",
            "learning": "Advanced System Design & AI",
            "quote": "The best error message is the one that never shows up.",
            "timeline": []
        }
    
    focus = config.get("focus", "Building next-generation AI-powered development tools")
    quote = config.get("quote", "The best error message is the one that never shows up.")
    learning = config.get("learning", "Advanced System Design & AI")
    timeline = config.get("timeline", [])
        
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
    
    now = datetime.now().strftime("%Y-%m-%d")
    active_names = ", ".join([p['name'] for p in live_data['active_projects_list'] if p['name'] != 'More Coming Soon'])
    
    live_section = f"""  <div align="center">
    <p>🕐 Last Updated: {now}</p>
    <p>💭 Quote: "{quote}"</p>
    <p>🎯 Current Focus: {focus}</p>
    <p>🚀 Active Projects: {active_names}</p>
    <p>💡 Learning: {learning}</p>
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
    
    encoded_focus = urllib.parse.quote(safe_shield_text(focus))
    quick_stats = f"""  <p align="center">
    <a href="https://github.com/{GITHUB_USERNAME}?tab=repositories"><img src="https://img.shields.io/badge/Total%20Stars-{stats['stars']}-F8D866?style=for-the-badge&logo=github&logoColor=white&labelColor=0D1117" alt="Total Stars"></a>
    <a href="https://github.com/{GITHUB_USERNAME}"><img src="https://img.shields.io/badge/Yearly%20Commits-{stats['commits']}-73C0F4?style=for-the-badge&logo=github&logoColor=white&labelColor=0D1117" alt="Yearly Commits"></a>
    <a href="https://github.com/{GITHUB_USERNAME}"><img src="https://img.shields.io/badge/Focus-{encoded_focus}-F85D7F?style=for-the-badge&logoColor=white&labelColor=0D1117" alt="Current Focus"></a>
  </p>"""

    if quick_stats_start in content:
        content = re.sub(f'{quick_stats_start}.*?{quick_stats_end}', 
                        f'{quick_stats_start}\n{quick_stats}\n  {quick_stats_end}', 
                        content, flags=re.DOTALL)
                        
    # 5. Update Advanced Analytics Badges
    adv_stats_start = "<!-- ADV-STATS:START -->"
    adv_stats_end = "<!-- ADV-STATS:END -->"
    best_lang = safe_shield_text(live_data['top_langs'][0][0]) if live_data['top_langs'] else 'None'
    top_project = safe_shield_text(active_names.split(', ')[0]) if active_names else 'None'

    adv_stats = f"""  <p align="center">
    <a href="https://github.com/{GITHUB_USERNAME}"><img src="https://img.shields.io/badge/Total%20Commits%20(Year)-{stats['commits']}-orange?style=for-the-badge&logo=github" alt="Commits" /></a>
    <a href="https://github.com/{GITHUB_USERNAME}?tab=repositories"><img src="https://img.shields.io/badge/Total%20Public%20Repos-{stats['repos']}-blue?style=for-the-badge&logo=github" alt="Repos" /></a>
    <a href="https://github.com/{GITHUB_USERNAME}?tab=repositories"><img src="https://img.shields.io/badge/Total%20Stars%20Earned-{stats['stars']}-yellow?style=for-the-badge&logo=github" alt="Stars" /></a>
    <a href="https://github.com/{GITHUB_USERNAME}?tab=followers"><img src="https://img.shields.io/badge/GitHub%20Followers-{stats['followers']}-green?style=for-the-badge&logo=github" alt="Followers" /></a>
    <a href="https://github.com/{GITHUB_USERNAME}"><img src="https://img.shields.io/badge/Main%20Language-{urllib.parse.quote(best_lang)}-red?style=for-the-badge&logo=code" alt="Top Lang" /></a>
    <a href="https://github.com/{GITHUB_USERNAME}/{urllib.parse.quote(top_project)}"><img src="https://img.shields.io/badge/Top%20Project-{urllib.parse.quote(top_project)}-purple?style=for-the-badge&logo=github" alt="Top Project" /></a>
  </p>"""

    if adv_stats_start in content:
        content = re.sub(f'{adv_stats_start}.*?{adv_stats_end}', 
                        f'{adv_stats_start}\n{adv_stats}\n  {adv_stats_end}', 
                        content, flags=re.DOTALL)
                        
    # 5.3 Replace Timeline section
    timeline_start = "<!-- TIMELINE:START -->"
    timeline_end = "<!-- TIMELINE:END -->"
    
    if isinstance(timeline, list) and timeline:
        timeline_rows = []
        for item in timeline:
            if isinstance(item, dict):
                desc_html = f" - {item.get('desc', '')}" if "desc" in item else ""
                timeline_rows.append(f"    <li>{item.get('icon', '💼')} <strong>{item.get('year', '')}</strong>: <i>{item.get('role', '')}</i>{desc_html}</li>")
        
        timeline_html = "\n".join(timeline_rows)
        timeline_block = f"""<details>
  <summary>⏳ <strong>View Career Timeline</strong></summary>
  <br>
  <ul>
{timeline_html}
  </ul>
</details>"""

        if timeline_start in content:
            content = re.sub(f'{timeline_start}.*?{timeline_end}', 
                            f'{timeline_start}\n{timeline_block}\n{timeline_end}', 
                            content, flags=re.DOTALL)
                        
    # 5.5 Update Language Proficiency Meters
    skill_meter_start = "<!-- SKILL-METER:START -->"
    skill_meter_end = "<!-- SKILL-METER:END -->"
    
    color_map = ["6366F1", "EC4899", "22D3EE", "F8D866", "F85D7F", "00D4AA"]
    
    skills_rows = []
    for i, (lang, percentage) in enumerate(live_data['top_langs']):
      # map a color looping through the color map
      color = color_map[i % len(color_map)]
      skills_rows.append(f"      <tr><td><b>{lang}</b></td><td><img src=\"https://geps.dev/progress/{int(percentage)}?color={color}\" /></td></tr>")
      
    skills_html = "\n".join(skills_rows)
    
    skill_block = f"""  <details>
    <summary>🎯 <strong>Skill Proficiency Levels</strong> <i>(Auto-Updated)</i></summary>
    <br>
    <table border="0">
{skills_html}
    </table>
  </details>"""
  
    if skill_meter_start in content:
        content = re.sub(f'{skill_meter_start}.*?{skill_meter_end}', 
                        f'{skill_meter_start}\n{skill_block}\n  {skill_meter_end}', 
                        content, flags=re.DOTALL)

    # 6. Hide Blog Section if empty
    blog_section_start = "<!-- BLOG-SECTION:START -->"
    blog_section_end = "<!-- BLOG-SECTION:END -->"
    blog_content_start = "<!-- BLOG-POST-LIST:START -->"
    blog_content_end = "<!-- BLOG-POST-LIST:END -->"
    
    # We'll just check if the posts string is empty. Currently it's a fixed placeholder on README
    # The README.md has a static placeholder for blog posts right now, let's wrap it and hide it using regex locally.
    pass # Blog Section hides will be handled via README native markdown deletion since no blog logic exists in python yet

    # 7. Bust Cache on Streak Stats
    # We remove the random timestamp to prevent unnecessary daily commits if stats haven't changed.
    content = re.sub(r'https://github-readme-streak-stats\.herokuapp\.com/\?user=amarzeus&theme=tokyonight&hide_border=true(?:&cb=\d+)?', 
                     f'https://github-readme-streak-stats.herokuapp.com/?user=amarzeus&theme=tokyonight&hide_border=true', 
                     content)

    # 8. Update Recent Activity
    activity_start = "<!-- ACTIVITY:START -->"
    activity_end = "<!-- ACTIVITY:END -->"
    
    activity = get_latest_activity()
    act_str = "<br>\n".join(f"🚀 {a}" for a in activity) if activity else "_No recent activity found._"
    
    if activity_start in content:
        content = re.sub(f'{activity_start}.*?{activity_end}', 
                        f'{activity_start}\n<div align="left">\n<p>{act_str}</p>\n</div>\n  {activity_end}', 
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
