FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Data directory for the SQLite database
RUN mkdir -p /data
ENV DATABASE=/data/roastapp.db

EXPOSE 3000

CMD ["python", "app.py"]
