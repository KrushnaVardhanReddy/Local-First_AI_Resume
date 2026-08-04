.PHONY: install test build clean

install:
	uv sync

test:
	PYTHONPATH=. uv run pytest tests/ -v

build:
	bash scripts/build.sh

clean:
	rm -rf build/ dist/ *.spec
