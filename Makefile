# Makefile
# Convenience commands for Docker development

.PHONY: build test run clean help

# Default target
help:
	@echo "rgb-weaver Docker Commands"
	@echo ""
	@echo "Commands:"
	@echo "  make build    Build Docker image"
	@echo "  make test     Test Docker image" 
	@echo "  make run      Run interactive shell in container"
	@echo "  make clean    Clean Docker images and containers"
	@echo "  make push     Push to Docker registry (requires login)"
	@echo ""
	@echo "Quick usage:"
	@echo "  docker run -v \$$(pwd):/data rgb-weaver:latest dem.tif output.pmtiles --min-z 8 --max-z 14"

build:
	@echo "Building rgb-weaver Docker image..."
	./scripts/docker-build.sh

test:
	@echo "Testing rgb-weaver Docker image..."
	./scripts/docker-test.sh

run:
	@echo "Running interactive rgb-weaver container..."
	docker run -it --rm -v $(pwd):/data rgb-weaver:latest /bin/bash

clean:
	@echo "Cleaning Docker images and containers..."
	docker container prune -f
	docker image prune -f
	@echo "Cleanup complete"

push:
	@echo "Pushing to Docker registry..."
	docker tag rgb-weaver:latest your-registry/rgb-weaver:latest
	docker tag rgb-weaver:latest your-registry/rgb-weaver:2.0.0
	docker push your-registry/rgb-weaver:latest
	docker push your-registry/rgb-weaver:2.0.0
	@echo "Images pushed successfully"

# Development commands
dev-build:
	docker build --target development -t rgb-weaver:dev .

dev-run:
	docker run -it --rm -v $(pwd):/app rgb-weaver:dev /bin/bash