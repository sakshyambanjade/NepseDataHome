FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt pyproject.toml README.md ./
COPY api ./api
COPY src ./src
COPY data/history ./data/history
COPY data/master ./data/master
COPY data/metadata ./data/metadata
COPY data/quality ./data/quality

RUN pip install --no-cache-dir -r requirements.txt fastapi uvicorn

EXPOSE 8080

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]

