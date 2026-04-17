FROM python:3.11-slim

WORKDIR /app/backend

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install --with-deps chromium 

COPY src/ ./src/

EXPOSE 8003

ENV PYTHONPATH="/app/backend/src"

CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8003"]
