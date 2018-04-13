#!/bin/bash

# Check for a testing app
if [ -z ${1+x} ]; then
    echo "The app identifier is required"
    exit 1
elif [ -z ${2+x} ]; then
    echo "The path to the app's build context is required"
    exit 1
fi

# Set the image name
IMAGE="${3:-ppmtest}/$1"

# Replace its image
echo "Building $1 -> $IMAGE"

# Build it
#docker build -t "$IMAGE" "$2"

# Initialize the override file
cat > ./docker-compose.override.yml <<EOL
version: '2.1'
services:
  $1:
    image: $IMAGE
EOL
