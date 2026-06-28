FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install -U pip
RUN pip install -e .

CMD ["python", "main.py"]
