.PHONY: install start test

install:
	poetry lock
	poetry install

start:
	python3 lgtv_remote.py

test:
	poetry run pytest tests/ -v
