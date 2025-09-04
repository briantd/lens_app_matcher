#!/usr/bin/env python3
"""
Unit tests for label value extraction functionality in lens_app_matcher.

Tests the GitHubAPIClient.extract_label_value method with various 
Kubernetes YAML label formats.
"""

import pytest
import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from lens_app_matcher import GitHubAPIClient


class TestLabelExtraction:
    """Test cases for Kubernetes label value extraction."""
    
    @pytest.fixture
    def client(self):
        """Create a GitHubAPIClient instance for testing."""
        return GitHubAPIClient()
    
    def test_extract_quoted_double_value(self, client):
        """Test extraction of double-quoted label values."""
        text = 'app.kubernetes.io/name: "nginx"'
        result = client.extract_label_value(text, 'app.kubernetes.io/name')
        assert result == "nginx"
    
    def test_extract_quoted_single_value(self, client):
        """Test extraction of single-quoted label values."""
        text = "app.kubernetes.io/name: 'redis'"
        result = client.extract_label_value(text, 'app.kubernetes.io/name')
        assert result == "redis"
    
    def test_extract_unquoted_value(self, client):
        """Test extraction of unquoted label values."""
        text = "app.kubernetes.io/name: postgres"
        result = client.extract_label_value(text, 'app.kubernetes.io/name')
        assert result == "postgres"
    
    def test_extract_with_whitespace(self, client):
        """Test extraction with leading/trailing whitespace."""
        text = "  app.kubernetes.io/name: \"my-app\"  "
        result = client.extract_label_value(text, 'app.kubernetes.io/name')
        assert result == "my-app"
    
    def test_extract_with_indentation(self, client):
        """Test extraction from indented YAML."""
        text = "    app.kubernetes.io/name: web-server"
        result = client.extract_label_value(text, 'app.kubernetes.io/name')
        assert result == "web-server"
    
    def test_extract_from_multiline_yaml(self, client):
        """Test extraction from multiline YAML context."""
        text = """metadata:
  labels:
    app.kubernetes.io/name: web-server
    app.kubernetes.io/version: v1.0"""
        result = client.extract_label_value(text, 'app.kubernetes.io/name')
        assert result == "web-server"
    
    def test_extract_case_insensitive(self, client):
        """Test that extraction is case insensitive."""
        text = "APP.KUBERNETES.IO/NAME: backend-service"
        result = client.extract_label_value(text, 'app.kubernetes.io/name')
        assert result == "backend-service"
    
    def test_extract_with_hyphens_and_numbers(self, client):
        """Test extraction of values with hyphens and numbers."""
        text = 'app.kubernetes.io/name: "my-app-v2"'
        result = client.extract_label_value(text, 'app.kubernetes.io/name')
        assert result == "my-app-v2"
    
    def test_extract_no_match(self, client):
        """Test extraction when no label is present."""
        text = "some.other.label: value"
        result = client.extract_label_value(text, 'app.kubernetes.io/name')
        assert result is None
    
    def test_extract_empty_string(self, client):
        """Test extraction from empty string."""
        text = ""
        result = client.extract_label_value(text, 'app.kubernetes.io/name')
        assert result is None
    
    def test_extract_malformed_label(self, client):
        """Test extraction from malformed label syntax."""
        text = "app.kubernetes.io/name:"  # No value
        result = client.extract_label_value(text, 'app.kubernetes.io/name')
        assert result is None
    
    @pytest.mark.parametrize("test_input,expected", [
        ('app.kubernetes.io/name: "nginx"', "nginx"),
        ("app.kubernetes.io/name: 'redis'", "redis"),
        ('app.kubernetes.io/name: postgres', "postgres"),
        ('  app.kubernetes.io/name: "my-app"', "my-app"),
        ('app.kubernetes.io/name: web-server-123', "web-server-123"),
        ('APP.KUBERNETES.IO/NAME: UPPERCASE', "UPPERCASE"),
        ('no match here', None),
        ('', None),
    ])
    def test_extract_parametrized(self, client, test_input, expected):
        """Parametrized test for various label extraction scenarios."""
        result = client.extract_label_value(test_input, 'app.kubernetes.io/name')
        assert result == expected
    
    def test_extract_multiple_occurrences(self, client):
        """Test that extraction finds the first occurrence."""
        text = """app.kubernetes.io/name: first-app
some other content
app.kubernetes.io/name: second-app"""
        result = client.extract_label_value(text, 'app.kubernetes.io/name')
        assert result == "first-app"
    
    def test_extract_with_special_characters(self, client):
        """Test extraction of values with allowed special characters."""
        text = 'app.kubernetes.io/name: "app_with.special-chars"'
        result = client.extract_label_value(text, 'app.kubernetes.io/name')
        assert result == "app_with.special-chars"
