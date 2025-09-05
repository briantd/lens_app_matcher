# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a Python-based Lens App Name Matcher that searches GitHub repositories to find and extract Kubernetes `app.kubernetes.io/name` label values. The tool uses GitHub's Code Search API to locate these labels in YAML files and extracts the actual string values assigned to them, helping discover naming patterns used in real-world Kubernetes applications.

## Architecture

The project follows a modular architecture with clear separation of concerns:

- **`src/lens_app_matcher.py`**: Main application containing:
  - `GitHubAPIClient`: Handles GitHub API interactions with authentication and code search capabilities
  - `CodeSearchResult`: Data structure for code search results with extracted values
  - `extract_label_value`: Method to extract Kubernetes label values from YAML content
  - CLI interface using Click for command-line interaction with search functionality

## Development Commands

### Environment Setup
```bash
# Install dependencies using uv (recommended)
uv sync

# Install with development dependencies (includes pytest)
uv sync --extra dev

# Alternative: Install with pip
pip install -e .
```

### Running the Application

**Kubernetes Label Search:**
```bash
# Search for Kubernetes app.kubernetes.io/name and app.kubernetes.io/component labels
uv run python src/lens_app_matcher.py -l yaml --max-results 50

# Search in a specific repository
uv run python src/lens_app_matcher.py -r "kubernetes/kubernetes" --output k8s_labels.json

# Search with language filter and tab-separated output
uv run python src/lens_app_matcher.py -l yaml --max-results 30 --tab-output labels.tsv
```

**Basic Commands:**
```bash
# Show all available commands
uv run python src/lens_app_matcher.py --help
```

### GitHub API Setup
The application requires a GitHub token for higher rate limits:
```bash
export GITHUB_TOKEN=your_github_token_here
```

### Development Workflow
```bash
# Show all available commands
uv run python src/lens_app_matcher.py --help

# Test code search functionality with language filter
uv run python src/lens_app_matcher.py -l yaml --max-results 10

# Search in specific repository
uv run python src/lens_app_matcher.py -r "owner/repo" -l yaml

# Generate both JSON and tab-separated output
uv run python src/lens_app_matcher.py -l yaml --output results.json --tab-output results.tsv
```

### Testing
```bash
# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run tests with coverage report
uv run pytest --cov=src --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_label_extraction.py

# Run specific test method
uv run pytest tests/test_label_extraction.py::TestLabelExtraction::test_extract_quoted_double_value
```

## Key Dependencies

- **requests**: GitHub API communication
- **click**: CLI interface and argument parsing
- **rich**: Enhanced terminal output with progress bars and tables
- **pyyaml**: Configuration file support (though config functionality is partially implemented)

## Project Structure

- Uses `uv` for modern Python dependency management
- Python 3.13+ required (specified in `.python-version`)
- Single-module architecture in `src/` directory
- Rich CLI interface with progress indicators and formatted output
- Supports JSON output for integration with other tools

## Important Implementation Details

### Label Value Extraction
The `extract_label_value` method implements pattern matching to extract Kubernetes label values:
1. **Quoted Values**: Matches `app.kubernetes.io/name: "value"` or `app.kubernetes.io/name: 'value'`
2. **Unquoted Values**: Matches `app.kubernetes.io/name: value` format
3. **Case Insensitive**: Works regardless of label key casing
4. **Context Aware**: Extracts values from YAML fragments returned by GitHub's API

### API Integration
- Uses GitHub Code Search API with proper authentication
- Implements proper rate limiting and error handling
- Searches code content by patterns, language, and repository filters
- Extracts meaningful label values from YAML content while filtering template variables

## Configuration

The application supports YAML configuration files (via `--config` flag), though the feature is partially implemented. Configuration structure should include:
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

## Data Flow

1. **Query Construction**: CLI arguments build GitHub code search query
2. **API Fetching**: `GitHubAPIClient` retrieves code search results with progress tracking
3. **Pattern Analysis**: `extract_label_value()` extracts Kubernetes label values from YAML fragments
4. **Value Extraction**: Meaningful app names are extracted from matched code patterns
5. **Output**: Rich table display with repository, file path, extracted values, and context
