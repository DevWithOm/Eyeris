# Deployment Guide

Use Python 3.11 and Node.js LTS. Install `requirements-dev.txt`, copy `.env.example` to `.env`, start PostgreSQL with `docker compose up -d db`, run `uvicorn backend.app.main:app --reload`, then run `npm install && npm run dev` inside `frontend/`. Replace all development credentials before deployment.
