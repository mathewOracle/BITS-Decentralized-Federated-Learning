FROM tensorflow/tensorflow:2.15.0
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
RUN rm -rf /usr/local/cuda* /usr/lib/x86_64-linux-gnu/libcuda*
COPY . /app/
EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]