FROM python:3.11.4-slim

RUN mkdir /app/

COPY . /app/

WORKDIR /app/

RUN pip install -r requirements.txt

CMD ["bash", "/app/start.sh"]
