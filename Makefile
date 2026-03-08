.PHONY: install install-dev test lint format type-check clean

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v --cov=src/nomothetic --cov-report=html

lint:
	ruff check src/ tests/
	black --check src/ tests/

format:
	black src/ tests/
	ruff check --fix src/ tests/

type-check:
	mypy src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/ .mypy_cache/

help:
	@echo "Available targets:"
	@echo "  install      - Install the package"
	@echo "  install-dev  - Install package and development dependencies"
	@echo "  test         - Run tests with coverage"
	@echo "  lint         - Check code style"
	@echo "  format       - Format code with black and ruff"
	@echo "  type-check   - Run type checking with mypy"
	@echo "  clean        - Remove generated files and caches"
