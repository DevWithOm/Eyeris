FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt requirements-backend.txt requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend backend
COPY integration integration
COPY ai_models ai_models
COPY computer_vision computer_vision
COPY config config
EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
