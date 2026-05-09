# Anime Visual Concept Generator (Default)

Python + FastAPI + OpenAI + simple frontend + Docker.

## Features
- Upload optional reference image
- Input theme and style direction
- Agent-like pipeline:
  1. Worldbuilding summary
  2. Visual elements composition
  3. Layout generation
  4. Detail optimization
- Outputs both JSON and Markdown

## Quick Start

```bash
cp .env.example .env
# set OPENAI_API_KEY in .env

docker compose up --build
# open http://localhost:8000
```

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
