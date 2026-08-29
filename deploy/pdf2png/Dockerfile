FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir flask pdf2image pillow

COPY app.py /app/app.py
WORKDIR /app

EXPOSE 5000
CMD ["python", "-u", "app.py"]
