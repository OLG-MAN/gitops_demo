FROM python:3.11-slim-buster

WORKDIR /app
COPY . /app/

RUN pip install -r requirements.txt

ENV FLASK_APP=app.py
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]

# CMD flask run -h 0.0.0.0 -p 5000