[Go back to README.md](https://github.com/onesch/redwave-overlays/blob/master/README.md)

# Contributing Guide

Thanks for your interest in contributing to **RedWave Overlays**!  
This document explains how to set up the project for development.

## Installation

```bash
git clone https://github.com/onesch/redwave-overlays.git
cd redwave-overlays

# Python dependencies
pip install -r requirements.txt

# Node dependencies
cd frontend
npm install
```

## Usage

```bash
# Start both FastAPI backend and Electron app
npm run start:dev
# Production mode (required backend_run/main.exe)
npm run start:prod
```

## Tests
```bash
# Run the full test suite
python -m pytest -vv

npm run test:frontend
```

```bash
# Generate a coverage report
coverage run -m pytest
coverage report -m

npm run coverage:frontend
```

## Project Structure

Want to understand how the project is organized?
Check out [Project structure](https://github.com/onesch/redwave-overlays/blob/master/.github/docs/STRUCTURE.md).

## Build & Packaging

For building the production version of RedWave overlays, see [how to build app](https://github.com/onesch/redwave-overlays/blob/master/.github/docs/PROJECTBUILD.md).


## Contribution Workflow

1. Fork the repository.
2. Create a new branch from develop:

```bash
git checkout develop
git pull
git checkout -b feature/YOUR_TEXT_HERE
```

3. Make your changes.
4. Add tests for new functionality.
5. Run tests to ensure everything works.
6. Open a Pull Request into develop branch.
