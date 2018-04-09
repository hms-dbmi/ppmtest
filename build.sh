#!/bin/bash

# Check for a testing app
if [ -z ${1+x} ]; then
  exit 0
else
    # Determine where app sources are located
    APPS_DIR=${PPM_APPS_DIR:-"./apps/"}

    cat > ./docker-compose.override.yml <<EOL
version: '2.1'
services:
EOL
    for i in $(echo $1 | sed "s/,/ /g")
    do

        # Make sure the source exists
        CONTEXT="$APPS_DIR/$i"
        if [ ! -f "$CONTEXT" ]; then
            echo "$i - App source directory does not exist: $CONTEXT" >&2
        else

            # Set the image name
            IMAGE="ppmtest/$i:test"

            # Replace its image
            echo "Building $i -> $IMAGE"

            # Build it
            docker build -t "$IMAGE" "$CONTEXT"

            # Append the override
            cat >> ./docker-compose.override.yml <<EOL
  $i:
    image: $IMAGE
EOL
        fi
    done
fi

# Ensure override is not empty
if [[ $(wc -l <./docker-compose.override.yml) -lt 4 ]]; then

    # Remove it
    echo "No apps were build, removing docker-compose.override.yml" >&2
    rm ./docker-compose.override.yml

fi