FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN chmod +x /app/vector_cloud_entrypoint.py

ENV PORT=8088
ENV PYTHONUNBUFFERED=1

EXPOSE 8088

CMD ["python3", "vector_cloud_entrypoint.py"]
