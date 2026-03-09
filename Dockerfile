FROM python:3.12-slim AS backend
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM node:20-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
ARG VITE_API_KEY
ENV VITE_API_KEY=$VITE_API_KEY
RUN npm run build

FROM python:3.12-slim
WORKDIR /code
COPY --from=backend /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend /usr/local/bin /usr/local/bin
COPY app/ app/
COPY --from=frontend /build/dist frontend/dist
RUN mkdir -p /data
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
