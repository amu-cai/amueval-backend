FROM python:3.12.3
WORKDIR /code
ADD requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --progress-bar off --upgrade -r /code/requirements.txt
COPY . /code
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
