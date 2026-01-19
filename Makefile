# Makefile for AI Desktop Assistant
# Cross-platform task runner

.PHONY: help install install-dev run test lint format clean

# Default target
help:
	@echo "AI Desktop Assistant - Available Commands"
	@echo ""
	@echo "  make install      Install production dependencies"
	@echo "  make install-dev  Install development dependencies"
	@echo "  make run          Run the assistant"
	@echo "  make test         Run tests"
	@echo "  make lint         Run linters"
	@echo "  make format       Format code"
	@echo "  make clean        Remove build artifacts"
	@echo "  make ollama       Start Ollama server"
	@echo ""

# Install production dependencies
install:
	pip install -r requirements.txt
	@echo ""
	@echo "✅ Dependencies installed!"
	@echo "📝 Copy .env.example to .env and configure"

# Install dev dependencies
install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov black isort flake8 mypy bandit
	@echo ""
	@echo "✅ Development dependencies installed!"

# Run the assistant
run:
	python main.py

# Run tests
test:
	pytest tools/test_core_smoke.py -v

# Run all linters
lint:
	@echo "Running flake8..."
	flake8 . --count --show-source --statistics --exclude=venv,.venv
	@echo ""
	@echo "Running mypy..."
	mypy . --ignore-missing-imports --exclude venv
	@echo ""
	@echo "Running bandit..."
	bandit -r . -x ./venv,./tests -ll

# Format code
format:
	@echo "Running isort..."
	isort . --skip venv --skip .venv
	@echo ""
	@echo "Running black..."
	black . --exclude "venv|\.venv"
	@echo ""
	@echo "✅ Code formatted!"

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf __pycache__/
	rm -rf */__pycache__/
	rm -rf */*/__pycache__/
	rm -f *.pyc
	rm -f .coverage
	rm -f coverage.xml
	@echo "✅ Cleaned!"

# Start Ollama server
ollama:
	ollama serve

# Pull recommended model
ollama-model:
	ollama pull mistral

# Build executable (Windows)
build:
	pip install pyinstaller
	pyinstaller --onefile --name ai-assistant main.py

# Create ZIP release
release:
	@echo "Creating release ZIP..."
	powershell Compress-Archive -Path * -DestinationPath ai-desktop-assistant-release.zip -Force
	@echo "✅ Release ZIP created!"
