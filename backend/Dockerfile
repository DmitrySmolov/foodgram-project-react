FROM python:3.9-slim

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        gcc \
        libc-dev \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip \
    && pip install -r /app/requirements.txt --no-cache-dir

COPY . /app

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0.0.0.0:8000"]
