# ScopeRoot

Share a directory with ChatGPT.


## Installation

Clone the repository and create a symlink to the
`ScopeRoot` script in a directory in your `$PATH`:

```sh
git clone https://github.com/user/ScopeRoot.git ~/repos/ScopeRoot
ln -s ~/repos/ScopeRoot/ScopeRoot ~/.local/bin/ScopeRoot
export PATH="$HOME/.local/bin:$PATH"  # Add to ~/.bashrc or ~/.zshrc for persistence
```

Adjust the paths as needed for your setup. Common choices for symlink location:
- `~/.local/bin/` (recommended, Python convention)
- `~/bin/`
- `/usr/local/bin/` (system-wide, requires sudo)


## Usage

Run the wrapper script in your project directory:

```sh
ScopeRoot              # Auto-detects available port
ScopeRoot 9000        # Specify a custom port
```

This starts the MCP server
and automatically creates an SSH tunnel with a public URL.


## Connect to ChatGPT

1. Run `ScopeRoot` in your project directory
2. Copy the public URL from the output (e.g., `https://xxx.localhost.run`)
3. In ChatGPT, add a new MCP server
        (Developer mode must be enabled):
   - Name: `ScopeRoot`
   - MCP Server URL: `https://<tunnel-url>/mcp`
   - Authentication: `No Auth`
4. Use it in a chat like so: `/ScopeRoot`
    - The server will now have access to your whitelisted files


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


## Test locally using this Repo

see [./Makefile](./Makefile)


## License

This project is licensed under the
[MIT License](https://opensource.org/licenses/MIT).
