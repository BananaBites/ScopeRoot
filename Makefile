
install:
	python3 -m venv .venv
	. .venv/bin/activate && \
	pip install fastmcp pathspec

run:
	. .venv/bin/activate && \
	python mcp_fs.py


open:
	ngrok http 8000