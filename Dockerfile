FROM python:3.10-slim-buster
WORKDIR /app

ARG BUILD_DATE
ENV IMAGE_BUILD_DATE=$BUILD_DATE

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]