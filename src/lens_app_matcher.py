#!/usr/bin/env python3
"""
Lens App Name Matcher

A tool for finding and extracting Kubernetes app.kubernetes.io/name label values from GitHub repositories.
"""

import os
import json
import re
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

import click
import requests
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

@dataclass
class CodeSearchResult:
    """Code search result structure"""
    file_path: str
    repository: str
    line_number: int
    matched_line: str
    context_lines: List[str]
    html_url: str
    extracted_values: List[str] = None

class GitHubAPIClient:
    """GitHub API client for fetching repository data"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        
        if self.token:
            self.session.headers.update({'Authorization': f'token {self.token}'})
        
        self.session.headers.update({
            'Accept': 'application/vnd.github.v3.text-match+json',
            'User-Agent': 'Lens-App-Name-Matcher'
        })
    
    def extract_label_value(self, text: str) -> Optional[str]:
        """Extract the value from a Kubernetes label string like 'app.kubernetes.io/name: "value"'"""
        # Pattern to match: app.kubernetes.io/name: "value" or app.kubernetes.io/name: value
        pattern = r'app\.kubernetes\.io/name:\s*["\']?([^"\'\s\n]+)["\']?'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else None
    
    def search_code(self, pattern: str, language: str = None, repo_filter: str = None, max_results: int = 100) -> List[CodeSearchResult]:
        """Search for code patterns using GitHub Code Search API"""
        results = []
        
        # Build search query
        query_parts = [f'"{pattern}"']
        if language:
            query_parts.append(f'language:{language}')
        if repo_filter:
            query_parts.append(f'repo:{repo_filter}')
        
        query = ' '.join(query_parts)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Searching code...", total=None)
            
            try:
                response = self.session.get(
                    f"{self.base_url}/search/code",
                    params={
                        'q': query,
                        'sort': 'indexed',
                        'order': 'desc',
                        'per_page': min(max_results, 100)
                    },
                    timeout=30
                )
                
                response.raise_for_status()
                data = response.json()
                
                if data.get('items'):
                    for item in data['items'][:max_results]:
                        # Extract context lines if available
                        context_lines = []
                        full_text = ""
                        if 'text_matches' in item:
                            for match in item['text_matches']:
                                if 'fragment' in match:
                                    context_lines.append(match['fragment'])
                                    full_text += match['fragment'] + "\n"
                        
                        # Extract label values if the pattern is a Kubernetes label
                        extracted_values = []
                        if 'app.kubernetes.io/name' in pattern:
                            for line in context_lines:
                                value = self.extract_label_value(line)
                                if value:
                                    extracted_values.append(value)
                        
                        results.append(CodeSearchResult(
                            file_path=item['path'],
                            repository=item['repository']['full_name'],
                            line_number=item.get('line_number', 0),
                            matched_line=item.get('name', ''),
                            context_lines=context_lines,
                            html_url=item['html_url'],
                            extracted_values=extracted_values
                        ))
                
                progress.update(task, description=f"Found {len(results)} code matches")
                
            except requests.RequestException as e:
                console.print(f"[red]Error searching code: {e}[/red]")
                if hasattr(e.response, 'status_code') and e.response.status_code == 403:
                    console.print("[yellow]Note: Code search requires authentication. Make sure GITHUB_TOKEN is set.[/yellow]")
        
        return results

@click.command()
@click.option('--pattern', '-p', required=True, help='Code pattern to search for (e.g., "app.kubernetes.io/name")')
@click.option('--language', '-l', help='Programming language to filter by')
@click.option('--repo', '-r', help='Specific repository to search (format: owner/repo)')
@click.option('--max-results', default=50, help='Maximum number of results to return')
@click.option('--output', '-o', help='Output file (JSON format)')
def search(pattern, language, repo, max_results, output):
    """Search for code patterns in GitHub repositories."""
    
    console.print("[bold blue]Lens App Name Matcher[/bold blue]")
    console.print(f"Searching for: [yellow]{pattern}[/yellow]")
    if language:
        console.print(f"Language: [cyan]{language}[/cyan]")
    if repo:
        console.print(f"Repository: [cyan]{repo}[/cyan]")
    console.print()
    
    # Initialize GitHub client and search for code
    client = GitHubAPIClient()
    results = client.search_code(pattern, language, repo, max_results)
    
    if not results:
        console.print("[red]No code matches found. Try adjusting your search criteria.[/red]")
        return
    
    console.print(f"[green]Found {len(results)} code matches[/green]")
    
    # Display results
    table = Table(title="Code Search Results")
    table.add_column("Repository", style="cyan", no_wrap=True)
    table.add_column("File Path", style="magenta")
    table.add_column("Context", style="white", max_width=50)
    if any(r.extracted_values for r in results):
        table.add_column("Extracted Values", style="green", no_wrap=True)
    table.add_column("URL", style="blue", no_wrap=True)
    
    for result in results:
        context = "\n".join(result.context_lines[:3]) if result.context_lines else result.matched_line
        # Truncate context if too long
        if len(context) > 150:
            context = context[:147] + "..."
        
        row_data = [
            result.repository,
            result.file_path,
            context
        ]
        
        if any(r.extracted_values for r in results):
            extracted_str = ", ".join(result.extracted_values) if result.extracted_values else ""
            row_data.append(extracted_str)
        
        row_data.append(result.html_url)
        table.add_row(*row_data)
    
    console.print()
    console.print(table)
    
    # Save to file if requested
    if output:
        result_data = {
            'pattern': pattern,
            'language': language,
            'repository_filter': repo,
            'results': [
                {
                    'repository': r.repository,
                    'file_path': r.file_path,
                    'line_number': r.line_number,
                    'matched_line': r.matched_line,
                    'context_lines': r.context_lines,
                    'extracted_values': r.extracted_values,
                    'html_url': r.html_url
                } for r in results
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        with open(output, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        console.print(f"\n[green]Results saved to {output}[/green]")

if __name__ == '__main__':
    search()
