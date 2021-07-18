NAME   := nucleo
TAG    := $$(git rev-parse HEAD)
IMG    := ${NAME}:${TAG}
LATEST := ${NAME}:latest

build:
	docker build -t ${IMG} .
	docker tag ${IMG} ${LATEST}

build-nc:
	docker build --no-cache -t ${IMG} .
	docker tag ${IMG} ${LATEST}

run:
	docker-compose up -d

up: build run
