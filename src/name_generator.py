#!/usr/bin/env python3
"""
GitHub App Name Generator

A tool for generating creative application names based on GitHub project data.
"""

import os
import sys
import json
import re
import random
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

import click
import requests
import yaml
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

@dataclass
class RepoData:
    """Repository data structure"""
    name: str
    description: str
    language: str
    stars: int
    topics: List[str]
    full_name: str

class GitHubAPIClient:
    """GitHub API client for fetching repository data"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        
        if self.token:
            self.session.headers.update({'Authorization': f'token {self.token}'})
        
        self.session.headers.update({
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-App-Name-Generator'
        })
    
    def search_repositories(self, query: str, per_page: int = 100, max_pages: int = 5) -> List[RepoData]:
        """Search for repositories matching the query"""
        repos = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Fetching repositories...", total=None)
            
            for page in range(1, max_pages + 1):
                try:
                    response = self.session.get(
                        f"{self.base_url}/search/repositories",
                        params={
                            'q': query,
                            'sort': 'stars',
                            'order': 'desc',
                            'per_page': per_page,
                            'page': page
                        },
                        timeout=30
                    )
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    if not data.get('items'):
                        break
                    
                    for item in data['items']:
                        repos.append(RepoData(
                            name=item['name'],
                            description=item.get('description', ''),
                            language=item.get('language', ''),
                            stars=item.get('stargazers_count', 0),
                            topics=item.get('topics', []),
                            full_name=item['full_name']
                        ))
                    
                    progress.update(task, description=f"Fetched {len(repos)} repositories...")
                    
                except requests.RequestException as e:
                    console.print(f"[red]Error fetching data: {e}[/red]")
                    break
        
        return repos

class NameGenerator:
    """Generate app names based on repository data"""
    
    def __init__(self):
        self.name_patterns = []
        self.word_combinations = set()
        self.common_suffixes = ['app', 'hub', 'kit', 'craft', 'forge', 'lab', 'studio', 'works']
        self.common_prefixes = ['super', 'ultra', 'mega', 'pro', 'smart', 'quick', 'fast', 'easy']
        
    def analyze_repositories(self, repos: List[RepoData]) -> None:
        """Analyze repository names to extract patterns"""
        for repo in repos:
            # Extract words from repository names
            words = self._extract_words(repo.name)
            self.word_combinations.update(words)
            
            # Extract words from descriptions
            if repo.description:
                desc_words = self._extract_words(repo.description)
                self.word_combinations.update(desc_words[:5])  # Limit description words
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract meaningful words from text"""
        if not text:
            return []
        
        # Split on common delimiters and convert to lowercase
        words = re.findall(r'[a-zA-Z]+', text.lower())
        
        # Filter out common words and very short words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        
        return [word for word in words if len(word) > 2 and word not in stop_words]
    
    def generate_names(self, count: int = 10, topic_filter: Optional[str] = None) -> List[str]:
        """Generate creative app names"""
        names = set()
        word_list = list(self.word_combinations)
        
        if topic_filter:
            # Filter words related to the topic
            topic_words = [w for w in word_list if topic_filter.lower() in w or w in topic_filter.lower()]
            if topic_words:
                word_list = topic_words + random.sample(word_list, min(50, len(word_list)))
        
        generation_strategies = [
            self._compound_names,
            self._prefix_suffix_names,
            self._tech_fusion_names,
            self._descriptive_names
        ]
        
        attempts = 0
        max_attempts = count * 10
        
        while len(names) < count and attempts < max_attempts:
            strategy = random.choice(generation_strategies)
            name = strategy(word_list)
            if name and len(name) > 3:
                names.add(name.title())
            attempts += 1
        
        return list(names)[:count]
    
    def _compound_names(self, words: List[str]) -> str:
        """Generate compound names by combining two words"""
        if len(words) < 2:
            return ""
        
        word1 = random.choice(words)
        word2 = random.choice([w for w in words if w != word1])
        
        return word1.capitalize() + word2.capitalize()
    
    def _prefix_suffix_names(self, words: List[str]) -> str:
        """Generate names with common prefixes/suffixes"""
        if not words:
            return ""
        
        base_word = random.choice(words)
        
        if random.choice([True, False]):
            # Add prefix
            prefix = random.choice(self.common_prefixes)
            return prefix.capitalize() + base_word.capitalize()
        else:
            # Add suffix
            suffix = random.choice(self.common_suffixes)
            return base_word.capitalize() + suffix.capitalize()
    
    def _tech_fusion_names(self, words: List[str]) -> str:
        """Generate tech-sounding fusion names"""
        if len(words) < 2:
            return ""
        
        word1 = random.choice(words)
        word2 = random.choice([w for w in words if w != word1])
        
        # Take part of first word + part of second word
        part1 = word1[:len(word1)//2 + 1] if len(word1) > 3 else word1
        part2 = word2[len(word2)//2:] if len(word2) > 3 else word2
        
        return (part1 + part2).capitalize()
    
    def _descriptive_names(self, words: List[str]) -> str:
        """Generate descriptive names with tech suffixes"""
        if not words:
            return ""
        
        base_word = random.choice(words)
        tech_suffixes = ['ly', 'io', 'ify', 'js', 'go', 'py', 'rs']
        
        if random.choice([True, False]) and base_word.endswith('e'):
            return base_word[:-1] + random.choice(tech_suffixes)
        else:
            return base_word + random.choice(tech_suffixes)

@click.command()
@click.option('--topic', '-t', help='Topic or technology to focus on (e.g., "web", "machine learning")')
@click.option('--language', '-l', help='Programming language to filter by')
@click.option('--min-stars', default=10, help='Minimum number of stars for repositories')
@click.option('--count', '-c', default=10, help='Number of names to generate')
@click.option('--output', '-o', help='Output file (JSON format)')
@click.option('--config', help='Configuration file path')
def main(topic, language, min_stars, count, output, config):
    """Generate creative app names based on GitHub repository data."""
    
    # Load configuration if provided
    settings = {}
    if config and Path(config).exists():
        with open(config, 'r') as f:
            settings = yaml.safe_load(f)
    
    # Build search query
    query_parts = []
    if topic:
        query_parts.append(f'"{topic}"')
    if language:
        query_parts.append(f'language:{language}')
    if min_stars > 0:
        query_parts.append(f'stars:>={min_stars}')
    
    if not query_parts:
        query_parts.append('stars:>=100')  # Default to popular repos
    
    query = ' '.join(query_parts)
    
    console.print(f"[bold blue]GitHub App Name Generator[/bold blue]")
    console.print(f"Search query: [yellow]{query}[/yellow]")
    console.print()
    
    # Initialize GitHub client and fetch data
    client = GitHubAPIClient()
    repos = client.search_repositories(query, max_pages=3)
    
    if not repos:
        console.print("[red]No repositories found. Try adjusting your search criteria.[/red]")
        return
    
    console.print(f"[green]Found {len(repos)} repositories[/green]")
    
    # Generate names
    generator = NameGenerator()
    generator.analyze_repositories(repos)
    names = generator.generate_names(count, topic)
    
    # Display results
    table = Table(title="Generated App Names")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Variations", style="magenta")
    
    for i, name in enumerate(names, 1):
        variations = [
            name.lower(),
            name.replace(' ', '-').lower(),
            name.replace(' ', '_').lower()
        ]
        table.add_row(f"{i}. {name}", " | ".join(variations))
    
    console.print()
    console.print(table)
    
    # Save to file if requested
    if output:
        result = {
            'query': query,
            'repository_count': len(repos),
            'generated_names': names,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(output, 'w') as f:
            json.dump(result, f, indent=2)
        
        console.print(f"\n[green]Results saved to {output}[/green]")

if __name__ == '__main__':
    main()
