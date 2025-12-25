#!/usr/bin/env python3
"""
Test script to verify mcp_fs.py logic without running the full server.
Tests shell-style glob matching behavior using fnmatch.
"""

import os
import sys
import tempfile
from pathlib import Path

# Create a temporary test directory structure
def setup_test_env():
    """Create a temporary directory with test files and subdirectories."""
    tmpdir = tempfile.mkdtemp(prefix="scoperoot_test_")
    tmppath = Path(tmpdir)
    
    # Create test files
    (tmppath / "README.md").write_text("# Test README")
    (tmppath / "secret.env").write_text("SECRET_KEY=should_be_denied")
    (tmppath / "main.py").write_text("print('hello')")
    
    # Create directories
    (tmppath / "docs").mkdir()
    (tmppath / "docs" / "guide.md").write_text("# Guide")
    (tmppath / "docs" / "api.md").write_text("# API")
    
    (tmppath / "src").mkdir()
    (tmppath / "src" / "main.py").write_text("def main(): pass")
    (tmppath / "src" / "utils.py").write_text("def util(): pass")
    (tmppath / "src" / "config").mkdir(parents=True)
    (tmppath / "src" / "config" / "settings.py").write_text("DEBUG=True")
    
    (tmppath / "tests").mkdir()
    (tmppath / "tests" / "test_main.py").write_text("def test(): pass")
    
    (tmppath / "private").mkdir()
    (tmppath / "private" / "config.txt").write_text("secret data")
    
    # Create a .venv-like directory to simulate the real scenario
    (tmppath / ".venv" / "lib" / "python3.12" / "site-packages").mkdir(parents=True)
    (tmppath / ".venv" / "lib" / "python3.12" / "site-packages" / "README.md").write_text("venv readme")
    
    # Create .mcp-allow file with shell-style patterns
    # These patterns should:
    # - Match specific files: README.md (only at root)
    # - Match all files in dirs: docs/**, src/**, tests/**
    # - NOT match README.md in .venv/
    allow_content = """# allow these:
README.md
docs/**
src/**
tests/**
"""
    (tmppath / ".mcp-allow").write_text(allow_content)
    
    return tmppath


def test_shell_glob_behavior():
    """Test that patterns behave like shell globs, not recursive anywhere."""
    testdir = setup_test_env()
    print(f"📁 Test directory: {testdir}\n")
    
    # Change to test directory (this is what happens when user runs ScopeRoot)
    original_cwd = os.getcwd()
    os.chdir(testdir)
    
    try:
        from mcp_fs import _safe_rel
        
        test_cases = [
            # Files that should be allowed
            ("README.md", True, "README.md at root should be allowed"),
            ("docs/guide.md", True, "docs/guide.md should be allowed"),
            ("docs/api.md", True, "docs/api.md should be allowed"),
            ("src/main.py", True, "src/main.py should be allowed"),
            ("src/utils.py", True, "src/utils.py should be allowed"),
            ("src/config/settings.py", True, "src/config/settings.py should be allowed (under src/**)"),
            ("tests/test_main.py", True, "tests/test_main.py should be allowed"),
            
            # Files that should be denied
            ("secret.env", False, "secret.env should be denied (hard deny rule)"),
            ("main.py", False, "main.py at root should be denied (not in allow list)"),
            ("private/config.txt", False, "private/config.txt should be denied (not in allow list)"),
            (".venv/lib/python3.12/site-packages/README.md", False, ".venv README should be denied (not matching README.md pattern)"),
        ]
        
        print("Testing file access logic with shell-style glob patterns:\n")
        passed = 0
        failed = 0
        for path, should_work, description in test_cases:
            try:
                result = _safe_rel(path)
                if should_work:
                    print(f"✅ PASS: {description}")
                    passed += 1
                else:
                    print(f"❌ FAIL: {description}")
                    print(f"       Expected to be denied but was allowed")
                    failed += 1
            except ValueError as e:
                if not should_work:
                    print(f"✅ PASS: {description}")
                    passed += 1
                else:
                    print(f"❌ FAIL: {description}")
                    print(f"       Error: {e}")
                    failed += 1
        
        # Test list_files
        print(f"\n\nTesting list_files():\n")
        from mcp_fs import list_files as list_files_func
        
        files = list_files_func.fn(".")
        print(f"Files found in current directory:")
        for f in sorted(files):
            print(f"  ✓ {f}")
        
        # Verify venv files are NOT included
        venv_files = [f for f in files if ".venv" in f]
        if venv_files:
            print(f"\n❌ FAIL: Found .venv files (should be filtered out):")
            for f in venv_files:
                print(f"  ✗ {f}")
            failed += 1
        else:
            print(f"\n✅ PASS: No .venv files leaked into results")
            passed += 1
        
        # Verify expected files are present
        expected = {"README.md", "docs/guide.md", "docs/api.md", "src/main.py", 
                   "src/utils.py", "src/config/settings.py", "tests/test_main.py"}
        found = set(files)
        if expected.issubset(found):
            print(f"✅ PASS: All expected files found")
            passed += 1
        else:
            missing = expected - found
            print(f"❌ FAIL: Missing expected files: {missing}")
            failed += 1
        
        print(f"\n\n{'='*60}")
        print(f"Results: {passed} passed, {failed} failed")
        print(f"{'='*60}")
        
        return failed == 0
        
    finally:
        os.chdir(original_cwd)
        # Cleanup
        import shutil
        shutil.rmtree(testdir)
        print(f"\n🧹 Cleaned up test directory")


if __name__ == "__main__":
    success = test_shell_glob_behavior()
    sys.exit(0 if success else 1)

