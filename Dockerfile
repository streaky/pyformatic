
ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements-demo.txt .
RUN pip install --no-cache-dir -r requirements-demo.txt \
    && playwright install --with-deps chromium || true

COPY . .

CMD ["uvicorn", "demo.main:app", "--host", "0.0.0.0", "--port", "8000"]
