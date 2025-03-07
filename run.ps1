docker build -t scriptsculpt:latest -f Dockerfile .

docker run -it --rm -v ${PWD}/app:/app -p 7860:7860 --name scriptsculpt scriptsculpt:latest