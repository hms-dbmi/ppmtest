#!/bin/bash

# Check for a testing app
if [ -z ${1+x} ]; then
  exit 0
else
    cat > ./docker-compose.override.yml <<EOL
version: '2.1'
services:
EOL
    for i in $(echo $1 | sed "s/,/ /g")
    do
        # call your procedure/other scripts here below
        echo "$i"

        # Set the image name
        IMAGE="ppmtest/$i:test"

        # Replace its image
        echo "Building $i -> $IMAGE"

        # Build the image
        docker build -t "$IMAGE" ./apps/$i

        cat >> ./docker-compose.override.yml <<EOL
  $i:
    image: $IMAGE
EOL
  done
fi