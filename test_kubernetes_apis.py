# coding: utf-8

# -------------------------------------------------------------------
# Purpose: Kubernetes APIs test
# Author: Ho-Jung Kim (godmode2k@hotmail.com)
# Date: Since June 16, 2022
#
# Reference:
# - https://github.com/kubernetes-client/python
# - https://kubernetes.io/docs/reference/kubernetes-api/
# - https://kubernetes.io/docs/reference/kubectl/cheatsheet/
# - https://kubernetes.io/docs/reference/kubectl/docker-cli-to-kubectl/
# - https://github.com/kubernetes-client/python/tree/master/kubernetes/docs
#
# $ pip install kubernetes
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

# Kubernetes client
# SEE: https://github.com/kubernetes-client/python
# pip install kubernetes
from kubernetes import client, config



# ---------------------------------------------------------



from kubernetes import client, config

# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()


DEFAULT_NAMESPACE = "default"

# Pull From Docker Private Registry
DEPLOYMENT_IMAGE = "docker_image_ip:5000/test_img:1.0"
DEPLOYMENT_NAME = "test1-img"
DEPLOYMENT_SERVICE_NAME = "test1-img-service"
DEPLOYMENT_INGRESS_NAME = "test1-img-ingress"
# By default, the range of the service NodePorts is 30000-32768.
# This range contains 2768 ports, which means that you can create up to 2768 services with NodePorts.
# 30000: 8080 (Tomcat9)
# 30001: 3306 (MariaDB)
# --service-node-port-range=30000-40000
DEPLOYMENT_PORT_NAME__CONTAINER_WAS = "tomcat"
DEPLOYMENT_PORT_NAME__CONTAINER_DB = "mariadb"
DEPLOYMENT_PORT_EXPOSE__CONTAINER_WAS = int(30000)
DEPLOYMENT_PORT_EXPOSE__CONTAINER_DB = int(30001)
DEPLOYMENT_PORT__CONTAINER_WAS = int(8080)
DEPLOYMENT_PORT__CONTAINER_DB = int(3306)


def pod_list():
    print("Listing pods with their IPs:")

    v1 = client.CoreV1Api()

    ret = v1.list_pod_for_all_namespaces(watch=False)
    for i in ret.items:
        if i.metadata.namespace == "kube-system":
            continue

        print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))

def create_deployment():
    print( "create_deployment()" )

    apps_v1_api = client.AppsV1Api()

    container = client.V1Container(
        name = DEPLOYMENT_NAME,
        image = DEPLOYMENT_IMAGE,
        ports = [
            client.V1ContainerPort( container_port = DEPLOYMENT_PORT_EXPOSE__CONTAINER_WAS ),
            client.V1ContainerPort( container_port = DEPLOYMENT_PORT_EXPOSE__CONTAINER_DB )
        ]
    )

    template = client.V1PodTemplateSpec(
        metadata = client.V1ObjectMeta( labels = { "app" : DEPLOYMENT_NAME } ),
        spec = client.V1PodSpec( containers = [container] )
    )

    spec = client.V1DeploymentSpec(
        replicas = 1,
        selector = client.V1LabelSelector(
            match_labels = { "app" : DEPLOYMENT_NAME }
        ),
        template = template
    )

    deployment = client.V1Deployment(
        api_version = "apps/v1",
        kind = "Deployment",
        metadata = client.V1ObjectMeta( name = DEPLOYMENT_NAME ),
        spec = spec
    )

    apps_v1_api.create_namespaced_deployment(
        namespace = DEFAULT_NAMESPACE,
        body = deployment
    )

def create_service():
    print( "create_service()" )

    core_v1_api = client.CoreV1Api()

    body = client.V1Service(
        api_version = "v1",
        kind = "Service",
        metadata = client.V1ObjectMeta(
            name = DEPLOYMENT_SERVICE_NAME
        ),
        spec = client.V1ServiceSpec(
            type = "LoadBalancer",
            #type = "NodePort",
            external_i_ps = ["<worker node ip"],
            selector = { "app": DEPLOYMENT_NAME },
            ports = [
                client.V1ServicePort(
                    name = DEPLOYMENT_PORT_NAME__CONTAINER_WAS,
                    node_port = DEPLOYMENT_PORT_EXPOSE__CONTAINER_WAS,
                    port = DEPLOYMENT_PORT__CONTAINER_WAS,
                    target_port = DEPLOYMENT_PORT__CONTAINER_WAS
                ),
                client.V1ServicePort(
                    name = DEPLOYMENT_PORT_NAME__CONTAINER_DB,
                    node_port = DEPLOYMENT_PORT_EXPOSE__CONTAINER_DB,
                    port = DEPLOYMENT_PORT__CONTAINER_DB,
                    target_port = DEPLOYMENT_PORT__CONTAINER_DB
                )
            ]
        )
    )

    core_v1_api.create_namespaced_service(
        namespace = DEFAULT_NAMESPACE,
        body = body
    )

"""
def create_ingress():
    print( "create_ingress()" )

    body = client.V1Ingress(
        api_version = "networking.k8s.io/v1",
        kind = "Ingress",
        metadata = client.V1ObjectMeta(
            name = DEPLOYMENT_INGRESS_NAME,
            annotations = {
                "nginx.ingress.kubernetes.io/rewrite-target": "/"
            }
        ),
        spec = client.V1IngressSpec(
            rules = [ client.V1IngressRule(
                host = "example.com",
                http = client.V1HTTPIngressRuleValue(
                    paths = [ client.V1HTTPIngressPath(
                        path = "/",
                        path_type = "Exact",
                        backend = client.V1IngressBackend(
                            service = client.V1IngressServiceBackend(
                                port = client.V1ServieBackendPort(
                                    number = 0
                                ),
                                name = DEPLOYMENT_SERVICE_NAME
                            )
                        )
                    ) 
                )
            )
        )
    )
"""



if __name__ == "__main__":
    pod_list()
    #create_deployment()
    #create_service()


