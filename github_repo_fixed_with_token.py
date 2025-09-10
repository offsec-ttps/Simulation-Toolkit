# -*- coding: utf-8 -*-
"""
Complete GitHub Repository to Excel Exporter - Fixed Version
============================================================
This script extracts data from GitHub repositories using the GitHub API 
and exports everything to Excel format with multiple sheets.

FIXED: Syntax error and added embedded token support

Requirements:
pip install requests pandas openpyxl

Usage:
python github_repo_fixed_with_token.py
"""

import requests
import pandas as pd
from datetime import datetime
import time
import os

# =============================================================================
# ADD YOUR GITHUB PERSONAL ACCESS TOKEN HERE
# =============================================================================
# Replace the token below with your actual GitHub Personal Access Token
# Get your token from: https://github.com/settings/tokens

GITHUB_TOKEN = "your_github_personal_access_token_here"

# =============================================================================

def get_access_token():
    """Get GitHub token from embedded value or environment variable"""
    # Check embedded token first
    if GITHUB_TOKEN and GITHUB_TOKEN != "your_github_personal_access_token_here":
        return GITHUB_TOKEN

    # Fallback to environment variable
    env_token = os.environ.get('GITHUB_TOKEN')
    if env_token:
        return env_token

    return None

def save_github_repo_to_excel(repo_url, access_token=None, output_file=None):
    """
    Save GitHub repository data to Excel file

    Args:
        repo_url: GitHub repository URL (e.g., 'https://github.com/owner/repo')
        access_token: GitHub Personal Access Token (optional but recommended)
        output_file: Output Excel filename (optional)
    """

    # Parse repository URL
    if repo_url.startswith('https://github.com/'):
        repo_path = repo_url.replace('https://github.com/', '')
    else:
        repo_path = repo_url

    owner, repo_name = repo_path.split('/')

    # Setup headers
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if access_token:
        headers['Authorization'] = 'token {}'.format(access_token)

    print("Extracting data from: {}/{}".format(owner, repo_name))

    # Get repository basic info
    repo_url_api = "https://api.github.com/repos/{}/{}".format(owner, repo_name)
    response = requests.get(repo_url_api, headers=headers)

    if response.status_code != 200:
        print("Error: {} - {}".format(response.status_code, response.json().get('message', 'Unknown error')))
        return None

    repo_data = response.json()

    # Extract repository information
    repo_info = {
        'Repository Name': repo_data['name'],
        'Full Name': repo_data['full_name'],
        'Description': repo_data['description'] or 'No description',
        'Owner': repo_data['owner']['login'],
        'Owner Type': repo_data['owner']['type'],
        'Language': repo_data['language'] or 'Not specified',
        'Stars': repo_data['stargazers_count'],
        'Forks': repo_data['forks_count'],
        'Watchers': repo_data['watchers_count'],
        'Open Issues': repo_data['open_issues_count'],
        'Size (KB)': repo_data['size'],
        'Created Date': repo_data['created_at'][:10],
        'Updated Date': repo_data['updated_at'][:10],
        'Pushed Date': repo_data['pushed_at'][:10],
        'Default Branch': repo_data['default_branch'],
        'License': repo_data['license']['name'] if repo_data['license'] else 'No license',
        'Visibility': 'Private' if repo_data['private'] else 'Public',
        'Clone URL (HTTPS)': repo_data['clone_url'],
        'Clone URL (SSH)': repo_data['ssh_url'],
        'Homepage': repo_data['homepage'] or 'None',
        'Has Issues': repo_data['has_issues'],
        'Has Wiki': repo_data['has_wiki'],
        'Has Pages': repo_data['has_pages'],
        'Has Projects': repo_data['has_projects'],
        'Archived': repo_data['archived'],
        'Disabled': repo_data['disabled'],
        'Topics': ', '.join(repo_data.get('topics', [])),
        'Network Count': repo_data['network_count'],
        'Subscribers Count': repo_data['subscribers_count']
    }

    # Get recent commits (last 30)
    print("Fetching recent commits...")
    commits_url = "https://api.github.com/repos/{}/{}/commits".format(owner, repo_name)
    commits_response = requests.get(commits_url, headers=headers, params={'per_page': 30})

    commits_data = []
    if commits_response.status_code == 200:
        for commit in commits_response.json():
            commits_data.append({
                'SHA': commit['sha'][:8],
                'Author': commit['commit']['author']['name'],
                'Author Email': commit['commit']['author']['email'],
                'Date': commit['commit']['author']['date'][:10],
                'Message': commit['commit']['message'].split('\n')[0][:100],  # First line only
                'Committer': commit['commit']['committer']['name'],
                'URL': commit['html_url']
            })

    # Get languages
    print("Fetching language data...")
    languages_url = "https://api.github.com/repos/{}/{}/languages".format(owner, repo_name)
    languages_response = requests.get(languages_url, headers=headers)

    languages_data = []
    if languages_response.status_code == 200:
        languages = languages_response.json()
        total_bytes = sum(languages.values())
        for lang, bytes_count in languages.items():
            languages_data.append({
                'Language': lang,
                'Bytes': bytes_count,
                'Percentage': round((bytes_count / total_bytes) * 100, 2) if total_bytes > 0 else 0
            })
        languages_data.sort(key=lambda x: x['Bytes'], reverse=True)

    # Get contributors
    print("Fetching contributors...")
    contributors_url = "https://api.github.com/repos/{}/{}/contributors".format(owner, repo_name)
    contributors_response = requests.get(contributors_url, headers=headers, params={'per_page': 20})

    contributors_data = []
    if contributors_response.status_code == 200:
        for contributor in contributors_response.json():
            contributors_data.append({
                'Username': contributor['login'],
                'Contributions': contributor['contributions'],
                'Type': contributor['type'],
                'Profile URL': contributor['html_url']
            })

    # Get issues (last 50)
    print("Fetching recent issues...")
    issues_url = "https://api.github.com/repos/{}/{}/issues".format(owner, repo_name)
    issues_response = requests.get(issues_url, headers=headers, params={'per_page': 50, 'state': 'all'})

    issues_data = []
    if issues_response.status_code == 200:
        for issue in issues_response.json():
            if 'pull_request' not in issue:  # Skip pull requests
                issues_data.append({
                    'Number': issue['number'],
                    'Title': issue['title'][:80],
                    'State': issue['state'],
                    'Author': issue['user']['login'],
                    'Created': issue['created_at'][:10],
                    'Updated': issue['updated_at'][:10],
                    'Comments': issue['comments'],
                    'Labels': ', '.join([label['name'] for label in issue['labels']]),
                    'URL': issue['html_url']
                })

    # Get releases (last 10)
    print("Fetching releases...")
    releases_url = "https://api.github.com/repos/{}/{}/releases".format(owner, repo_name)
    releases_response = requests.get(releases_url, headers=headers, params={'per_page': 10})

    releases_data = []
    if releases_response.status_code == 200:
        for release in releases_response.json():
            releases_data.append({
                'Tag': release['tag_name'],
                'Name': release['name'] or release['tag_name'],
                'Published': release['published_at'][:10] if release['published_at'] else 'Draft',
                'Author': release['author']['login'] if release['author'] else 'Unknown',
                'Prerelease': release['prerelease'],
                'Draft': release['draft'],
                'Downloads': sum([asset['download_count'] for asset in release['assets']]),
                'URL': release['html_url']
            })

    # Create output filename
    if not output_file:
        safe_repo_name = repo_name.replace('/', '_').replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = "{}_github_data_{}.xlsx".format(safe_repo_name, timestamp)

    # Save to Excel
    print("Saving to Excel: {}".format(output_file))

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:

        # Repository Info Sheet
        repo_df = pd.DataFrame([repo_info])
        repo_df.to_excel(writer, sheet_name='Repository_Info', index=False)

        # Commits Sheet
        if commits_data:
            commits_df = pd.DataFrame(commits_data)
            commits_df.to_excel(writer, sheet_name='Recent_Commits', index=False)

        # Languages Sheet
        if languages_data:
            languages_df = pd.DataFrame(languages_data)
            languages_df.to_excel(writer, sheet_name='Languages', index=False)

        # Contributors Sheet
        if contributors_data:
            contributors_df = pd.DataFrame(contributors_data)
            contributors_df.to_excel(writer, sheet_name='Contributors', index=False)

        # Issues Sheet
        if issues_data:
            issues_df = pd.DataFrame(issues_data)
            issues_df.to_excel(writer, sheet_name='Issues', index=False)

        # Releases Sheet
        if releases_data:
            releases_df = pd.DataFrame(releases_data)
            releases_df.to_excel(writer, sheet_name='Releases', index=False)

        # Summary Sheet
        summary_data = {
            'Metric': [
                'Repository Name',
                'Owner',
                'Primary Language',
                'Total Stars',
                'Total Forks',
                'Open Issues',
                'Total Contributors',
                'Total Commits Analyzed',
                'Total Releases',
                'Repository Size (KB)',
                'Created Date',
                'Last Updated',
                'License',
                'Export Date'
            ],
            'Value': [
                repo_info['Repository Name'],
                repo_info['Owner'],
                repo_info['Language'],
                repo_info['Stars'],
                repo_info['Forks'],
                repo_info['Open Issues'],
                len(contributors_data),
                len(commits_data),
                len(releases_data),
                repo_info['Size (KB)'],
                repo_info['Created Date'],
                repo_info['Updated Date'],
                repo_info['License'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
        }

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

    print("Successfully saved GitHub repository data to: {}".format(output_file))
    print("Data exported:")
    print("   - Repository metadata")
    print("   - {} recent commits".format(len(commits_data)))
    print("   - {} programming languages".format(len(languages_data)))
    print("   - {} contributors".format(len(contributors_data)))
    print("   - {} issues".format(len(issues_data)))
    print("   - {} releases".format(len(releases_data)))

    return output_file

# Example usage
if __name__ == "__main__":
    # Get access token (embedded or from environment)
    ACCESS_TOKEN = get_access_token()

    # Configuration - Replace with your values
    REPO_URL = "https://github.com/microsoft/vscode"  # Example repository

    print("GitHub Repository to Excel Converter")
    print("=" * 50)

    if ACCESS_TOKEN:
        print("✅ GitHub token found - using authenticated access")
    else:
        print("⚠️  No GitHub token found - using unauthenticated access (limited)")
        print("   Add your token to line 21 for better performance")

    # You can also specify the repository directly
    try:
        custom_repo = input("Enter GitHub repository URL (or press Enter for default): ").strip()
        if custom_repo:
            REPO_URL = custom_repo
    except:
        pass  # Use default if input fails

    try:
        output_file = save_github_repo_to_excel(
            repo_url=REPO_URL,
            access_token=ACCESS_TOKEN
        )

        if output_file:
            print("\nRepository data saved successfully!")
            print("File: {}".format(output_file))

    except Exception as e:
        print("Error: {}".format(str(e)))
        print("Try adding a GitHub Personal Access Token for better API access")

# =============================================================================
# INSTRUCTIONS: How to add your GitHub Personal Access Token
# =============================================================================
"""
STEP 1: Get your GitHub Personal Access Token
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name it (e.g., "GitHub Export Tool")
4. Select scopes: ☑️ repo ☑️ user ☑️ read:org
5. Click "Generate token"
6. COPY the token immediately (you won't see it again!)

STEP 2: Add token to this script
Replace line 21:
GITHUB_TOKEN = "your_github_personal_access_token_here"

With your actual token:
GITHUB_TOKEN = "ghp_1234567890abcdef..."

STEP 3: Save and run
python github_repo_fixed_with_token.py

That's it! The script will now use your token for higher API limits.
"""
