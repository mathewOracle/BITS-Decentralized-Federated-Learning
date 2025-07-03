FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install fastapi[all] tensorflow numpy
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
