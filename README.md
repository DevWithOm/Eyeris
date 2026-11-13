# Retina Screening

Modular diabetic-retinopathy screening research prototype.

- `frontend/`: React + Vite interface.
- `backend/`: FastAPI REST API and PostgreSQL persistence.
- `ai_models/`: classification, segmentation and explainability.
- `computer_vision/`: image quality and preprocessing.
- `integration/`: screening pipeline and decision orchestration.
- `matlab/`, `simulink/`: complementary application and simulation.
- `data/`: dataset directories and manifests.
- `storage/`: local runtime files (ignored by Git).
- `artifacts/`: model metadata and generated artifacts.

## Local setup
1. Use Python 3.11 and Node.js LTS.
2. Create a virtual environment and install `requirements-dev.txt`.
3. Copy `.env.example` to `.env` and set local credentials.
4. Start PostgreSQL: `docker compose up -d db`.
5. Start API: `uvicorn backend.app.main:app --reload`.
6. Start UI: `cd frontend && npm install && npm run dev`.

This is a research screening-support prototype, not a diagnostic medical device.
Do not commit patient-identifiable images, datasets, credentials or model weights.
