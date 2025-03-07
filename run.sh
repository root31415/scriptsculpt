docker build -t scriptsculpt:latest -f Dockerfile .

docker run -it --rm -v $(pwd)/app:/app -p 7860:7860 scriptsculpt:latest
