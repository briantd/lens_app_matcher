# GitHub App Name Generator

A tool for generating creative and meaningful application names based on GitHub project data and patterns.

## Overview

This project analyzes GitHub repositories to suggest potential application names by examining:
- Repository names and patterns
- Project descriptions and topics
- Popular naming conventions
- Domain-specific terminology

## Features

- **GitHub API Integration**: Fetch repository data and metadata
- **Name Pattern Analysis**: Extract common naming patterns from successful projects
- **Smart Suggestions**: Generate contextually relevant app names
- **Filtering Options**: Filter by language, topic, or project type
- **Export Capabilities**: Save generated names to various formats

## Prerequisites

- Python 3.8+ (or Node.js 16+ if using JavaScript implementation)
- GitHub API token (for higher rate limits)
- Internet connection for API access

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd github-app-name-generator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # or
   npm install
   ```

3. Set up GitHub API token:
   ```bash
   export GITHUB_TOKEN=your_github_token_here
   ```

## Usage

### Basic Usage

```bash
python src/name_generator.py --topic web --count 10
```

### Advanced Options

```bash
python src/name_generator.py \
  --topic "machine learning" \
  --language python \
  --min-stars 100 \
  --count 20 \
  --output names.json
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

Generate names for a web development project:
```bash
python src/name_generator.py --topic web --language javascript
```

Output:
```
Suggested App Names:
1. WebCraftJS
2. ReactFlow
3. VueForge
4. NextGenWeb
5. StackBuilder
...
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

- [ ] Add support for GitLab and Bitbucket
- [ ] Implement ML-based name generation
- [ ] Add name availability checking
- [ ] Create web interface
- [ ] Add name scoring and ranking
