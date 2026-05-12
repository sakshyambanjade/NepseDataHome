FROM node:20-alpine AS web-build

WORKDIR /web

COPY web/package.json ./
COPY web/vite.config.js ./
COPY web/index.html ./
COPY web/src ./src

RUN npm install && npm run build


FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt pyproject.toml README.md ./
COPY api ./api
COPY src ./src
COPY --from=web-build /web/dist ./web/dist
COPY data/history ./data/history
COPY data/master ./data/master
COPY data/metadata ./data/metadata
COPY data/quality ./data/quality

RUN pip install --no-cache-dir -r requirements.txt fastapi uvicorn

EXPOSE 8080

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]

