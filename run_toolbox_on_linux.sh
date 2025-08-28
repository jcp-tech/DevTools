#!/bin/bash
# This script loads environment variables from .env and runs the toolbox Docker container

# Export all variables from .env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi


# Run the toolbox Docker container with MySQL environment variables from .env

## Need to choose (Option 1)
# docker run --rm -p 5000:5000 \
#   -v "$(pwd)/tools.yaml:/app/tools.yaml" \
#   $(env | grep -v '^PWD=' | grep -v '^SHLVL=' | grep -v '^_' | awk -F= '{print "-e "$1}') \
#   us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:0.10.0 \
#   --tools-file /app/tools.yaml

## Need to choose (Option 2)
# docker run --rm -p 5000:5000 \
#   -e MYSQL_HOST="$MYSQL_HOST" \
#   -e MYSQL_PORT="$MYSQL_PORT" \
#   -e MYSQL_USER="$MYSQL_USER" \
#   -e MYSQL_PASSWORD="$MYSQL_PASSWORD" \
#   -e MYSQL_DATABASE="$MYSQL_DATABASE" \
#   us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:0.10.0 \
#   --prebuilt mysql

## Run Using
# chmod +x run_toolbox_docker.sh
# ./run_toolbox_docker.sh