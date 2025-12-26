from __future__ import annotations

import argparse
import fnmatch
import logging
import os
from pathlib import Path
from typing import List, Optional

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

ROOT = Path(os.getcwd()).resolve()
ALLOW_FILE = ROOT / ".mcp-allow"

# Hard-deny a few common "oops" secrets even if someone whitelists too broadly
# Uses fnmatch patterns (shell-style wildcards)
DENY_PATTERNS = [
    ".env", "**/.env", "*.pem", "**/*.pem", "*id_rsa*", "**/*id_rsa*",
    ".git", ".git/**", "**/.git/**", ".venv", ".venv/**", "**/.venv/**",
]

# Track the last valid allow patterns and file mtime
_allow_patterns: List[str] = []
_allow_file_mtime: float = 0
_last_error: Optional[str] = None


def _load_allow_patterns() -> List[str]:
    """Load and parse .mcp-allow file, return list of patterns.
    
    Supports shell-style glob patterns:
    - README.md      matches README.md at root
    - src/**         matches all files under src/
    - *.py           matches all .py files at root
    
    Reference: https://docs.python.org/3/library/fnmatch.html
    """
    global _allow_patterns, _allow_file_mtime, _last_error
    
    try:
        if not ALLOW_FILE.exists():
            # Default-deny: nothing is accessible unless user creates .mcp-allow
            return []
        
        # Check if file changed
        current_mtime = ALLOW_FILE.stat().st_mtime
        if current_mtime == _allow_file_mtime and _allow_patterns:
            return _allow_patterns  # Cache hit, no reload needed
        
        # Read and parse file
        lines = [ln.strip() for ln in ALLOW_FILE.read_text(encoding="utf-8").splitlines()]
        lines = [ln for ln in lines if ln and not ln.startswith("#")]
        
        # Validate patterns (basic check)
        for pattern in lines:
            if not pattern or pattern.startswith("#"):
                continue
            # fnmatch patterns should be simple; no validation needed for basic syntax
        
        # Success: update cache
        # Always include .mcp-allow for transparency about access rules
        lines.append(".mcp-allow")
        _allow_patterns = lines
        _allow_file_mtime = current_mtime
        _last_error = None
        return lines
        
    except Exception as e:
        error_msg = f"Error reading .mcp-allow: {e}"
        logger.error(error_msg)
        _last_error = error_msg
        # Return last valid patterns, or empty list if none exist
        return _allow_patterns


def _matches_patterns(path: str, patterns: List[str]) -> bool:
    """Check if path matches any of the given fnmatch patterns."""
    for pattern in patterns:
        # Handle recursive patterns (glob-style)
        if "**" in pattern:
            # Convert ** patterns to match any depth
            # e.g., "src/**" should match "src/file.py", "src/subdir/file.py", etc.
            pattern_prefix = pattern.replace("**", "").rstrip("/")
            if not pattern_prefix or path.startswith(pattern_prefix + "/"):
                # Check if the remaining part matches
                if pattern_prefix:
                    remaining = path[len(pattern_prefix)+1:]
                    if fnmatch.fnmatch(remaining, "*"):
                        return True
                else:
                    return True
        else:
            # Simple fnmatch for non-recursive patterns
            if fnmatch.fnmatch(path, pattern):
                return True
    
    return False

def _safe_rel(path: str) -> Path:
    """Validate and resolve a relative path, checking allow/deny rules."""
    # Interpret requested paths relative to ROOT; forbid absolute paths
    p = Path(path)
    if p.is_absolute():
        raise ValueError("Absolute paths are not allowed.")
    resolved = (ROOT / p).resolve()

    # Prevent escaping ROOT (covers .. traversal and symlinks that point outward)
    try:
        resolved.relative_to(ROOT)
    except ValueError:
        raise ValueError("Path escapes the workspace root.")

    rel = resolved.relative_to(ROOT)
    rel_posix = rel.as_posix()

    # Check hard-deny patterns first
    if _matches_patterns(rel_posix, DENY_PATTERNS):
        raise ValueError("Path is denied by built-in deny rules.")

    # For directories, allow them to be traversed (contents will be checked)
    # For files, they must be whitelisted in .mcp-allow
    if resolved.is_file():
        allow_patterns = _load_allow_patterns()
        if _last_error:
            raise ValueError(_last_error)
        if not _matches_patterns(rel_posix, allow_patterns):
            raise ValueError("Path is not whitelisted in .mcp-allow.")

    return resolved

mcp = FastMCP("local-workspace")

@mcp.tool
def list_files(prefix: str = ".") -> List[str]:
    """List whitelisted files under prefix (relative to workspace root)."""
    base = _safe_rel(prefix)
    out: List[str] = []
    allow_patterns = _load_allow_patterns()
    
    for p in base.rglob("*"):
        if p.is_file():
            rel = p.relative_to(ROOT).as_posix()
            # Apply allow/deny at file-level
            if not _matches_patterns(rel, DENY_PATTERNS) and _matches_patterns(rel, allow_patterns):
                out.append(rel)
    return sorted(out)

@mcp.tool
def read_text(path: str, max_bytes: int = 200_000) -> str:
    """Read a whitelisted text file (UTF-8)."""
    # Special case: .mcp-allow is always readable (for transparency about access rules)
    # but never writable (for security - to prevent privilege escalation)
    p = Path(path).resolve()
    if p.name == ".mcp-allow":
        p = ROOT / ".mcp-allow"
    else:
        p = _safe_rel(path)
    data = p.read_bytes()
    if len(data) > max_bytes:
        raise ValueError(f"File too large ({len(data)} bytes). Increase max_bytes if needed.")
    return data.decode("utf-8", errors="replace")

@mcp.tool
def write_text(path: str, content: str, create: bool = True) -> str:
    """Write a whitelisted text file (UTF-8)."""
    p = _safe_rel(path)
    # Prevent writing to .mcp-allow (read-only for security)
    if p.name == ".mcp-allow" or p.as_posix() == ".mcp-allow":
        raise ValueError(".mcp-allow is read-only for security reasons. Manual filesystem edits required.")
    if not p.exists() and not create:
        raise ValueError("File does not exist and create=False.")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return "ok"

def get_help_text() -> str:
    """Return MCP-specific help text for use in ScopeRoot."""
    return """
.MCP-ALLOW CONFIGURATION:
  Create a .mcp-allow file to control what ChatGPT can access.

  Example .mcp-allow:
    # allow these:
    README.md
    Makefile
    docs/**
    src/**
    tests/**
    # '.mcp-allow' itself can always be read but never be written by Chat-GPT

PATTERN SYNTAX:
  README.md         Match a specific file at root
  docs/**           Match all files recursively under docs/
  *.py              Match all .py files at root
  **                Match all files and dirs, ok for scaffolding in empty directory

SECURITY:
  • .mcp-allow is read-only (ChatGPT cannot modify it)
  • Hard-denied patterns: .env, *.pem, *id_rsa*, .git/**, .venv/**
  • ChatGPT can only access files matching your .mcp-allow patterns
  • Cannot escape the workspace root (.. traversal and symlink escapes blocked)

INSTRUCTIONS FOR CHATGPT:
  "I've set up ScopeRoot to share my project. You can access files defined in
  .mcp-allow using shell-style glob patterns. Read .mcp-allow to see what you
  can access. You can read and modify whitelisted files, but you cannot edit
  .mcp-allow itself (manual filesystem edits required). If you need access to
  additional locations, I'll update .mcp-allow."

EDIT ACCESS:
  If ChatGPT needs access to a new directory or file:
  1. Update your .mcp-allow file on the filesystem
  2. The changes are automatically detected and loaded
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run FastMCP file server for sharing project files with ChatGPT",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=get_help_text()
    )
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    args = parser.parse_args()
    
    # Streamable HTTP transport on localhost, mounted at /mcp
    mcp.run(transport="http", host="127.0.0.1", port=args.port, path="/mcp")
