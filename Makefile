.PHONY: install test build clean setup-node

setup-node:
	npm install -g resumed jsonresume-theme-even

install: setup-node
	uv sync

test:
	PYTHONPATH=. uv run pytest tests/ -v

build:
	bash scripts/build.sh

clean:
	rm -rf build/ dist/ *.spec

USER ?= krushna
JOB ?= fake-senior-golang-engineer

render:
	cd users/$(USER)/output/$(JOB) && uv run rendercv render resume.yaml
