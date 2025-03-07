docker build -t scriptsculpt:latest -f Dockerfile .

docker run -it --rm -v $(pwd)/app:/app scriptsculpt:latest
