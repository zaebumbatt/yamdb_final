FROM python:3.8.5

WORKDIR /code
COPY . .
RUN mkdir /static
RUN pip install -r requirements.txt