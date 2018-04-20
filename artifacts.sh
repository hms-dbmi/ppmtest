#!/bin/bash

# Get the path where to store artifacts
if [ -z ${1+x} ]; then
    echo "The path to artifacts directory is required"
    exit 1
fi

# Create a container
mkdir -p "$1"

# Get the hub container
HUB="$(docker-compose ps -q hub)"

# Get the name of the output volume
VOLUME=$(docker inspect --format '{{ range .Mounts }}{{ if eq .Destination "/home/seluser/videos" }}{{ .Name }}{{ end }}{{ end }}' $HUB)

# Copy the videos
docker run --rm -v "$1":/artifacts -v "$VOLUME":/videos busybox sh -c 'cp /videos/*.mp4 /artifacts/ && chmod 777 /artifacts/*'