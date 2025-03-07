FROM python:3.12-slim

RUN mkdir -p /app

WORKDIR /app

RUN apt-get update && \
    apt-get install -y tk && \
    rm -rf /var/lib/apt/lists/*


COPY requirements.txt .

RUN pip install -r requirements.txt

RUN rm requirements.txt

CMD ["/bin/bash"]
# CMD ["python", "main.py"]