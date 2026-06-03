"""
Reusable test validators and helpers for MCP tools.
"""

from pathlib import Path
from typing import Any
import ast


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_path(path_str: str) -> Path:
    """
    Validate and resolve a filesystem path.
    
    Args:
        path_str: Path string to validate
        
    Returns:
        Resolved Path object
        
    Raises:
        ValidationError: If path is invalid
    """
    if not isinstance(path_str, str):
        raise ValidationError("path must be string")
    
    path = Path(path_str).resolve()
    return path


def validate_git_repo(path_str: str) -> bool:
    """
    Validate that a path is a git repository.
    
    Args:
        path_str: Path to check
        
    Returns:
        True if valid git repo, raises ValidationError otherwise
    """
    path = validate_path(path_str)
    if not (path / ".git").exists():
        raise ValidationError(f"Not a git repository: {path_str}")
    return True


def validate_python_file(path_str: str) -> bool:
    """
    Validate that a file is a Python file with valid syntax.
    
    Args:
        path_str: Path to Python file
        
    Returns:
        True if valid Python file
        
    Raises:
        ValidationError: If not a Python file or invalid syntax
    """
    path = validate_path(path_str)
    
    if not path.suffix == ".py":
        raise ValidationError(f"Not a Python file: {path_str}")
    
    try:
        content = path.read_text(encoding="utf-8")
        ast.parse(content)
        return True
    except SyntaxError as e:
        raise ValidationError(f"Syntax error in {path_str}: {e.msg} at line {e.lineno}")
    except Exception as e:
        raise ValidationError(f"Error reading file {path_str}: {e}")


def validate_python_code(code: str) -> bool:
    """
    Validate Python code syntax without executing it.
    
    Args:
        code: Python code string
        
    Returns:
        True if valid syntax
        
    Raises:
        ValidationError: If syntax is invalid
    """
    if not isinstance(code, str):
        raise ValidationError("code must be string")
    
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        raise ValidationError(f"Syntax error: {e.msg} at line {e.lineno}")


def validate_regex_pattern(pattern: str) -> bool:
    """
    Validate regex pattern.
    
    Args:
        pattern: Regex pattern string
        
    Returns:
        True if valid regex
        
    Raises:
        ValidationError: If regex is invalid
    """
    import re
    
    if not isinstance(pattern, str):
        raise ValidationError("pattern must be string")
    
    try:
        re.compile(pattern)
        return True
    except re.error as e:
        raise ValidationError(f"Invalid regex: {e}")


def validate_git_message(message: str) -> bool:
    """
    Validate git commit message.
    
    Args:
        message: Commit message
        
    Returns:
        True if valid message
        
    Raises:
        ValidationError: If message is invalid
    """
    if not isinstance(message, str):
        raise ValidationError("message must be string")
    
    if not message.strip():
        raise ValidationError("message cannot be empty")
    
    return True


def validate_dict_payload(payload: dict[str, Any], required_keys: list[str]) -> bool:
    """
    Validate that a payload dict has required keys.
    
    Args:
        payload: Dictionary to validate
        required_keys: List of required key names
        
    Returns:
        True if all required keys present
        
    Raises:
        ValidationError: If any required keys missing
    """
    if not isinstance(payload, dict):
        raise ValidationError("payload must be dict")
    
    missing = [k for k in required_keys if k not in payload]
    if missing:
        raise ValidationError(f"Missing required keys: {missing}")
    
    return True


def assert_file_exists(path_str: str) -> Path:
    """
    Assert that a file exists.
    
    Args:
        path_str: Path to file
        
    Returns:
        Path object if file exists
        
    Raises:
        ValidationError: If file doesn't exist
    """
    path = validate_path(path_str)
    if not path.exists():
        raise ValidationError(f"File not found: {path_str}")
    return path


def assert_dir_exists(path_str: str) -> Path:
    """
    Assert that a directory exists.
    
    Args:
        path_str: Path to directory
        
    Returns:
        Path object if directory exists
        
    Raises:
        ValidationError: If directory doesn't exist
    """
    path = validate_path(path_str)
    if not path.is_dir():
        raise ValidationError(f"Directory not found: {path_str}")
    return path


def compare_outputs(expected: str, actual: str, ignore_whitespace: bool = False) -> bool:
    """
    Compare two outputs (useful for testing tool results).
    
    Args:
        expected: Expected output
        actual: Actual output
        ignore_whitespace: Whether to ignore whitespace differences
        
    Returns:
        True if outputs match
    """
    if ignore_whitespace:
        expected = " ".join(expected.split())
        actual = " ".join(actual.split())
    
    return expected == actual


def extract_lines_with_pattern(text: str, pattern: str) -> list[str]:
    """
    Extract lines matching a pattern (helper for validation).
    
    Args:
        text: Text to search
        pattern: Literal string pattern
        
    Returns:
        List of matching lines
    """
    return [line for line in text.split("\n") if pattern in line]
