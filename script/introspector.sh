#!/bin/bash

set -e

DEFAULT_CONFIGS="$(pwd)/configs"

INTROSPECTOR_CONFIG_PATH=${INTROSPECTOR_CONFIG_PATH:-$DEFAULT_CONFIGS}

mkdir -p $INTROSPECTOR_CONFIG_PATH

docker run -it --rm --mount type=bind,source="$(realpath $INTROSPECTOR_CONFIG_PATH)",target=/app/configs davea/introspector $@
