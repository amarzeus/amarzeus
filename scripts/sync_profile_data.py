import json
import os
import re
import subprocess
from datetime import datetime

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
    # GraphQL Query for languages and recent repos
    query = """
    query {
      user(login: "%s") {
        repositories(first: 100, ownerAffiliations: OWNER, orderBy: {field: PUSHED_AT, direction: DESC}) {
          nodes {
            name
            description
            url
            pushedAt
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
      }
    }
    """ % GITHUB_USERNAME
    
    output = run_command(f'gh api graphql -f query=\'{query}\'')
    if not output:
        return None
    
    data = json.loads(output)
    repos = data['data']['user']['repositories']['nodes']
    
    # Process Languages
    language_stats = {}
    for repo in repos:
        for edge in repo['languages']['edges']:
            lang_name = edge['node']['name']
            size = edge['size']
            language_stats[lang_name] = language_stats.get(lang_name, 0) + size
            
    sorted_langs = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
    total_size = sum(language_stats.values())
    
    top_langs = []
    for lang, size in sorted_langs[:6]:
        percentage = (size / total_size) * 100
        top_langs.append((lang, int(percentage)))
        
    # Process Active Projects (Top 3 recently pushed, excluding the profile repo itself)
    active_projects = [r for r in repos if r['name'].lower() != GITHUB_USERNAME.lower()][:3]
    active_project_names = [r['name'] for r in active_projects]
    
    return {
        "top_langs": top_langs,
        "active_projects": ", ".join(active_project_names)
    }

def update_readme(live_data):
    # Load config
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
        
    with open(README_PATH, 'r') as f:
        content = f.read()
    
    # Update Skill Meter
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
    
    # Update Live Data
    live_data_start = "<!-- LIVE-DATA:START -->"
    live_data_end = "<!-- LIVE-DATA:END -->"
    
    now = datetime.now().strftime("%-m/%-d/%Y, %-I:%M:%S %p")
    
    live_section = f"""  <div align="center">
    <p>🕐 Last Updated: {now}</p>
    <p>💭 Quote: "{config['quote']}"</p>
    <p>🎯 Current Focus: {config['focus']}</p>
    <p>🚀 Active Projects: {live_data['active_projects']}</p>
    <p>💡 Learning: {config['learning']}</p>
  </div>"""
    
    content = re.sub(f'{live_data_start}.*?{live_data_end}', 
                    f'{live_data_start}\n{live_section}\n  {live_data_end}', 
                    content, flags=re.DOTALL)
    
    with open(README_PATH, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    data = get_live_data()
    if data:
        update_readme(data)
        print("Successfully updated README.md with live data!")
    else:
        print("Failed to fetch live stats.")
