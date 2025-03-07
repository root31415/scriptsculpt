FROM python:3.12-slim

RUN mkdir -p /app

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN rm requirements.txt

CMD ["/bin/bash"]