# ScopeRoot

Share a directory with ChatGPT.


## Installation

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install fastmcp
```


## Run

Run in the directory you want to share.

```sh
. .venv/bin/activate
python mcp_fs.py
```


## Open

Open the access and provide an access url.

open:
	ngrok http 8000


## Or use the convenient wrapper script (put it in your PATH):

```sh
ScopeRoot              # Auto-detects available port
ScopeRoot 9000        # Specify a custom port
```


## Configure Access

Create a `.mcp-allow` file in the directory you're sharing
to specify which files are accessible.


### Pattern Syntax

Patterns use shell-style glob syntax (via Python's `fnmatch`):
- `README.md` - matches a specific file at root
- `src/**` - matches all files recursively under `src/`
- `*.py` - matches all `.py` files at root
- `docs/*.md` - matches markdown files directly in `docs/` (not in subdirs)
- `**/*.py` - matches all `.py` files anywhere
- `tests/**` - matches everything under `tests/`

See [fnmatch documentation](https://docs.python.org/3/library/fnmatch.html)
for full pattern details.


### Example `.mcp-allow`

```
# Files you want to share
README.md
docs/**
src/**
tests/**

# Specific config files
pyproject.toml
```


### Hard-Deny Rules

Even if whitelisted, these patterns are always denied for security:
- `.env`, `**/.env` - Environment files
- `*.pem`, `**/*.pem` - Private keys
- `*id_rsa*`, `**/*id_rsa*` - SSH keys
- `.git/**`, `**/.git/**` - Git metadata
- `.venv/**`, `**/.venv/**` - Virtual environments


### Dynamic Reload

The `.mcp-allow` file is automatically reloaded when it changes.
If there's a syntax error:

1. An error message is logged
2. The last valid configuration remains in effect
3. Fix the file and it will reload automatically
