FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY modules ./modules
COPY run_pipeline.py ./run_pipeline.py
COPY data ./data
COPY configs ./configs

RUN mkdir -p logs reports

EXPOSE 8000

CMD ["sh", "-c", "uvicorn modules.api.app:app --host 0.0.0.0 --port ${PORT}"]