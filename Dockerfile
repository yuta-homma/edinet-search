FROM python:3.9.15-slim

COPY requirements.txt .
RUN pip3 install -r requirements.txt

# COPY ./app /app

CMD [ "python", "/app/main.py" ]
