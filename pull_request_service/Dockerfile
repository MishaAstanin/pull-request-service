FROM python:3.10

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

RUN apt-get update && apt-get install -y postgresql-client

COPY . .

CMD ["sh", "-c", "\
  until pg_isready -h db -p 5432; do \
    echo 'Waiting for database...'; \
    sleep 2; \
  done; \
  python manage.py migrate && python manage.py runserver 0.0.0.0:8080"]
