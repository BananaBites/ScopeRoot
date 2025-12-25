
install:
	python3 -m venv .venv
	. .venv/bin/activate && \
	pip install fastmcp

run:
	. .venv/bin/activate && \
	python mcp_fs.py

test:
	. .venv/bin/activate && \
	python test_mcp_fs.py

open:
	ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
  		-R 80:localhost:8000 localhost.run
