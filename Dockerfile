FROM python:3.10-slim-bullseye
WORKDIR /usr/src/app
COPY src/ .
COPY requirements.txt .
RUN pip3 install -r requirements.txt
CMD ["python3", "-u", "start.py"]