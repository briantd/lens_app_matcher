# Lens App Name Matcher

A tool for finding and extracting Kubernetes `app.kubernetes.io/name` label values from GitHub repositories.

## Overview

This project searches GitHub repositories to find instances of the `app.kubernetes.io/name` Kubernetes label and extracts the actual string values assigned to it. This is useful for discovering naming patterns and conventions used in real-world Kubernetes applications.

## Features

- **GitHub Code Search Integration**: Uses GitHub's Code Search API to find label patterns
- **Value Extraction**: Automatically extracts the actual values assigned to `app.kubernetes.io/name` labels
- **Rich Display**: Shows results in a formatted table with repository, file path, extracted values, and context
- **Filtering Options**: Filter by programming language or specific repositories
- **Export Capabilities**: Save search results to JSON format

## Prerequisites

- Python 3.13+
- GitHub API token (required for code search)
- Internet connection for API access

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd lens-app-name-matcher
   ```

2. Install dependencies using uv:
   ```bash
   uv sync
   ```

3. Set up GitHub API token:
   ```bash
   export GITHUB_TOKEN=your_github_token_here
   ```

## Usage

### Basic Usage

```bash
uv run python src/lens_app_matcher.py -l yaml
```

### Advanced Options

```bash
# Search for Kubernetes labels in YAML files with higher result limit
uv run python src/lens_app_matcher.py -l yaml --max-results 50

# Search in a specific repository
uv run python src/lens_app_matcher.py -r "kubernetes/kubernetes" --output results.json

# Search with custom result limit and save to file
uv run python src/lens_app_matcher.py -l yaml --max-results 100 --output k8s_labels.json

# Generate tab-separated output with MD5 hashes
uv run python src/lens_app_matcher.py -l yaml --max-results 30 --tab-output labels.tsv
```

## Configuration

Configure the tool using `config/settings.yaml`:

```yaml
github:
  api_url: "https://api.github.com"
  timeout: 30
  
generation:
  default_count: 10
  max_count: 100
  
filters:
  min_stars: 10
  languages: ["python", "javascript", "go", "rust"]
```

## Examples

Search for Kubernetes app name and component labels:
```bash
uv run python src/lens_app_matcher.py -l yaml --max-results 20
```

Output:
```
┌─────────────────────────────────────────┬──────────────────────────────┬──────────────────┬────────────────────────────────────────┐
│ Repository                              │ File Path                    │ Extracted Values │ Context                                │
├─────────────────────────────────────────┼──────────────────────────────┼──────────────────┼────────────────────────────────────────┤
│ kubernetes/examples                     │ staging/volumes/nfs/nfs.yaml │ nfs-server       │ app.kubernetes.io/name: nfs-server     │
│ helm/charts                             │ stable/mysql/values.yaml     │ mysql            │ app.kubernetes.io/name: mysql          │
│ kubernetes-sigs/aws-load-balancer...    │ docs/examples/game.yaml      │ "2048"           │ app.kubernetes.io/name: "2048"         │
└─────────────────────────────────────────┴──────────────────────────────┴──────────────────┴────────────────────────────────────────┘
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Roadmap

- [ ] Support for other Kubernetes labels (app.kubernetes.io/component, app.kubernetes.io/part-of, etc.)
- [ ] Add filtering by star count and repository activity
- [ ] Statistical analysis of naming patterns
- [ ] Export to different formats (CSV, Excel)
- [ ] Web interface for easier searching
- [ ] Integration with Kubernetes lens for direct import
