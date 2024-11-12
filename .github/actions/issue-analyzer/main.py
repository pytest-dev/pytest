#!/usr/bin/env python3

import os
import sys
import json
from typing import Dict, Any
from anthropic import Anthropic
from github import Github
from github.Issue import Issue

def get_github_event() -> Dict[str, Any]:
    """Read GitHub event data from the event file."""
    event_path = os.getenv('GITHUB_EVENT_PATH')
    if not event_path:
        raise ValueError("GITHUB_EVENT_PATH not set")
    
    with open(event_path, 'r') as f:
        return json.load(f)

def analyze_issue_with_claude(issue_title: str, issue_body: str) -> str:
    anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    # FIXME - Add actual prompt here
    prompt = f"""You are an AI assistant helping open source maintainers clarify GitHub issues.
    Please analyze this issue and identify what information is missing or needs clarification.
    Focus on technical details, reproduction steps, and system information that would help resolve the issue.

    Issue Title: {issue_title}
    Issue Body: {issue_body}

    Please provide a response in the following format:
    1. Missing Information (bullet points of what's needed)
    2. Clarifying Questions (specific questions to ask the issue author)
    3. Next Steps (suggested actions for the issue author)"""

    message = anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    
    return message.content[0].text

def post_comment(issue: Issue, analysis: str):
    """Post Claude's analysis as a comment on the issue."""
    comment_body = f"""Hello! 👋 I'm an AI assistant helping to analyze this issue.

{analysis}

Note: I'm an automated assistant helping to gather information. A maintainer will review this issue soon."""
    
    issue.create_comment(comment_body)

def main():
    try:
        # Get GitHub token and create GitHub client
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            raise ValueError("GITHUB_TOKEN not set")
        
        gh = Github(github_token)
        
        # Get event data
        event = get_github_event()
        issue_data = event['issue']
        
        # Get repository info
        repo_name = os.getenv('GITHUB_REPOSITORY')
        if not repo_name:
            raise ValueError("GITHUB_REPOSITORY not set")
        
        repo = gh.get_repo(repo_name)
        issue = repo.get_issue(number=issue_data['number'])
        
        # Analyze issue with Claude
        analysis = analyze_issue_with_claude(
            issue_title=issue_data['title'],
            issue_body=issue_data['body']
        )
        
        # Post the analysis as a comment
        post_comment(issue, analysis)
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()