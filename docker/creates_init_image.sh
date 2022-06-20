#!/bin/sh
#
# Creates New Image
# filename: creates_init_image.sh
#
# hjkim, 2022.05.25
#

echo '=================================='
echo 'CREATES_INIT_IMAGE'
echo '=================================='

BIN_DOCKER=/usr/bin/docker
DEFAULT_DOCKERFILE=Dockerfile_cloud_manager.default

OPT_TAG_NAME=$1
OPT_TAG_VERSION=$2


if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 [Tag Name] [Tag Version]"
    exit
fi

echo '=================================='
echo "TAG = $1:$2"
echo '=================================='


$BIN_DOCKER build -f $DEFAULT_DOCKERFILE --tag $OPT_TAG_NAME:$OPT_TAG_VERSION .

if [ $? -ne 0 ]; then
    echo '=================================='
    echo "build [FAIL]"
    echo '=================================='
else
    echo '=================================='
    echo "build [SUCCESS]"
    echo '=================================='
fi

