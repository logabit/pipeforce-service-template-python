FROM python:3.10-slim-bullseye
COPY requirements.txt .
RUN pip3 install -r requirements.txt
WORKDIR /usr/src/app
COPY . .
CMD ["./run-service.sh"]