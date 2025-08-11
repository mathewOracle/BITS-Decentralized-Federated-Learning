FROM python:3.10-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
 && rm -rf /var/lib/apt/lists/*
 
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
RUN rm -rf /usr/local/cuda* /usr/lib/x86_64-linux-gnu/libcuda*
COPY . /app/
EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]