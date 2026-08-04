.PHONY: install test build clean

install:
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
