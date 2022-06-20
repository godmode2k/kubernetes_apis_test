#!/bin/sh
#
# Creates New Instance
# filename: creates_instance.sh
#
# hjkim, 2022.05.25
#
#--------------------------------------------------
# Docker Private Registry
# SEE: https://docs.docker.com/registry/
#
# Error: ... http: server gave HTTP response to HTTPS client
# creates /etc/docker/daemon.json
# { "insecure-registries": ["localhost:5000"] }
# $ sudo service docker restart
#
# $ sudo docker run -d -p 5000:5000 --name private-registry registry:latest
# // -v /docker_private_registry/registry:/var/lib/registry/Docker/registry/v2
# $ sudo docker image tag ubuntu localhost:5000/myfirstimage
# $ sudo docker push localhost:5000/myfirstimage
# $ curl -X GET http://localhost:5000/v2/_catalog
# $ curl -X GET http://localhost:5000/v2/myfirstimage/tags/list
# $ sudo docker pull localhost:5000/myfirstimage
#--------------------------------------------------


echo '=================================='
echo 'CREATES_INSTANCE'
echo '=================================='
echo 'FIXME:'
echo '  -> Port selection: DB port (7000 ~), WWW(+WAS) port (8000 ~)'
echo '  -> DB port: 7000, WWW(+WAS) port: 8000, 8001(WWW port +1)'
echo

BIN_DOCKER=/usr/bin/docker
BIN_DOCKER_COMPOSE=/usr/local/bin/docker-compose
DEFAULT_DOCKER_COMPOSE=Docker-compose-default.yml
DEFAULT_RESOURCE_PATH=$HOME
DEFAULT_CLOUD_SERVICE_PATH=$DEFAULT_RESOURCE_PATH/res/cloud_service/default
DEFAULT_VOLUME_MOUNT_PATH=$DEFAULT_RESOURCE_PATH/mnt/cloud
DEFAULT_OS_IMAGE="test_cloud_manager:1.0"


if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] || [ -z "$5" ] || [ -z "$6" ]; then
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "    [Service Name]"
    echo "    [DB root Password] [DB User Password]"
    echo "    [DB port: 7000~] [WWW port: 8000~] [WAS port: WWW port +1]"
    echo
    echo "e.g., $0 test_service1 root1234 user1234 7000 8000 8001"
    exit
fi


OPT_DEFAULT_SERVICE_NAME=$1

OPT_DEFAULT_DB_PORT=$4
OPT_DEFAULT_DB_ROOT_PASSWORD=$2
#OPT_DEFAULT_DB_NAME=
OPT_DEFAULT_DB_USER__SERVICE_NAME=$OPT_DEFAULT_SERVICE_NAME
OPT_DEFAULT_DB_PASSWORD__SERVICE_NAME=$3
OPT_DEFAULT_OS_WWW_PORT=$5
OPT_DEFAULT_OS_WAS_PORT=$6

VOLUME_MOUNT_BASE_PATH="$DEFAULT_VOLUME_MOUNT_PATH/$OPT_DEFAULT_SERVICE_NAME"
VOLUME_MOUNT_PATH="$VOLUME_MOUNT_BASE_PATH/mnt_shared"
VOLUME_MOUNT_PATH_MYSQL="$VOLUME_MOUNT_PATH/mysql"
VOLUME_MOUNT_PATH_WWW="$VOLUME_MOUNT_PATH/www"
#VOLUME_MOUNT_PATH_LOGS="$VOLUME_MOUNT_BASE_PATH/logs"

DOCKER_COMPOSE="Docker-compose-$OPT_DEFAULT_SERVICE_NAME.yml"
DOCKER_COMPOSE_FILE_PATH="$VOLUME_MOUNT_BASE_PATH/$DOCKER_COMPOSE"

# checks path
if [ ! -d "$VOLUME_MOUNT_PATH" ]; then
    mkdir -p $VOLUME_MOUNT_PATH
    mkdir -p $VOLUME_MOUNT_PATH_MYSQL
    mkdir -p $VOLUME_MOUNT_PATH_WWW
    #mkdir -p $VOLUME_MOUNT_PATH_LOGS
else
    echo "CREATES VOLUME MOUNT DIRECTORY [FAIL]"
    echo "Directory Exists"
    echo "Path: $VOLUME_MOUNT_PATH"
    exit
fi

# checks again
if [ ! -d "$VOLUME_MOUNT_PATH" ] ||
 [ ! -d "$VOLUME_MOUNT_PATH_MYSQL" ] ||
 [ ! -d "$VOLUME_MOUNT_PATH_WWW" ]; then
 #[ ! -d "$VOLUME_MOUNT_PATH_LOGS" ]; then
    echo "CREATES VOLUME MOUNT DIRECTORY [FAIL]"
    echo "No such file or directory"
    echo "Path: $VOLUME_MOUNT_PATH"
    echo "Path: $VOLUME_MOUNT_PATH_MYSQL"
    echo "Path: $VOLUME_MOUNT_PATH_WWW"
    #echo "Path: $VOLUME_MOUNT_PATH_LOGS"
    exit
else
    echo "CREATES VOLUME MOUNT DIRECTORY [SUCCESS]"
fi

echo "CREATES docker-compose yml file"
echo "Filename: $DOCKER_COMPOSE_FILE_PATH"
cat << EOF >> $DOCKER_COMPOSE_FILE_PATH
services:
  $(echo "$OPT_DEFAULT_SERVICE_NAME")_mysql:
    container_name: $(echo "$OPT_DEFAULT_SERVICE_NAME")_mysql
    image: mysql:latest
    ports:
      - "$(echo "$OPT_DEFAULT_DB_PORT"):3306"
    environment:
      - MYSQL_ROOT_PASSWORD=$(echo "$OPT_DEFAULT_DB_ROOT_PASSWORD")
      #- MYSQL_DATABASE=$(echo "$OPT_DEFAULT_DB_NAME") # import schema later
      - MYSQL_USER=$(echo "$OPT_DEFAULT_DB_USER__SERVICE_NAME")
      - MYSQL_PASSWORD=$(echo "$OPT_DEFAULT_DB_PASSWORD__SERVICE_NAME")
    restart: always
    volumes:
      - $(echo "$VOLUME_MOUNT_PATH_MYSQL"):/var/lib/mysql

  $(echo "$OPT_DEFAULT_SERVICE_NAME")_www:
    container_name: $(echo "$OPT_DEFAULT_SERVICE_NAME")_www
    image: $(echo "$DEFAULT_OS_IMAGE")
    ports:
      - "$(echo "$OPT_DEFAULT_OS_WWW_PORT"):80"
      - "$(echo "$OPT_DEFAULT_OS_WAS_PORT"):8080"
    depends_on:
      - $(echo "$OPT_DEFAULT_SERVICE_NAME")_mysql
    #links:
    #  - $(echo "$OPT_DEFAULT_SERVICE_NAME")_mysql:$(echo "$OPT_DEFAULT_SERVICE_NAME")_mysql
    restart: always
    volumes:
      - $(echo "$VOLUME_MOUNT_PATH_WWW"):/var/www/html
      #- $(echo "$VOLUME_MOUNT_PATH_LOGS"):/var/log

EOF

if [ $? -ne 0 ]; then
    echo "CREATES INSTANCE [FAIL]"
else
    echo "CREATES INSTANCE [SUCCESS]"
fi



echo '=================================='
echo 'INSTANCE UP...'
echo '=================================='
$BIN_DOCKER_COMPOSE -f $DOCKER_COMPOSE_FILE_PATH up -d

if [ $? -ne 0 ]; then
    echo "INSTANCE UP [FAIL]"
else
    echo "INSTANCE UP [SUCCESS]"
fi




