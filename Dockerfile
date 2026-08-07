FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pipeline/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline/pipeline_service.py ./pipeline_service.py
COPY CurrentTournament/fixture.csv ./CurrentTournament/fixture.csv

CMD exec gunicorn --bind :${PORT:-8080} --workers 1 --threads 4 --timeout 120 pipeline_service:app
