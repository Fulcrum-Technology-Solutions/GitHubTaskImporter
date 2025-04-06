# GitHub Task Creator

A Python utility to create GitHub issues in bulk from a CSV file.

## Features

- Creates GitHub issues from a CSV file
- Supports setting issue properties:
  - Title
  - Description
  - Assignees (multiple, comma-separated)
  - Labels (multiple, comma-separated)
  - Type (added as an additional label)
  - Milestone

## Requirements

- Python 3.6+
- `requests` library: `pip install requests`

## Usage

1. Create a CSV file with your tasks. See `sample_tasks.csv` for the expected format.
2. Run the script:
   ```
   python github_task_creator.py
   ```
3. Enter the requested information:
   - GitHub API token (see Token Permissions below)
   - Organization name
   - Repository name
   - Path to your CSV file

## Token Permissions

Create a fine-grained personal access token with these permissions:
- Repository access: Select specific repository you want to modify
- Repository permissions:
  - Contents: Read and write
  - Issues: Read and write (required for creating issues, editing issues, assigning issues)
  - Metadata: Read-only (required for API access, mandatory)
  - Milestone: Read and write (for milestone creation)

## CSV Format

Your CSV file should include the following columns:

```
title,description,assignee,labels,type,milestone
```

Example:
```
title,description,assignee,labels,type,milestone
Setup project repository,Create initial project structure and documentation,johndoe,setup,infrastructure,Sprint 1
```

- For multiple assignees, use a comma-separated list: `johndoe,janedoe`
- For multiple labels, use a comma-separated list: `bug,frontend`

## Notes

- **Type Field**: The "type" field from the CSV is sent as the issue type. Note that according to GitHub's API, "Only users with push access can set the type for new issues. The type is silently dropped otherwise."
- **Milestone Creation**: If a milestone does not exist, the script will automatically create it.
- **API Token**: Make sure your token has appropriate permissions as described in the Token Permissions section.
- **Projects**: Project functionality has been removed. The script does not support adding issues to projects.