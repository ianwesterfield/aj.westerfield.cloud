#!/usr/bin/env python3
"""
Docker & Containerization Training Data Generator
Target: ~300 examples for Docker, docker-compose, container orchestration
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SYSTEM_PROMPT = """You are AJ, an expert AI assistant for Docker and containerization.
You help with container management, Dockerfile creation, docker-compose, and container orchestration."""

# =============================================================================
# TOOL SELECTION TASKS
# =============================================================================

BASIC_DOCKER_TASKS = [
    {
        "instruction": "List all running containers",
        "command": "docker ps",
        "explanation": "Shows running containers; use -a to include stopped containers"
    },
    {
        "instruction": "List all Docker images",
        "command": "docker images",
        "explanation": "Shows all local images with tags and sizes"
    },
    {
        "instruction": "Pull an image from Docker Hub",
        "command": "docker pull nginx:latest",
        "explanation": "Downloads nginx image with latest tag"
    },
    {
        "instruction": "Run a container from an image",
        "command": "docker run -d -p 8080:80 --name web nginx",
        "explanation": "Runs nginx in detached mode, maps port 8080 to container's 80"
    },
    {
        "instruction": "Stop a running container",
        "command": "docker stop web",
        "explanation": "Gracefully stops container named 'web'"
    },
    {
        "instruction": "Remove a container",
        "command": "docker rm web",
        "explanation": "Removes stopped container; use -f to force remove running container"
    },
    {
        "instruction": "View container logs",
        "command": "docker logs -f web",
        "explanation": "Follows logs from container 'web'; -f for follow mode"
    },
    {
        "instruction": "Execute command in running container",
        "command": "docker exec -it web bash",
        "explanation": "Opens interactive bash shell in running container"
    },
    {
        "instruction": "Build an image from Dockerfile",
        "command": "docker build -t myapp:1.0 .",
        "explanation": "Builds image tagged 'myapp:1.0' from Dockerfile in current directory"
    },
    {
        "instruction": "Show container resource usage",
        "command": "docker stats",
        "explanation": "Live stream of container CPU, memory, network, I/O usage"
    },
    {
        "instruction": "Inspect container details",
        "command": "docker inspect web",
        "explanation": "Returns detailed JSON info about container configuration"
    },
    {
        "instruction": "Copy files from container",
        "command": "docker cp web:/app/logs ./logs",
        "explanation": "Copies /app/logs from container to local ./logs"
    },
    # NEW: Additional basic Docker tasks
    {
        "instruction": "List all containers including stopped ones",
        "command": "docker ps -a",
        "explanation": "Shows all containers regardless of state"
    },
    {
        "instruction": "Remove all stopped containers",
        "command": "docker container prune -f",
        "explanation": "Removes all containers that are not running"
    },
    {
        "instruction": "Remove unused images",
        "command": "docker image prune -a -f",
        "explanation": "Removes all images not used by any container"
    },
    {
        "instruction": "Restart a container",
        "command": "docker restart web",
        "explanation": "Stops and starts the container named 'web'"
    },
    {
        "instruction": "Show the last 50 lines of container logs",
        "command": "docker logs --tail 50 web",
        "explanation": "Shows the last 50 log lines from container"
    },
    {
        "instruction": "View logs with timestamps",
        "command": "docker logs -t web",
        "explanation": "Displays logs with timestamp prefix"
    },
    {
        "instruction": "Run container in interactive mode",
        "command": "docker run -it ubuntu bash",
        "explanation": "Runs Ubuntu container with interactive terminal"
    },
    {
        "instruction": "Run container with name",
        "command": "docker run -d --name mycontainer nginx",
        "explanation": "Runs nginx with custom name 'mycontainer'"
    },
    {
        "instruction": "Remove an image",
        "command": "docker rmi nginx:latest",
        "explanation": "Removes the nginx:latest image from local storage"
    },
    {
        "instruction": "Tag an image",
        "command": "docker tag myapp:latest myregistry.com/myapp:v1.0",
        "explanation": "Creates a new tag for an existing image"
    },
    {
        "instruction": "List Docker volumes",
        "command": "docker volume ls",
        "explanation": "Shows all Docker volumes"
    },
    {
        "instruction": "Create a Docker volume",
        "command": "docker volume create mydata",
        "explanation": "Creates a named volume called 'mydata'"
    },
    {
        "instruction": "Remove a Docker volume",
        "command": "docker volume rm mydata",
        "explanation": "Removes the named volume 'mydata'"
    },
    {
        "instruction": "List Docker networks",
        "command": "docker network ls",
        "explanation": "Shows all Docker networks"
    },
    {
        "instruction": "Show disk usage by Docker",
        "command": "docker system df",
        "explanation": "Shows disk space used by images, containers, volumes"
    },
    {
        "instruction": "Kill a running container",
        "command": "docker kill web",
        "explanation": "Forcefully stops container immediately (SIGKILL)"
    },
    {
        "instruction": "Pause a running container",
        "command": "docker pause web",
        "explanation": "Suspends all processes in container"
    },
    {
        "instruction": "Unpause a paused container",
        "command": "docker unpause web",
        "explanation": "Resumes processes in a paused container"
    },
    {
        "instruction": "Show processes running in container",
        "command": "docker top web",
        "explanation": "Lists processes running inside the container"
    },
    {
        "instruction": "Show port mappings for container",
        "command": "docker port web",
        "explanation": "Lists port mappings for the container"
    },
    {
        "instruction": "Show image history",
        "command": "docker history myapp:latest",
        "explanation": "Shows the layers/commands that built the image"
    },
    {
        "instruction": "Login to Docker registry",
        "command": "docker login myregistry.com",
        "explanation": "Authenticates to a container registry"
    },
    {
        "instruction": "Logout from Docker registry",
        "command": "docker logout myregistry.com",
        "explanation": "Removes stored credentials for registry"
    },
    {
        "instruction": "Search Docker Hub for images",
        "command": "docker search python",
        "explanation": "Searches Docker Hub for Python images"
    },
    {
        "instruction": "Export container filesystem to tar",
        "command": "docker export web > container.tar",
        "explanation": "Exports container filesystem (not image layers)"
    },
    {
        "instruction": "Import container from tar",
        "command": "docker import container.tar myimage:imported",
        "explanation": "Creates image from exported container filesystem"
    },
    {
        "instruction": "Get container IP address",
        "command": "docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' web",
        "explanation": "Extracts container IP address from inspect output"
    },
    {
        "instruction": "Show container changes from base image",
        "command": "docker diff web",
        "explanation": "Shows filesystem changes in running container"
    },
    {
        "instruction": "Wait for container to stop",
        "command": "docker wait web",
        "explanation": "Blocks until container stops, returns exit code"
    },
    {
        "instruction": "Rename a container",
        "command": "docker rename oldname newname",
        "explanation": "Changes the name of an existing container"
    },
    {
        "instruction": "Update container resource limits",
        "command": "docker update --memory=1g web",
        "explanation": "Updates memory limit of running container"
    },
]

ADVANCED_DOCKER_TASKS = [
    {
        "instruction": "Run container with volume mount",
        "command": "docker run -d -v $(pwd)/data:/app/data -v config:/app/config myapp",
        "explanation": "Bind mount ./data and named volume 'config' into container"
    },
    {
        "instruction": "Run container with environment variables",
        "command": "docker run -d --env-file .env -e DEBUG=true myapp",
        "explanation": "Loads vars from .env file and sets DEBUG=true"
    },
    {
        "instruction": "Create a Docker network",
        "command": "docker network create --driver bridge mynetwork",
        "explanation": "Creates bridge network for container communication"
    },
    {
        "instruction": "Connect container to network",
        "command": "docker network connect mynetwork web",
        "explanation": "Connects running container to network"
    },
    {
        "instruction": "Run container with resource limits",
        "command": "docker run -d --memory=512m --cpus=0.5 myapp",
        "explanation": "Limits container to 512MB RAM and half a CPU core"
    },
    {
        "instruction": "Create and run multi-container setup",
        "command": "docker compose up -d",
        "explanation": "Starts all services defined in docker-compose.yml in detached mode"
    },
    {
        "instruction": "View compose service logs",
        "command": "docker compose logs -f api db",
        "explanation": "Follows logs for api and db services"
    },
    {
        "instruction": "Scale a compose service",
        "command": "docker compose up -d --scale api=3",
        "explanation": "Scales api service to 3 replicas"
    },
    {
        "instruction": "Rebuild compose services",
        "command": "docker compose up -d --build",
        "explanation": "Rebuilds images before starting containers"
    },
    {
        "instruction": "Run one-off command with compose",
        "command": "docker compose run --rm api python manage.py migrate",
        "explanation": "Runs migration in api service, removes container after"
    },
    {
        "instruction": "Export container as image",
        "command": "docker commit web myapp:snapshot",
        "explanation": "Creates image from running container's current state"
    },
    {
        "instruction": "Save image to file",
        "command": "docker save -o myapp.tar myapp:latest",
        "explanation": "Exports image to tar file for transfer"
    },
    {
        "instruction": "Load image from file",
        "command": "docker load -i myapp.tar",
        "explanation": "Imports image from tar file"
    },
    {
        "instruction": "Push image to registry",
        "command": "docker push myregistry.com/myapp:1.0",
        "explanation": "Pushes tagged image to container registry"
    },
    {
        "instruction": "Prune unused Docker resources",
        "command": "docker system prune -a --volumes",
        "explanation": "Removes all unused images, containers, networks, and volumes"
    },
    # Additional advanced Docker tasks
    {
        "instruction": "Run container with health check",
        "command": "docker run -d --health-cmd='curl -f http://localhost/ || exit 1' --health-interval=30s nginx",
        "explanation": "Runs container with periodic health check"
    },
    {
        "instruction": "Disconnect container from network",
        "command": "docker network disconnect mynetwork web",
        "explanation": "Removes container from network"
    },
    {
        "instruction": "Create overlay network for swarm",
        "command": "docker network create --driver overlay --attachable myoverlay",
        "explanation": "Creates overlay network for multi-host communication"
    },
    {
        "instruction": "Run container with GPU access",
        "command": "docker run -d --gpus all nvidia/cuda:12.0-base nvidia-smi",
        "explanation": "Runs container with access to all GPUs"
    },
    {
        "instruction": "Run container with specific user",
        "command": "docker run -d --user 1000:1000 myapp",
        "explanation": "Runs container as specific UID:GID"
    },
    {
        "instruction": "Run container with read-only filesystem",
        "command": "docker run -d --read-only -v /tmp:/tmp myapp",
        "explanation": "Container filesystem is read-only except mounted volumes"
    },
    {
        "instruction": "Run container with restart policy",
        "command": "docker run -d --restart=unless-stopped myapp",
        "explanation": "Automatically restarts container unless explicitly stopped"
    },
    {
        "instruction": "Run privileged container",
        "command": "docker run -d --privileged myapp",
        "explanation": "Container has full access to host devices (use carefully)"
    },
    {
        "instruction": "Run container with custom DNS",
        "command": "docker run -d --dns=8.8.8.8 --dns-search=example.com myapp",
        "explanation": "Sets custom DNS server and search domain"
    },
    {
        "instruction": "Run container with capabilities",
        "command": "docker run -d --cap-add=NET_ADMIN --cap-drop=CHOWN myapp",
        "explanation": "Adds NET_ADMIN and removes CHOWN capability"
    },
    {
        "instruction": "Run container with tmpfs mount",
        "command": "docker run -d --tmpfs /tmp:rw,noexec,nosuid,size=100m myapp",
        "explanation": "Mounts tmpfs (RAM-backed) filesystem"
    },
    {
        "instruction": "Run container with ulimits",
        "command": "docker run -d --ulimit nofile=65535:65535 myapp",
        "explanation": "Sets file descriptor limits for container"
    },
    {
        "instruction": "Build image with build args",
        "command": "docker build --build-arg VERSION=1.0 --build-arg ENV=prod -t myapp:1.0 .",
        "explanation": "Passes build-time variables to Dockerfile"
    },
    {
        "instruction": "Build image without cache",
        "command": "docker build --no-cache -t myapp:fresh .",
        "explanation": "Forces complete rebuild without layer cache"
    },
    {
        "instruction": "Build with specific Dockerfile",
        "command": "docker build -f Dockerfile.prod -t myapp:prod .",
        "explanation": "Uses Dockerfile.prod instead of default Dockerfile"
    },
    {
        "instruction": "Multi-platform build with buildx",
        "command": "docker buildx build --platform linux/amd64,linux/arm64 -t myapp:multi --push .",
        "explanation": "Builds for multiple architectures and pushes to registry"
    },
    {
        "instruction": "Create buildx builder",
        "command": "docker buildx create --name mybuilder --use",
        "explanation": "Creates and activates new buildx builder instance"
    },
    {
        "instruction": "Inspect buildx builder",
        "command": "docker buildx inspect --bootstrap",
        "explanation": "Shows builder info and ensures it's running"
    },
    {
        "instruction": "Build and load image locally",
        "command": "docker buildx build --load -t myapp:local .",
        "explanation": "Builds with buildx and loads to local Docker"
    },
    {
        "instruction": "View compose configuration",
        "command": "docker compose config",
        "explanation": "Validates and shows resolved compose configuration"
    },
    {
        "instruction": "Stop compose services",
        "command": "docker compose stop",
        "explanation": "Stops services without removing containers"
    },
    {
        "instruction": "Remove compose services",
        "command": "docker compose down -v --rmi local",
        "explanation": "Stops and removes containers, volumes, and local images"
    },
    {
        "instruction": "Restart specific compose service",
        "command": "docker compose restart api",
        "explanation": "Restarts only the api service"
    },
    {
        "instruction": "Pull compose images",
        "command": "docker compose pull",
        "explanation": "Pulls latest images for all services"
    },
    {
        "instruction": "Show compose service status",
        "command": "docker compose ps -a",
        "explanation": "Shows status of all compose services"
    },
    {
        "instruction": "Execute command in compose service",
        "command": "docker compose exec api bash",
        "explanation": "Opens bash shell in running api service container"
    },
    {
        "instruction": "View compose events",
        "command": "docker compose events",
        "explanation": "Streams events from compose services"
    },
    {
        "instruction": "View specific compose logs since time",
        "command": "docker compose logs --since 10m api",
        "explanation": "Shows logs from last 10 minutes for api service"
    },
    {
        "instruction": "Build specific compose service",
        "command": "docker compose build api --no-cache",
        "explanation": "Builds only api service without cache"
    },
    {
        "instruction": "Create compose services without starting",
        "command": "docker compose create",
        "explanation": "Creates containers but doesn't start them"
    },
    {
        "instruction": "Watch and rebuild on changes",
        "command": "docker compose watch",
        "explanation": "Watches for file changes and rebuilds/syncs"
    },
    {
        "instruction": "Copy file from compose service",
        "command": "docker compose cp api:/app/data.json ./data.json",
        "explanation": "Copies file from service container to host"
    },
]

# =============================================================================
# DOCKERFILE EXAMPLES
# =============================================================================

DOCKERFILE_TASKS = [
    {
        "instruction": "Create a Dockerfile for a Python Flask app",
        "dockerfile": """FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home appuser
USER appuser

EXPOSE 5000

CMD ["python", "app.py"]""",
        "explanation": "Multi-layer build with caching, non-root user for security"
    },
    {
        "instruction": "Create a multi-stage Dockerfile for Node.js",
        "dockerfile": """# Build stage
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules

USER node
EXPOSE 3000

CMD ["node", "dist/index.js"]""",
        "explanation": "Multi-stage build reduces final image size by excluding dev dependencies and build tools"
    },
    {
        "instruction": "Create a Dockerfile for a Go application",
        "dockerfile": """# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/server

# Final stage - scratch for minimal image
FROM scratch

COPY --from=builder /app/server /server
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

EXPOSE 8080

ENTRYPOINT ["/server"]""",
        "explanation": "Scratch base for smallest possible image; static binary with no OS"
    },
]

# =============================================================================
# DOCKER COMPOSE EXAMPLES
# =============================================================================

COMPOSE_TASKS = [
    {
        "instruction": "Create docker-compose for a web app with database",
        "compose": """version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgres://user:pass@db:5432/myapp
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=myapp
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d myapp"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:""",
        "explanation": "App waits for healthy db, data persisted in named volume"
    },
    {
        "instruction": "Create docker-compose with nginx reverse proxy",
        "compose": """version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - api

  api:
    build: ./api
    expose:
      - "8000"
    environment:
      - NODE_ENV=production
    deploy:
      replicas: 3

networks:
  default:
    driver: bridge""",
        "explanation": "Nginx load balances across 3 API replicas, only nginx exposed to host"
    },
]

# =============================================================================
# MULTI-STEP PLANNING TASKS
# =============================================================================

PLANNING_TASKS = [
    {
        "instruction": "Containerize an existing Node.js application",
        "steps": [
            "Analyze application dependencies and structure",
            "Create .dockerignore to exclude node_modules, .git, etc.",
            "Write Dockerfile with multi-stage build",
            "Build image: docker build -t myapp:1.0 .",
            "Test locally: docker run -p 3000:3000 myapp:1.0",
            "Create docker-compose.yml for local development",
            "Add healthcheck to container",
            "Configure environment variables properly",
            "Test with production-like settings",
            "Push to container registry"
        ]
    },
    {
        "instruction": "Debug a container that keeps restarting",
        "steps": [
            "Check container status: docker ps -a",
            "View exit code: docker inspect <container> --format='{{.State.ExitCode}}'",
            "Check logs: docker logs --tail 100 <container>",
            "Inspect events: docker events --since 1h",
            "Check resource constraints: docker stats",
            "Verify volume mounts exist",
            "Check environment variables are set correctly",
            "Try running interactively: docker run -it <image> sh",
            "Check for OOM kills: dmesg | grep -i oom"
        ]
    },
    {
        "instruction": "Set up a development environment with Docker",
        "steps": [
            "Create docker-compose.yml with all services",
            "Configure bind mounts for live code reload",
            "Set up hot reload in application",
            "Add database service with persistent volume",
            "Configure networking between services",
            "Create .env file for development secrets",
            "Add convenience scripts (start, stop, logs)",
            "Document setup steps in README"
        ]
    },
    {
        "instruction": "Migrate from docker-compose to production deployment",
        "steps": [
            "Audit security: remove debug flags, use non-root users",
            "Externalize configuration (env vars, configs)",
            "Set up proper logging (stdout, log aggregation)",
            "Configure health checks for all services",
            "Set resource limits (memory, CPU)",
            "Use specific image tags, not :latest",
            "Configure restart policies",
            "Set up secrets management",
            "Plan for zero-downtime deployments",
            "Configure monitoring and alerting"
        ]
    },
    {
        "instruction": "Optimize Docker image size",
        "steps": [
            "Analyze current image: docker history <image>",
            "Use multi-stage builds to exclude build tools",
            "Choose minimal base image (alpine, slim, distroless)",
            "Combine RUN commands to reduce layers",
            "Clean up package manager cache in same layer",
            "Use .dockerignore to exclude unnecessary files",
            "Remove development dependencies",
            "Use dive tool to inspect layers",
            "Consider using scratch for static binaries"
        ]
    },
]

# =============================================================================
# CONCEPT Q&A
# =============================================================================

BASIC_CONCEPTS = [
    {
        "question": "What is the difference between a Docker image and container?",
        "answer": "An image is a read-only template containing the application and its dependencies - think of it as a class definition. A container is a running instance of an image - like an object instantiated from that class. You can run multiple containers from one image. Images are built from Dockerfiles and stored in registries. Containers have writable layers on top of the image layers, but changes are lost when the container is removed unless you use volumes."
    },
    {
        "question": "What is a Docker volume?",
        "answer": "Volumes are Docker's preferred way to persist data outside containers. Types: 1) Named volumes - managed by Docker in /var/lib/docker/volumes, 2) Bind mounts - map host directory to container path, 3) tmpfs - stored in host memory only. Named volumes are recommended for databases and persistent data. Bind mounts are great for development (code sync). Volumes survive container removal and can be shared between containers."
    },
    {
        "question": "How does Docker networking work?",
        "answer": "Docker creates virtual networks for container communication. Default networks: bridge (isolated network per docker-compose), host (shares host network stack), none (no networking). Containers on same bridge network can communicate by service name (DNS resolution). Ports must be explicitly exposed (-p) to be accessible from host. User-defined bridge networks provide automatic DNS resolution between containers."
    },
    {
        "question": "What is docker-compose?",
        "answer": "Docker Compose is a tool for defining and running multi-container applications. You describe services, networks, and volumes in a docker-compose.yml file. Key features: service dependency management (depends_on), environment configuration, volume and network creation, easy scaling (--scale), simplified commands (up, down, logs). It's essential for local development with multiple services like app + database + cache."
    },
    {
        "question": "What is a Dockerfile?",
        "answer": "A Dockerfile is a script containing instructions to build a Docker image. Key instructions: FROM (base image), COPY/ADD (copy files), RUN (execute commands), ENV (set variables), EXPOSE (document ports), CMD/ENTRYPOINT (default command). Best practices: use specific base image tags, minimize layers, order commands for cache efficiency (least-changing first), use multi-stage builds, don't run as root."
    },
    {
        "question": "What is a Docker registry?",
        "answer": "A registry stores and distributes Docker images. Docker Hub is the default public registry. Private options: GitHub Container Registry (ghcr.io), AWS ECR, Azure ACR, Google GCR, Harbor (self-hosted). Images tagged as registry/repository:tag (e.g., ghcr.io/myorg/myapp:v1.0). docker push uploads, docker pull downloads. Registries support authentication, vulnerability scanning, and access control."
    },
    {
        "question": "What does docker run -d mean?",
        "answer": "The -d flag runs container in detached mode (background). Without -d, container runs in foreground and you see output. Common flags: -d (detach), -p (publish ports), -v (volumes), --name (container name), -e (environment variables), --rm (remove on exit), -it (interactive terminal). To see detached container output: docker logs <container>. To attach: docker attach <container>. Use docker exec for new processes."
    },
    {
        "question": "How do I view Docker logs?",
        "answer": "docker logs <container> shows container output (stdout/stderr). Useful flags: -f (follow in real-time), --tail 100 (last 100 lines), --since 1h (last hour), --timestamps (show timestamps). Docker Compose: docker compose logs -f <service>. By default, Docker uses json-file log driver. For production, consider using syslog, fluentd, or cloud logging drivers. Configure: --log-driver and --log-opt flags."
    },
    {
        "question": "What is Docker Hub?",
        "answer": "Docker Hub is Docker's default public registry for sharing container images. Features: public and private repositories, automated builds from GitHub, vulnerability scanning, official images (verified by Docker). Free tier: unlimited public repos, 1 private repo. docker pull nginx gets nginx:latest from Docker Hub. docker login authenticates for pushing. Consider alternatives for private images: GitHub Container Registry, self-hosted Harbor."
    },
    {
        "question": "How do environment variables work in Docker?",
        "answer": "Env vars configure containers at runtime without rebuilding images. Set with: -e VAR=value at runtime, ENV in Dockerfile (baked in), env_file in compose. Access in app normally. Secrets: don't put sensitive values in Dockerfile (visible in image history). Use Docker secrets, mount files, or inject at runtime. docker-compose.yml can use .env file for variable substitution."
    }
]

ADVANCED_CONCEPTS = [
    {
        "question": "How do multi-stage Docker builds work?",
        "answer": "Multi-stage builds use multiple FROM statements to create intermediate images. Each stage can copy artifacts from previous stages. This allows you to: use full build tools in one stage, copy only compiled output to minimal runtime image. Result is much smaller production images. Example: build with node:20 (has npm), copy built files to node:20-alpine or nginx. You can also target specific stages for debugging."
    },
    {
        "question": "What is the difference between CMD and ENTRYPOINT?",
        "answer": "ENTRYPOINT defines the executable that always runs; CMD provides default arguments. When both are set, CMD arguments are passed to ENTRYPOINT. ENTRYPOINT makes containers act like executables (docker run myimage arg). CMD alone can be completely overridden at runtime. Shell form (CMD command) vs exec form (CMD [\"command\"]) - prefer exec form to avoid shell signal handling issues. ENTRYPOINT is harder to override (requires --entrypoint flag)."
    },
    {
        "question": "How does Docker layer caching work?",
        "answer": "Docker caches each layer (instruction result) and reuses it if inputs haven't changed. Cache invalidation: if any layer changes, all subsequent layers rebuild. Strategy: order Dockerfile with least-changing first (base image, dependencies, then code). For COPY, cache checks file checksum. RUN caches based on command string. Use --no-cache to force rebuild. In CI, use --cache-from to pull previous image layers."
    },
    {
        "question": "How do Docker health checks work?",
        "answer": "HEALTHCHECK instruction defines how Docker checks if container is healthy. It runs a command periodically inside the container. Container states: starting, healthy, unhealthy. Parameters: --interval (check frequency), --timeout (max check duration), --retries (failures before unhealthy), --start-period (grace period for startup). Docker Compose depends_on can wait for healthy state. Orchestrators use health checks for rolling updates."
    },
    {
        "question": "What is container orchestration?",
        "answer": "Container orchestration manages deployment, scaling, and operation of containers across multiple hosts. Key features: service discovery, load balancing, rolling updates, self-healing (restart failed containers), secrets management, resource allocation. Tools: Kubernetes (most popular, complex), Docker Swarm (simpler, built-in), Nomad, ECS. Kubernetes concepts: Pods, Deployments, Services, Ingress. For simple needs, docker-compose or Swarm suffice."
    },
    {
        "question": "What are Docker security best practices?",
        "answer": "1) Don't run as root - use USER instruction, 2) Use minimal base images (alpine, distroless), 3) Scan images for vulnerabilities (Trivy, Snyk), 4) Don't store secrets in images - use runtime secrets, 5) Use read-only filesystems when possible, 6) Limit container capabilities (--cap-drop=ALL), 7) Use security profiles (seccomp, AppArmor), 8) Pin image versions, don't use :latest, 9) Keep images updated, 10) Use multi-stage builds to exclude build tools."
    },
    {
        "question": "What is BuildKit?",
        "answer": "BuildKit is Docker's next-gen build system. Enable with DOCKER_BUILDKIT=1 or default in Docker Desktop. Features: parallel build stages, better caching, build secrets (--secret), SSH forwarding for private repos, heredocs in Dockerfile, cache mounts for package managers. Syntax: # syntax=docker/dockerfile:1 enables new features. RUN --mount=type=cache,target=/root/.cache/pip pip install - caches pip downloads across builds."
    },
    {
        "question": "What are distroless images?",
        "answer": "Distroless images contain only your app and runtime dependencies - no shell, package manager, or OS utilities. Benefits: smaller size, smaller attack surface, fewer vulnerabilities. Google provides distroless for Java, Python, Node, etc. Example: gcr.io/distroless/java17. Debugging harder (no shell) - use debug variants or ephemeral debug containers. Combine with multi-stage: build in full image, run in distroless."
    },
    {
        "question": "How do Docker secrets work?",
        "answer": "Docker Swarm secrets store sensitive data (passwords, keys) securely. Secrets encrypted at rest, mounted as files in containers at /run/secrets/<name>. Create: echo 'password' | docker secret create db_pass -. Use in compose: secrets section + reference in service. Not available in plain Docker (non-Swarm) - use alternatives: mount file, env vars (less secure), external secret managers. Kubernetes has its own Secrets API."
    },
    {
        "question": "What is rootless Docker?",
        "answer": "Rootless Docker runs Docker daemon without root privileges. Benefits: no root access even if container escapes, better security for multi-tenant systems. Setup: install with curl -fsSL https://get.docker.com/rootless | sh. Limitations: some features unavailable (--privileged, some network modes), port < 1024 binding needs workaround. Alternative: Podman is rootless by default. Use rootless for better security posture."
    }
]

# =============================================================================
# ERROR/GUARDRAIL SCENARIOS
# =============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "Container can't connect to database",
        "error_type": "networking",
        "response": {
            "status": "needs_investigation",
            "common_causes": [
                "Database container not running or healthy",
                "Wrong hostname - use service name, not localhost",
                "Database not ready when app starts",
                "Wrong port or credentials",
                "Containers on different networks"
            ],
            "diagnostic_steps": [
                "Check both containers running: docker ps",
                "Verify same network: docker network inspect <network>",
                "Test connectivity: docker exec app ping db",
                "Check db logs: docker logs db",
                "Verify environment variables in app"
            ],
            "solutions": [
                "Use service name as hostname in connection string",
                "Add depends_on with healthcheck condition",
                "Ensure containers on same Docker network",
                "Add retry logic to application"
            ]
        }
    },
    {
        "instruction": "Docker build fails with 'no space left on device'",
        "error_type": "resources",
        "response": {
            "status": "recoverable",
            "explanation": "Docker storage is full of unused images, containers, or build cache",
            "solutions": [
                "Clean up unused resources: docker system prune -a",
                "Remove dangling images: docker image prune",
                "Remove stopped containers: docker container prune",
                "Remove unused volumes: docker volume prune",
                "Clear build cache: docker builder prune"
            ],
            "prevention": [
                "Set up regular cleanup jobs",
                "Use --rm with docker run for temporary containers",
                "Configure Docker to limit disk usage"
            ]
        }
    },
    {
        "instruction": "Container keeps getting OOM killed",
        "error_type": "resources",
        "response": {
            "status": "needs_action",
            "explanation": "Container exceeds memory limit and kernel kills it",
            "diagnostic_steps": [
                "Check memory limit: docker inspect <container> | grep Memory",
                "Monitor usage: docker stats <container>",
                "Check for memory leaks in application",
                "Review dmesg for OOM messages"
            ],
            "solutions": [
                "Increase memory limit: --memory=1g",
                "Optimize application memory usage",
                "Add swap limit: --memory-swap=2g",
                "Profile application for memory leaks",
                "Use memory-efficient base image"
            ]
        }
    },
    {
        "instruction": "Volume permissions are wrong inside container",
        "error_type": "permissions",
        "response": {
            "status": "common_issue",
            "explanation": "Host files have different UID/GID than container user",
            "solutions": [
                "Run container with matching UID: docker run --user $(id -u):$(id -g)",
                "Change host permissions to match container user",
                "Use named volumes instead of bind mounts for data",
                "In Dockerfile, create user with matching UID",
                "Use fixuid or similar tools"
            ],
            "compose_example": "user: '${UID}:${GID}' in docker-compose.yml"
        }
    },
    {
        "instruction": "Docker image build is very slow",
        "error_type": "performance",
        "response": {
            "status": "optimizable",
            "causes": [
                "Not leveraging build cache",
                "Copying unnecessary files",
                "Large base image",
                "Many layers"
            ],
            "solutions": [
                "Reorder Dockerfile for cache efficiency",
                "Copy package.json before source code",
                "Use .dockerignore (exclude node_modules, .git)",
                "Use smaller base image",
                "Combine RUN commands",
                "Use BuildKit: DOCKER_BUILDKIT=1 docker build"
            ],
            "cache_tip": "Dependencies change less often than code - install dependencies before copying code"
        }
    },
    {
        "instruction": "I need to run Docker inside Docker",
        "error_type": "security_warning",
        "response": {
            "status": "discouraged",
            "warning": "Docker-in-Docker (DinD) has security and complexity issues",
            "better_alternatives": [
                "Mount Docker socket: -v /var/run/docker.sock:/var/run/docker.sock",
                "Use Kaniko for building images in Kubernetes",
                "Use Buildah for rootless image building",
                "Use host's Docker daemon from container"
            ],
            "if_really_needed": {
                "command": "docker run --privileged -v /var/run/docker.sock:/var/run/docker.sock docker:dind",
                "warning": "--privileged gives container full host access - security risk"
            }
        }
    },
    {
        "instruction": "docker pull: image not found or access denied",
        "error_type": "authentication",
        "response": {
            "status": "troubleshoot",
            "possible_causes": [
                "Typo in image name/tag",
                "Private repository needs authentication",
                "Image truly doesn't exist",
                "Rate limiting (Docker Hub)"
            ],
            "diagnostic_steps": [
                "Verify image exists in registry",
                "Check exact name and tag",
                "Try docker login for private repos"
            ],
            "solutions": {
                "auth_issue": "docker login <registry> (e.g., docker login ghcr.io)",
                "rate_limit": "Authenticate or wait, use alternative registry",
                "private_gcr": "gcloud auth configure-docker",
                "private_ecr": "aws ecr get-login-password | docker login --username AWS --password-stdin <ecr-url>"
            }
        }
    },
    {
        "instruction": "Container exits immediately after starting",
        "error_type": "startup",
        "response": {
            "status": "troubleshoot",
            "explanation": "Container exits when main process exits",
            "diagnostic_steps": [
                "Check exit code: docker ps -a (Exited(N))",
                "View logs: docker logs <container>",
                "Check CMD/ENTRYPOINT in Dockerfile"
            ],
            "common_causes": [
                "Main process exits/crashes immediately",
                "Using shell that exits (CMD without foreground process)",
                "Missing dependencies or config",
                "Permission errors"
            ],
            "solutions": [
                "Ensure CMD runs foreground process",
                "Use exec form: CMD [\"node\", \"server.js\"]",
                "For debugging: docker run -it <image> /bin/sh",
                "Add -t to keep tty open for debugging"
            ]
        }
    },
    {
        "instruction": "docker-compose up fails with port already in use",
        "error_type": "networking",
        "response": {
            "status": "conflict",
            "explanation": "Another process (or container) is using the port",
            "diagnostic_steps": [
                {"linux": "sudo lsof -i :<port>"},
                {"windows": "netstat -ano | findstr :<port>"},
                {"docker": "docker ps (check for conflicting containers)"}
            ],
            "solutions": [
                "Stop conflicting process or container",
                "Use different host port: ports: '3001:3000'",
                "Stop old compose stack: docker compose down",
                "Kill orphan containers: docker compose down --remove-orphans"
            ]
        }
    },
    {
        "instruction": "Changes to code not reflected in container",
        "error_type": "development",
        "response": {
            "status": "common_confusion",
            "explanation": "Code is baked into image at build time",
            "solutions": {
                "for_development": [
                    "Use bind mount for live code: volumes: [./src:/app/src]",
                    "Enable hot reload in your framework",
                    "Ensure .dockerignore doesn't exclude source"
                ],
                "for_rebuilding": [
                    "Rebuild image: docker compose build",
                    "Force rebuild: docker compose build --no-cache",
                    "Recreate container: docker compose up --force-recreate"
                ]
            },
            "tip": "For dev, mount code. For prod, rebuild image."
        }
    },
    {
        "instruction": "Container can't resolve DNS names",
        "error_type": "networking",
        "response": {
            "status": "troubleshoot",
            "checks": [
                "Check container DNS: docker exec <container> cat /etc/resolv.conf",
                "Test DNS: docker exec <container> nslookup google.com",
                "Check Docker daemon DNS settings"
            ],
            "common_causes": [
                "Host firewall blocking Docker's DNS",
                "Corporate network DNS restrictions",
                "Docker DNS daemon issue"
            ],
            "solutions": [
                "Set DNS in daemon.json: {\"dns\": [\"8.8.8.8\", \"8.8.4.4\"]}",
                "Set in container: --dns 8.8.8.8",
                "Use host network mode for debugging",
                "Restart Docker daemon"
            ]
        }
    },
    {
        "instruction": "Docker Compose services not seeing latest .env changes",
        "error_type": "configuration",
        "response": {
            "status": "troubleshoot",
            "explanation": "Environment variables baked in at container creation",
            "checks": [
                "docker compose config - shows interpolated values",
                "docker exec <container> env - shows actual env in container"
            ],
            "solutions": [
                "Recreate containers: docker compose up -d --force-recreate",
                "For runtime env: use env_file directive",
                "For build-time: use args + ARG in Dockerfile",
                "Down and up: docker compose down && docker compose up -d"
            ]
        }
    },
    {
        "instruction": "Getting 'manifest unknown' when pulling image",
        "error_type": "registry",
        "response": {
            "status": "troubleshoot",
            "meaning": "Requested tag doesn't exist in registry",
            "common_causes": [
                "Tag doesn't exist (typo, never pushed)",
                "Platform mismatch (arm64 vs amd64)",
                "Image was deleted from registry"
            ],
            "solutions": {
                "check_available_tags": "docker manifest inspect <image>",
                "specify_platform": "docker pull --platform linux/amd64 <image>",
                "use_latest": "Try without tag to get :latest",
                "verify_exists": "Check registry web UI for available tags"
            },
            "apple_silicon_note": "M1/M2 Macs may need --platform linux/amd64 for some images"
        }
    },
    {
        "instruction": "Container loses data on restart",
        "error_type": "data_persistence",
        "response": {
            "status": "expected_behavior",
            "explanation": "Container filesystem is ephemeral - data in container is lost on removal",
            "solutions": [
                "Use volumes for persistent data: -v mydata:/app/data",
                "Use named volumes for databases",
                "Bind mount for development: -v $(pwd)/data:/app/data",
                "Check volume is correctly mounted: docker inspect <container>"
            ],
            "database_example": {
                "postgres": "volumes: ['postgres_data:/var/lib/postgresql/data']",
                "mysql": "volumes: ['mysql_data:/var/lib/mysql']"
            },
            "warning": "Don't use anonymous volumes for important data"
        }
    },
    {
        "instruction": "docker-compose.yml version warning or deprecated syntax",
        "error_type": "configuration",
        "response": {
            "status": "update_needed",
            "explanation": "Docker Compose v2 deprecates version field and some syntax",
            "changes": [
                "Remove 'version: 3.x' line (no longer needed)",
                "Use 'docker compose' (with space) not 'docker-compose'",
                "depends_on condition syntax changed",
                "Some networking options moved"
            ],
            "depends_on_new_syntax": {
                "old": "depends_on: [db]",
                "new": "depends_on: db: condition: service_healthy"
            },
            "recommendation": "Use latest Compose spec, remove version, update CLI"
        }
    }
]

# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def format_command_response(command: str, explanation: str) -> str:
    """Format as command execution response."""
    return json.dumps({
        "action": "execute_command",
        "shell": "bash",
        "command": command,
        "explanation": explanation
    }, indent=2)

def format_dockerfile_response(dockerfile: str, explanation: str) -> str:
    """Format as Dockerfile creation response."""
    return json.dumps({
        "action": "create_file",
        "filename": "Dockerfile",
        "content": dockerfile,
        "explanation": explanation
    }, indent=2)

def format_compose_response(compose: str, explanation: str) -> str:
    """Format as docker-compose creation response."""
    return json.dumps({
        "action": "create_file",
        "filename": "docker-compose.yml",
        "content": compose,
        "explanation": explanation
    }, indent=2)

def format_planning_response(steps: List[str]) -> str:
    """Format as multi-step plan."""
    return json.dumps({
        "action": "multi_step_plan",
        "steps": [{"step": i+1, "action": step} for i, step in enumerate(steps)],
        "requires_confirmation": True
    }, indent=2)

def format_error_response(error_data: dict) -> str:
    """Format error/guardrail response."""
    return json.dumps(error_data, indent=2)

def generate_tool_examples() -> List[Dict]:
    """Generate tool selection training examples."""
    examples = []
    
    all_tasks = BASIC_DOCKER_TASKS + ADVANCED_DOCKER_TASKS
    
    for task in all_tasks:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_command_response(task["command"], task["explanation"])
        })
    
    # Dockerfile examples
    for task in DOCKERFILE_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_dockerfile_response(task["dockerfile"], task["explanation"])
        })
    
    # Compose examples
    for task in COMPOSE_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_compose_response(task["compose"], task["explanation"])
        })
    
    return examples

def generate_planning_examples() -> List[Dict]:
    """Generate multi-step planning examples."""
    examples = []
    
    for task in PLANNING_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_planning_response(task["steps"])
        })
    
    return examples

def generate_concept_examples() -> List[Dict]:
    """Generate concept Q&A examples."""
    examples = []
    
    for concept in BASIC_CONCEPTS + ADVANCED_CONCEPTS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": concept["question"],
            "response": concept["answer"]
        })
    
    return examples

def generate_error_examples() -> List[Dict]:
    """Generate error handling examples."""
    examples = []
    
    for scenario in ERROR_SCENARIOS:
        response = scenario["response"].copy()
        response["error_type"] = scenario["error_type"]
        
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": scenario["instruction"],
            "response": format_error_response(response)
        })
    
    return examples

def generate_variations() -> List[Dict]:
    """Generate additional variations."""
    variations = []
    
    # Common docker queries
    docker_variations = [
        ("How do I remove all stopped containers?", "docker container prune removes all stopped containers. To remove all containers including running: docker rm -f $(docker ps -aq). For compose: docker compose down removes containers for that project."),
        ("How do I see what's inside a Docker image?", "Several approaches: docker history <image> shows layers and commands. docker run --rm -it <image> sh opens a shell. Use dive tool for visual layer inspection: dive <image>. docker inspect shows image metadata."),
        ("How do I update a running container?", "Containers are immutable - you don't update them in place. Instead: 1) Pull/build new image, 2) Stop old container, 3) Remove old container, 4) Start new container with new image. For compose: docker compose pull && docker compose up -d recreates with new images."),
        ("How do I pass secrets to containers?", "Never bake secrets in images. Options: 1) Environment variables (visible in inspect), 2) Docker secrets (Swarm only), 3) Volume mount secrets file, 4) External secret managers (Vault, AWS Secrets). For compose, use environment or env_file. In production, use proper secrets management."),
    ]
    
    for query, answer in docker_variations:
        variations.append({
            "system": SYSTEM_PROMPT,
            "instruction": query,
            "response": answer
        })
    
    return variations

def main():
    """Generate all Docker training data."""
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating Docker & Containerization Training Data")
    print("=" * 60)
    
    all_examples = []
    
    # Generate each category
    print("\n1. Generating tool selection examples...")
    tool_examples = generate_tool_examples()
    all_examples.extend(tool_examples)
    print(f"   Generated {len(tool_examples)} examples")
    
    print("\n2. Generating planning examples...")
    planning_examples = generate_planning_examples()
    all_examples.extend(planning_examples)
    print(f"   Generated {len(planning_examples)} examples")
    
    print("\n3. Generating concept Q&A...")
    concept_examples = generate_concept_examples()
    all_examples.extend(concept_examples)
    print(f"   Generated {len(concept_examples)} examples")
    
    print("\n4. Generating error/guardrail scenarios...")
    error_examples = generate_error_examples()
    all_examples.extend(error_examples)
    print(f"   Generated {len(error_examples)} examples")
    
    print("\n5. Generating variations...")
    variations = generate_variations()
    all_examples.extend(variations)
    print(f"   Generated {len(variations)} examples")
    
    # Shuffle for training
    random.shuffle(all_examples)
    
    # Save to JSONL
    output_file = output_dir / "docker_containerization.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_examples)} examples to {output_file}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Docker Training Data Generation Complete!")
    print("=" * 60)
    print(f"Total examples: {len(all_examples)}")
    print(f"  Tool selection: {len(tool_examples)}")
    print(f"  Planning: {len(planning_examples)}")
    print(f"  Concepts: {len(concept_examples)}")
    print(f"  Error handling: {len(error_examples)}")
    print(f"  Variations: {len(variations)}")

if __name__ == "__main__":
    main()
