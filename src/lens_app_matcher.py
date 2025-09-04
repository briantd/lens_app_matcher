#!/usr/bin/env python3
"""
Lens App Name Matcher

A tool for finding and extracting Kubernetes app.kubernetes.io/name label values from GitHub repositories.
"""

import os
import json
import re
import hashlib
import base64
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

import click
import requests
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def md5_and_base64encode(text: str) -> tuple:
    """Create MD5 hash of text and Base64-encode the MD5 hash.
    
    Returns:
        tuple: (md5_hash, base64_encoded_md5)
    """
    # Create MD5 hash
    md5_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    
    # Base64-encode the MD5 hash using the built-in base64 module
    input_bytes = md5_hash.encode('utf-8')
    base64_encoded = base64.b64encode(input_bytes).decode('utf-8')
    
    return md5_hash, base64_encoded

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
    extracted_names: List[str] = None
    extracted_components: List[str] = None

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
    
    def extract_label_value(self, text: str, label_key: str) -> Optional[str]:
        """Extract the value from a Kubernetes label string like 'app.kubernetes.io/name: "value"' or 'app.kubernetes.io/component: "value"'"""
        # Escape the label key for regex
        escaped_key = re.escape(label_key)
        # Pattern to match: app.kubernetes.io/name: "value" or app.kubernetes.io/name: value  
        pattern = f'{escaped_key}:\\s*["\']?([^"\'\\s\\n]+)["\']?'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else None
    
    def search_kubernetes_labels(self, language: str = None, repo_filter: str = None, max_results: int = 100) -> List[CodeSearchResult]:
        """Search for both app.kubernetes.io/name and app.kubernetes.io/component labels using GitHub Code Search API"""
        # Combine both patterns into a single OR query for better efficiency
        query_parts = ['"app.kubernetes.io/name" OR "app.kubernetes.io/component"']
        
        if language:
            query_parts.append(f'language:{language}')
        if repo_filter:
            query_parts.append(f'repo:{repo_filter}')
        
        query = ' '.join(query_parts)
        
        # Single API call instead of multiple calls
        return self._search_combined_patterns(query, max_results)
    
    def _search_combined_patterns(self, query: str, max_results: int) -> List[CodeSearchResult]:
        """Search for combined patterns and extract both name and component values from results"""
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Searching Kubernetes labels...", total=None)
            
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
                        if 'text_matches' in item:
                            for match in item['text_matches']:
                                if 'fragment' in match:
                                    context_lines.append(match['fragment'])
                        
                        # Always extract BOTH name and component values from all context lines
                        extracted_names = []
                        extracted_components = []
                        extracted_values = []  # Combined for backward compatibility
                        
                        for line in context_lines:
                            # Extract name values
                            name_value = self.extract_label_value(line, 'app.kubernetes.io/name')
                            if name_value:
                                extracted_names.append(name_value)
                                extracted_values.append(f"name:{name_value}")
                                
                            # Extract component values
                            component_value = self.extract_label_value(line, 'app.kubernetes.io/component')
                            if component_value:
                                extracted_components.append(component_value)
                                extracted_values.append(f"component:{component_value}")
                        
                        results.append(CodeSearchResult(
                            file_path=item['path'],
                            repository=item['repository']['full_name'],
                            line_number=item.get('line_number', 0),
                            matched_line=item.get('name', ''),
                            context_lines=context_lines,
                            html_url=item['html_url'],
                            extracted_values=extracted_values,
                            extracted_names=extracted_names,
                            extracted_components=extracted_components
                        ))
                
                progress.update(task, description=f"Found {len(results)} matches for Kubernetes labels")
                
            except requests.RequestException as e:
                console.print(f"[red]Error searching code: {e}[/red]")
                if hasattr(e.response, 'status_code') and e.response.status_code == 403:
                    console.print("[yellow]Note: Code search requires authentication. Make sure GITHUB_TOKEN is set.[/yellow]")
        
        return results

@click.command()
@click.option('--language', '-l', help='Programming language to filter by')
@click.option('--repo', '-r', help='Specific repository to search (format: owner/repo)')
@click.option('--max-results', default=50, help='Maximum number of results to return')
@click.option('--output', '-o', help='Output file (JSON format)')
@click.option('--tab-output', '-t', help='Output file for tab-separated values with MD5 and UU-encoded data')
def search(language, repo, max_results, output, tab_output):
    """Search for Kubernetes app.kubernetes.io/name and app.kubernetes.io/component labels in GitHub repositories."""
    
    console.print("[bold blue]Lens App Name Matcher[/bold blue]")
    console.print("Searching for: [yellow]app.kubernetes.io/name[/yellow] and [yellow]app.kubernetes.io/component[/yellow]")
    if language:
        console.print(f"Language: [cyan]{language}[/cyan]")
    if repo:
        console.print(f"Repository: [cyan]{repo}[/cyan]")
    console.print()
    
    # Initialize GitHub client and search for both patterns
    client = GitHubAPIClient()
    results = client.search_kubernetes_labels(language, repo, max_results)
    
    if not results:
        console.print("[red]No code matches found. Try adjusting your search criteria.[/red]")
        return
    
    console.print(f"[green]Found {len(results)} code matches[/green]")
    
    # Display results
    table = Table(title="Code Search Results")
    table.add_column("Repository", style="cyan", no_wrap=True)
    table.add_column("File Path", style="magenta")
    table.add_column("Context", style="white", max_width=50)
    if any(r.extracted_names for r in results):
        table.add_column("App Names", style="green", no_wrap=True)
    if any(r.extracted_components for r in results):
        table.add_column("Components", style="yellow", no_wrap=True)
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
        
        if any(r.extracted_names for r in results):
            names_str = ", ".join(result.extracted_names) if result.extracted_names else ""
            row_data.append(names_str)
            
        if any(r.extracted_components for r in results):
            components_str = ", ".join(result.extracted_components) if result.extracted_components else ""
            row_data.append(components_str)
        
        row_data.append(result.html_url)
        table.add_row(*row_data)
    
    console.print()
    console.print(table)
    
    # Save to file if requested
    if output:
        result_data = {
            'search_patterns': ['app.kubernetes.io/name', 'app.kubernetes.io/component'],
            'language': language,
            'repository_filter': repo,
            'results': [
                {
                    'repository': r.repository,
                    'file_path': r.file_path,
                    'line_number': r.line_number,
                    'matched_line': r.matched_line,
                    'context_lines': r.context_lines,
                    'extracted_names': r.extracted_names,
                    'extracted_components': r.extracted_components,
                    'extracted_values': r.extracted_values,  # Keep for backward compatibility
                    'html_url': r.html_url
                } for r in results
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        with open(output, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        console.print(f"\n[green]Results saved to {output}[/green]")
    
    # Save tab-separated file if requested
    if tab_output:
        # Collect all label values with their source information
        label_entries = []
        
        for result in results:
            # Add names with repository info
            if result.extracted_names:
                for name in result.extracted_names:
                    label_entries.append({
                        'type': 'name',
                        'value': name,
                        'repository': result.repository,
                        'url': result.html_url
                    })
            
            # Add components with repository info
            if result.extracted_components:
                for component in result.extracted_components:
                    label_entries.append({
                        'type': 'component',
                        'value': component,
                        'repository': result.repository,
                        'url': result.html_url
                    })
        
        if label_entries:
            # Sort by type, then by value, then by repository
            label_entries.sort(key=lambda x: (x['type'], x['value'], x['repository']))
            
            with open(tab_output, 'w') as f:
                # Write header
                f.write("Label_Type\tLabel_Value\tRepository\tURL\tMD5_Hash\tBase64_Encoded_MD5\n")
                
                # Write all entries
                for entry in label_entries:
                    md5_hash, base64_encoded = md5_and_base64encode(entry['value'])
                    f.write(f"{entry['type']}\t{entry['value']}\t{entry['repository']}\t{entry['url']}\t{md5_hash}\t{base64_encoded}\n")
            
            # Count unique values
            unique_names = len(set(e['value'] for e in label_entries if e['type'] == 'name'))
            unique_components = len(set(e['value'] for e in label_entries if e['type'] == 'component'))
            total_entries = len(label_entries)
            unique_names + unique_components
            
            console.print(f"[green]Tab-separated output saved to {tab_output}[/green]")
            console.print(f"[cyan]Found {unique_names} unique names and {unique_components} unique components[/cyan]")
            console.print(f"[cyan]Total entries: {total_entries} (including duplicates across repositories)[/cyan]")
        else:
            console.print("[yellow]No extracted values found for tab-separated output[/yellow]")

if __name__ == '__main__':
    search()
