# coding: utf-8

# -------------------------------------------------------------------
# Purpose: Docker APIs test
# Author: Ho-Jung Kim (godmode2k@hotmail.com)
# Date: Since May 25, 2022
#
# Reference:
# - https://docs.docker.com/engine/api/sdk/
# - https://docker-py.readthedocs.io/en/stable/
#
# $ pip install docker
#
# License:
#
#*
#* Copyright (C) 2021 Ho-Jung Kim (godmode2k@hotmail.com)
#*
#* Licensed under the Apache License, Version 2.0 (the "License");
#* you may not use this file except in compliance with the License.
#* You may obtain a copy of the License at
#*
#*      http://www.apache.org/licenses/LICENSE-2.0
#*
#* Unless required by applicable law or agreed to in writing, software
#* distributed under the License is distributed on an "AS IS" BASIS,
#* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#* See the License for the specific language governing permissions and
#* limitations under the License.
#*
# -------------------------------------------------------------------



import requests
import json
import datetime
import traceback
import sys
import time
import os

# pip install PyMySQL
#import pymysql

# Docker client
# SEE: https://docker-py.readthedocs.io/en/stable/
# $ pip install docker
import docker



# ---------------------------------------------------------



# Requests:
#
# Create an instance
# req_json = '{ "request": {"req": "create_instance", "service_name": "test_service1",
# "db_root_password": "root1234", "db_user_password": "user1234",
# "db_port": "7000:3306", # "www_port": "8000:80", "was_port": "8001:8080"} }'
#
# Image list
# req_json = '{ "request": {"req": "image_list"} }'
#
# Container list
# req_json = '{ "request": {"req": "container_list"} }'
#
# Start the container
# req_json = '{ "request": {"req": "container_start", "container_id": "..."} }'
#
# Stop the container
# req_json = '{ "request": {"req": "container_stop", "container_id": "..."} }'
#
# Remove the container
# req_json = '{ "request": {"req": "container_remove", "container_id": "..."} }'
#

#request_container_service( req_json )


# ---------------------------------------------------------



docker_client = docker.from_env()
#print( docker_client.containers.list() )

def request_container_service(req_json):
    #print( "request_container_service()" )

    """
    try:
    except Exception as e:
        traceback.print_exc()
        sys.exit(0)
    """

    # req_json =
    # {"req": "create_instance", "service_name": "test_service1",
    # "db_root_password": "root1234", "db_user_password": "user1234",
    # //! NOTE: container port is fixed
    # "db_port": "7000:3306", "www_port": "8000:80", "was_port": "8001:8080"}

    _req_req = req_json["req"]
    _req_service_name = req_json["service_name"] if "service_name" in req_json else ""
    _req_db_root_password = req_json["db_root_password"] if "db_root_password" in req_json else ""
    _req_db_user_password = req_json["db_user_password"] if "db_user_password" in req_json else ""
    _req_db_port = req_json["db_port"] if "db_port" in req_json else ""
    _req_www_port = req_json["www_port"] if "www_port" in req_json else ""
    _req_was_port = req_json["was_port"] if "was_port" in req_json else ""

    # Volume mount
    # - Database
    # - Web Server (WWW)
    # - Logs
    SERVICE_NAME = _req_service_name
    DEFAULT_IMAGE_NAME_DB = "mysql:latest"
    DEFAULT_IMAGE_NAME_WWW = "test_cloud_manager:1.0"
    DEFAULT_CONTAINER_NAME_DB = _req_service_name + "_mysql"
    DEFAULT_CONTAINER_NAME_WWW = _req_service_name + "_www"
    DEFAULT_HOST_MOUNT_BASE_PATH = "/mnt/cloud" + "/" + SERVICE_NAME
    DEFAULT_HOST_MOUNT_PATH = DEFAULT_HOST_MOUNT_BASE_PATH + "/mnt_shared"
    DEFAULT_HOST_MOUNT_PATH_DB = DEFAULT_HOST_MOUNT_PATH + "/mysql"
    DEFAULT_HOST_MOUNT_PATH_WWW = DEFAULT_HOST_MOUNT_PATH + "/apache2"
    #DEFAULT_HOST_MOUNT_PATH_LOGS = DEFAULT_HOST_MOUNT_PATH + "/logs"
    DEFAULT_CONTAINER_MOUNT_PATH_DB = "/var/lib/mysql"
    DEFAULT_CONTAINER_MOUNT_PATH_WWW = "/var/www/html"
    #DEFAULT_CONTAINER_MOUNT_PATH_LOGS = "/var/log"
    DEFAULT_DOCKER_COMPOSE_FILE = "Docker-compose-" + SERVICE_NAME + ".yml"
    DEFAULT_DOCKER_COMPOSE_FILE_PATH = DEFAULT_HOST_MOUNT_PATH + "/" + DEFAULT_DOCKER_COMPOSE_FILE


    # Private Registry



    print( "request_container_service():", "req = ", _req_req )

    res = { "result": "" }
    container_id_db = None
    container_id_www = None
    fp_compose_file = None

    if _req_req == "create_instance":
        # Creates volume directories
        DEFAULT_HOST_MOUNT_BASE_PATH = "/mnt/cloud" + "/" + SERVICE_NAME
        DEFAULT_HOST_MOUNT_PATH = DEFAULT_HOST_MOUNT_BASE_PATH + "/mnt_shared"
        DEFAULT_HOST_MOUNT_PATH_DB = DEFAULT_HOST_MOUNT_PATH + "/mysql"
        DEFAULT_HOST_MOUNT_PATH_WWW = DEFAULT_HOST_MOUNT_PATH + "/apache2"
        #DEFAULT_HOST_MOUNT_PATH_LOGS = DEFAULT_HOST_MOUNT_PATH + "/logs"

        try:
            # Base path
            #if not os.path.exists(DEFAULT_HOST_MOUNT_PATH):
            #    os.makedirs( DEFAULT_HOST_MOUNT_PATH )

            # Endpoint path
            if not os.path.exists(DEFAULT_HOST_MOUNT_PATH_DB):
                os.makedirs( DEFAULT_HOST_MOUNT_PATH_DB )
            else:
                ret_msg = f'"{DEFAULT_HOST_MOUNT_PATH_DB}" directory is exist'
                res["result"] = { "ret": "false", "msg": ret_msg }
                return res
            if not os.path.exists(DEFAULT_HOST_MOUNT_PATH_WWW):
                os.makedirs( DEFAULT_HOST_MOUNT_PATH_WWW )
            else:
                ret_msg = f'"{DEFAULT_HOST_MOUNT_PATH_WWW}" directory is exist'
                res["result"] = { "ret": "false", "msg": ret_msg }
                return res


            # Creates docker-compose file
            DEFAULT_DOCKER_COMPOSE = f'\
services:\n\
  {SERVICE_NAME}_mysql:\n\
    container_name: {SERVICE_NAME}_mysql\n\
    image: {DEFAULT_IMAGE_NAME_DB}\n\
    ports:\n\
      - "{_req_db_port}"\n\
    environment:\n\
      - MYSQL_ROOT_PASSWORD={_req_db_root_password}\n\
      #- MYSQL_DATABASE=... # import schema later\n\
      - MYSQL_USER={SERVICE_NAME}\n\
      - MYSQL_PASSWORD={_req_db_user_password}\n\
    restart: always\n\
    volumes:\n\
      - {DEFAULT_HOST_MOUNT_PATH_DB}:{DEFAULT_CONTAINER_MOUNT_PATH_DB}\n\
\n\
  {SERVICE_NAME}_www:\n\
    container_name: {SERVICE_NAME}_www\n\
    image: {DEFAULT_IMAGE_NAME_WWW}\n\
    ports:\n\
      - "{_req_www_port}"\n\
      - "{_req_was_port}"\n\
    depends_on:\n\
      - {DEFAULT_CONTAINER_NAME_DB}\n\
    #links:\n\
    #  - ..._mysql:..._mysql\n\
    restart: always\n\
    volumes:\n\
      - {DEFAULT_HOST_MOUNT_PATH_WWW}:{DEFAULT_CONTAINER_MOUNT_PATH_WWW}\n\
      #- ...:/var/log\n\
'
            if not os.path.exists(DEFAULT_DOCKER_COMPOSE_FILE_PATH):
                fp_compose_file = open( DEFAULT_DOCKER_COMPOSE_FILE_PATH, "w" )
                fp_compose_file.write( DEFAULT_DOCKER_COMPOSE )
                fp_compose_file.flush()
                fp_compose_file.close()
            else:
                ret_msg = f'"{DEFAULT_DOCKER_COMPOSE_FILE_PATH}" file is exist'
                res["result"] = { "ret": "false", "msg": ret_msg }
                return res


            """
            # Own Network:
            networking_config_db = docker_client.api.create_networking_config({
                'network_': docker_client.api.create_endpoint_config(
                    #ipv4_address = '',
                    #aliases = ['', ''],
                    links = [(DEFAULT_CONTAINER_NAME_DB, DEFAULT_CONTAINER_NAME_DB)]
                )
            })
            """


            # Container: Database
            container_id_db = docker_client.api.create_container(
                DEFAULT_IMAGE_NAME_DB, name = DEFAULT_CONTAINER_NAME_DB,
                ports = [_req_db_port.split(":")[1]], # container port
                volumes = [DEFAULT_CONTAINER_MOUNT_PATH_DB],
                environment = {
                    "MYSQL_ROOT_PASSWORD" : _req_db_root_password,
                    #"MYSQL_DATABASE" : "" # import schema later
                    "MYSQL_USER" : SERVICE_NAME,
                    "MYSQL_PASSWORD" : _req_db_user_password
                },
                detach = True,
                host_config = docker_client.api.create_host_config(
                    restart_policy = { "Name" : "always" },
                    port_bindings = {
                        # Port ( container : host )
                        _req_db_port.split(":")[1] : _req_db_port.split(":")[0],
                    },
                    binds = {
                        # Volume
                        #DEFAULT_HOST_MOUNT_PATH_DB + ":" + DEFAULT_CONTAINER_MOUNT_PATH_DB,
                        DEFAULT_HOST_MOUNT_PATH_DB : {
                            'bind' : DEFAULT_CONTAINER_MOUNT_PATH_DB,
                            'mode' : 'rw',
                        }
                    }
                )
            )
            if container_id_db != None:
                docker_client.api.start( container_id_db )
                container_id_db["id_digest"] = container_id_db["Id"][:12]
            else:
                ret_msg = f'Start container ({DEFAULT_CONTAINER_NAME_DB}): fail...'
                res["result"] = { "ret": "false", "msg": ret_msg }
                return res


            # Container: WWW (WAS)
            container_id_www = docker_client.api.create_container(
                DEFAULT_IMAGE_NAME_WWW, name = DEFAULT_CONTAINER_NAME_WWW,
                ports = [_req_www_port.split(":")[1]], # container port
                volumes = [DEFAULT_CONTAINER_MOUNT_PATH_WWW],
                detach = True,
                #networking_config = networking_config_db,
                host_config = docker_client.api.create_host_config(
                    restart_policy = { "Name" : "always" },
                    links = [(DEFAULT_CONTAINER_NAME_DB, DEFAULT_CONTAINER_NAME_DB)],
                    port_bindings = {
                        # Port ( container : host )
                        _req_www_port.split(":")[1] : _req_www_port.split(":")[0]
                    },
                    binds = {
                        # Volume
                        #DEFAULT_HOST_MOUNT_PATH_WWW + ":" + DEFAULT_CONTAINER_MOUNT_PATH_WWW,
                         DEFAULT_HOST_MOUNT_PATH_WWW : {
                            'bind' : DEFAULT_CONTAINER_MOUNT_PATH_WWW,
                            'mode' : 'rw',
                        }
                    }
                )
            )
            if container_id_www != None:
                docker_client.api.start( container_id_www )
                container_id_www["id_digest"] = container_id_www["Id"][:12]
            else:
                ret_msg = f'Start container ({DEFAULT_CONTAINER_NAME_WWW}): fail...'
                res["result"] = { "ret": "false", "msg": ret_msg }
                return res

            ret_msg = {"containers": [container_id_db, container_id_www]}
            res["result"] = { "ret": "true", "msg": ret_msg }
        except Exception as e:
            traceback.print_exc()
            #sys.exit(0)

            if fp_compose_file != None:
                fp_compose_file.close()

            try:
                docker_client.api.stop( container_id_db )
            except Exception as e_db1:
                traceback.print_exc()
                pass
            try:
                docker_client.api.stop( container_id_www )
            except Exception as e_www1:
                traceback.print_exc()
                pass

            try:
                if container_id_db != None:
                    docker_client.api.remove_container( container_id_db )
            except Exception as e_db2:
                traceback.print_exc()
                pass
            try:
                if container_id_www != None:
                    docker_client.api.remove_container( container_id_www )
            except Exception as e_www2:
                traceback.print_exc()
                pass

            ret_msg = f'Internal error: stop and removed the containers'
            res["result"] = { "ret": "false", "msg": ret_msg }
            return res
    elif _req_req == "image_list":
        #print( "request_container_service():", docker_client.images.list() )
        _res = docker_client.images.list()
        res["result"] = []

        for image in _res:
            #print( image.id )
            #print( image.tags )
            res["result"].append( image.tags[0] )
    elif _req_req == "container_list":
        #print( "request_container_service():", docker_client.containers.list() )
        _res = docker_client.containers.list()
        # ADD: filters [ "restarting", "running", "paused", "exited" ]
        #_req_filters = req_json["filters"]
        #filters = { "status": _req_filters }
        #_res = docker_client.containers.list( filters = filters )
        res["result"] = []

        for container in _res:
            #print( container.name, container.id[:12] )
            res["result"].append( [container.name, container.id[:12]] )
    elif _req_req == "container_start":
        #print( "request_container_service(): start" )
        pass
    elif _req_req == "container_stop":
        #print( "request_container_service(): stop" )
        _req_container_id = req_json["container_id"]

        try:
            docker_client.api.stop( _req_container_id )
            ret_msg = {"containers": [_req_container_id]}
            res["result"] = { "ret": "true", "msg": ret_msg }
        except Exception as e:
            traceback.print_exc()
            #sys.exit(0)

            ret_msg = f'Internal error: stop the container'
            res["result"] = { "ret": "false", "msg": ret_msg }
            return res
    elif _req_req == "container_remove":
        #print( "request_container_service(): remove" )
        _req_container_id = req_json["container_id"]

        try:
            docker_client.api.stop( _req_container_id )
        except Exception as e:
            traceback.print_exc()
            #sys.exit(0)
            pass

        try:
            docker_client.api.remove_container( _req_container_id )
            ret_msg = {"containers": [_req_container_id]}
            res["result"] = { "ret": "true", "msg": ret_msg }
        except Exception as e_db2:
            traceback.print_exc()
            #sys.exit(0)

            ret_msg = f'Internal error: stop and remove the container'
            res["result"] = { "ret": "false", "msg": ret_msg }
            return res
    else:
        result = { "res": "false" }
        #res = json.loads(str(result))
        res = json.loads(json.dumps(result).encode("utf8"))

    return res



if __name__ == "__main__":
    # Create an instance
    # req_json = '{ "request": {"req": "create_instance", "service_name": "test_service1",
    # "db_root_password": "root1234", "db_user_password": "user1234",
    # "db_port": "7000:3306", # "www_port": "8000:80", "was_port": "8001:8080"} }'
    #
    # Image list
    # req_json = '{ "request": {"req": "image_list"} }'
    #
    # Container list
    # req_json = '{ "request": {"req": "container_list"} }'
    #
    # Start the container
    # req_json = '{ "request": {"req": "container_start", "container_id": "..."} }'
    #
    # Stop the container
    # req_json = '{ "request": {"req": "container_stop", "container_id": "..."} }'
    #
    # Remove the container
    # req_json = '{ "request": {"req": "container_remove", "container_id": "..."} }'
    #

    request_container_service( req_json )


