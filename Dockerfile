FROM python:3.8.5

WORKDIR /code
COPY . .
RUN pip install -r requirements.txt
RUN mkdir static
RUN python manage.py collectstatic -y
CMD gunicorn api_yamdb.wsgi:application --bind 0.0.0.0:8000