#!/usr/bin/env python3
import csv
import requests
import sys
import getpass
from typing import Dict, List, Any, Optional

def get_user_input() -> Dict[str, str]:
    """Get required user information for GitHub API authentication and repository details."""
    token = getpass.getpass("Enter your GitHub API token: ")
    # Sanitize token to ensure it only contains valid characters
    token = ''.join(c for c in token if c.isalnum() or c in '-._~+/')
    
    org = input("Enter GitHub organization name: ")
    repo = input("Enter repository name: ")
    csv_file = input("Enter path to CSV file with tasks: ")
    
    # Verify input data
    if not token:
        print("Error: GitHub API token is required.")
        sys.exit(1)
    if not org:
        print("Error: GitHub organization name is required.")
        sys.exit(1)
    if not repo:
        print("Error: GitHub repository name is required.")
        sys.exit(1)
    if not csv_file:
        print("Error: CSV file path is required.")
        sys.exit(1)
    
    return {
        "token": token,
        "org": org,
        "repo": repo,
        "csv_file": csv_file
    }

def read_tasks_from_csv(csv_file: str) -> List[Dict[str, Any]]:
    """Read tasks from a CSV file."""
    tasks = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Print header info for debugging
            print(f"CSV Headers: {reader.fieldnames}")
            
            for row in reader:
                # Ensure all keys are lowercase to avoid case-sensitivity issues
                normalized_row = {k.lower(): v for k, v in row.items()}
                tasks.append(normalized_row)
                
        # Debug the first task
        if tasks:
            print(f"First task values: {tasks[0]}")
            
        return tasks
    except FileNotFoundError:
        print(f"Error: CSV file {csv_file} not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

def create_github_issue(auth_data: Dict[str, str], task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a GitHub issue using the GitHub API."""
    url = f"https://api.github.com/repos/{auth_data['org']}/{auth_data['repo']}/issues"
    
    # Use basic ASCII-only headers to avoid Unicode encoding issues
    # Ensure token is ASCII-encodable
    sanitized_token = ''.join(c for c in auth_data['token'] if ord(c) < 128)
    
    headers = {
        "Authorization": "token " + sanitized_token,
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Verify repo exists before creating issues
    repo_url = f"https://api.github.com/repos/{auth_data['org']}/{auth_data['repo']}"
    try:
        repo_response = requests.get(repo_url, headers=headers)
        repo_response.raise_for_status()
        print(f"Repository {auth_data['org']}/{auth_data['repo']} verified!")
    except requests.exceptions.RequestException as e:
        print(f"Error: Repository {auth_data['org']}/{auth_data['repo']} not found or not accessible.")
        print(f"Response: {e.response.text if hasattr(e, 'response') and e.response else 'No response'}")
        print("Please check the organization name, repository name, and your API token permissions.")
        return None
    
    # Prepare assignees (comma-separated list in CSV)
    assignees = [a.strip() for a in task.get('assignee', '').split(',')] if task.get('assignee') else []
    assignees = [a for a in assignees if a]  # Remove empty values
    
    # Prepare labels (comma-separated list in CSV)
    labels = []
    if task.get('labels'):
        labels = [l.strip() for l in task.get('labels', '').split(',') if l.strip()]
    
    # Debug the TYPE field specifically
    print("  - Original type value:", repr(task.get('type', 'None')))
    
    # Handle type field - set as issue type (GitHub API parameter)
    type_value = None
    if 'type' in task and task['type'] and isinstance(task['type'], str):
        type_value = task['type'].strip()
        print("  - Type (setting as issue type):", repr(type_value))
    
    # Create the base issue data
    issue_data = {
        "title": task.get('title', 'Untitled Task'),
        "body": task.get('description', ''),
        "assignees": assignees,
        "labels": labels
    }
    
    # Add type as a separate field if available
    if type_value:
        issue_data["type"] = type_value
    
    # Special debug for labels
    print("  - Final labels to be set:", repr(labels))
    
    # Debug output
    print("  - Title:", issue_data['title'])
    print("  - Body length:", len(issue_data['body']), "characters")
    print("  - Assignees:", ', '.join(assignees) if assignees else 'None')
    print("  - Labels:", ', '.join(labels) if labels else 'None')
    if "type" in issue_data:
        print("  - Type:", issue_data["type"])
    
    # Add milestone if provided
    if task.get('milestone') and task.get('milestone').strip():
        milestone_title = task.get('milestone').strip()
        print("  - Milestone:", milestone_title)
        milestone_id = get_milestone_id(auth_data, milestone_title)
        if milestone_id:
            issue_data["milestone"] = milestone_id
            print("  - Milestone ID:", milestone_id)
        else:
            print("  - Unable to set milestone:", milestone_title)
    
    try:
        # Create issue
        response = requests.post(url, headers=headers, json=issue_data)
        response.raise_for_status()
        
        issue = response.json()
        print("  + Created issue #" + str(issue['number']) + ": " + issue['html_url'])
        return issue
    except requests.exceptions.RequestException as e:
        print(f"Error creating issue '{task.get('title', 'Untitled Task')}': {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None

def get_milestone_id(auth_data: Dict[str, str], milestone_title: str) -> Optional[int]:
    """Get milestone ID by title."""
    url = f"https://api.github.com/repos/{auth_data['org']}/{auth_data['repo']}/milestones?state=all"
    
    # Ensure token is ASCII-encodable
    sanitized_token = ''.join(c for c in auth_data['token'] if ord(c) < 128)
    
    headers = {
        "Authorization": "token " + sanitized_token,
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        milestones = response.json()
        for milestone in milestones:
            if milestone["title"].lower() == milestone_title.lower():
                return milestone["number"]
        
        # If not found, create the milestone
        print("Milestone '" + milestone_title + "' not found. Creating it...")
        create_url = f"https://api.github.com/repos/{auth_data['org']}/{auth_data['repo']}/milestones"
        milestone_data = {
            "title": milestone_title,
            "state": "open",
            "description": "Auto-created milestone: " + milestone_title
        }
        create_response = requests.post(create_url, headers=headers, json=milestone_data)
        create_response.raise_for_status()
        new_milestone = create_response.json()
        print("Created milestone '" + milestone_title + "' with ID " + str(new_milestone['number']))
        return new_milestone["number"]
    except requests.exceptions.RequestException as e:
        print("Error with milestones:", e)
        if hasattr(e, 'response') and e.response is not None:
            print("Response:", e.response.text)
        return None

# Projects functionality removed as per user request

def main():
    print("GitHub Task Creator")
    print("==================")
    
    # Get authentication information and repository details
    auth_data = get_user_input()
    
    # Read tasks from CSV
    tasks = read_tasks_from_csv(auth_data["csv_file"])
    
    # Create GitHub issues for each task
    print(f"\nCreating {len(tasks)} tasks in {auth_data['org']}/{auth_data['repo']}...")
    
    success_count = 0
    for i, task in enumerate(tasks, 1):
        print(f"Creating task {i}/{len(tasks)}: {task.get('title', 'Untitled Task')}")
        result = create_github_issue(auth_data, task)
        if result:
            success_count += 1
            print(f"  ✓ Created issue #{result['number']}: {result['html_url']}")
    
    print(f"\nCreated {success_count} out of {len(tasks)} tasks successfully.")

if __name__ == "__main__":
    main()