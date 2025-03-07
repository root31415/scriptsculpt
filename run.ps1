docker build -t scriptsculpt:latest -f Dockerfile .
docker run -it --rm -v ${PWD}/app:/app scriptsculpt:latest