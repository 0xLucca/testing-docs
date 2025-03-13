import requests
import json
import os
import sys

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
# REPO_API_URL = "https://api.github.com/repos/polkadot-developers/polkadot-docs/issues"
REPO_API_URL = "https://api.github.com/repos/0xLucca/testing-docs/issues"

def issue_exists(title):
    """Check if an issue with the same title already exists."""
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }
        response = requests.get(REPO_API_URL, headers=headers)
        response.raise_for_status()

        issues = response.json()
        for issue in issues:
            if issue["title"] == title:
                return True
        return False
    except Exception as e:
        print(f"Error checking for existing issues: {e}")
        sys.exit(1)

def create_github_issue(title, body):
    """Create a GitHub issue using the GitHub API."""
    try:
        if issue_exists(title):
            print(f"Issue '{title}' already exists. Skipping creation.")
            return

        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }
        data = {"title": title, "body": body}
        response = requests.post(REPO_API_URL, headers=headers, json=data)

        if response.status_code == 201:
            print(f"Successfully created issue '{title}'")
            return
        else:
            print(f"Failed to create issue '{title}'. Status code: {response.status_code}")
            print(response.text)
            sys.exit(1)
    except Exception as e:
        print(f"Error creating issue: {e}")
        sys.exit(1)

def format_code_diff(current_code, latest_code):
    """Format the code difference for GitHub markdown."""
    diff_md = "```diff\n"
    
    # Split the code into lines
    current_lines = current_code.splitlines() if current_code else []
    latest_lines = latest_code.splitlines() if latest_code else []
    
    # Simple diff: prefix removed lines with - and added lines with +
    for line in current_lines:
        # if line not in latest_lines:
        diff_md += f"- {line}\n"
    
    for line in latest_lines:
        # if line not in current_lines:
        diff_md += f"+ {line}\n"
    
    diff_md += "```\n"
    return diff_md

def main():
    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN environment variable is not set.")
        sys.exit(1)

    try:
        with open("outdated_dependencies.json", "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        sys.exit(1)

    for dep in data.get("outdated_dependencies", []):
        title = f"Update needed: {dep['name']} ({dep['current_version']} -> {dep['latest_version']})"
        
        body = f"""A new release has been detected for {dep['name']}.

Category: {dep['category']}
Current version: {dep['current_version']}
Latest version: {dep['latest_version']}

Latest release: [View here]({dep['latest_release_url']})
"""

        # Add outdated snippets information if available
        if 'outdated_snippets' in dep and dep['outdated_snippets']:
            body += "\n## Outdated Code Snippets\n\n"
            body += "The following code snippets in the documentation need to be updated:\n\n"
            
            for i, snippet in enumerate(dep['outdated_snippets'], 1):
                file_path = snippet['file']
                line_number = snippet['line_number']
                current_url = snippet['current_url']
                latest_url = snippet['latest_url']
                
                # Include file path and line number as a link to the repository file if possible
                repo_file_path = f"https://github.com/polkadot-developers/polkadot-docs/blob/main/{file_path.replace('./', '')}#L{line_number}"
                body += f"### {i}. [{os.path.basename(file_path)}:{line_number}]({repo_file_path}#L{line_number})\n\n"
                
                # Add URLs for reference
                body += f"**Current URL:** {current_url}\n\n"
                body += f"**Latest URL:** {latest_url}\n\n"
                
                # If the comparison results include the actual code snippets, show the diff
                if 'current_code' in snippet and 'latest_code' in snippet:
                    body += "**Code Difference:**\n\n"
                    body += format_code_diff(snippet['current_code'], snippet['latest_code'])
                    body += "\n"
        
        body += "\nPlease review the change log and update the documentation accordingly."

        create_github_issue(title, body)

if __name__ == "__main__":
    main()