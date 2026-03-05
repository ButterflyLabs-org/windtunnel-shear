.PHONY: install lint test format typecheck build publish clean coverage

install:
	pip install -e ".[dev]"
	pre-commit install

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

typecheck:
	mypy src/

test:
	pytest tests/ -v --tb=short

coverage:
	pytest tests/ --cov=windtunnel_shear --cov-report=term-missing --cov-fail-under=90

build:
	python -m build

publish:
	twine upload dist/*

clean:
	rm -rf dist/ build/ *.egg-info .pytest_cache .mypy_cache .ruff_cache
