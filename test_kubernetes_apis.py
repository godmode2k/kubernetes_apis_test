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
#
# By default, the range of the service NodePorts is 30000-32768.
# This range contains 2768 ports, which means that you can create up to 2768 services with NodePorts.
# 30000: 8080 (Tomcat9)
# 30001: 3306 (MariaDB)
# --service-node-port-range=30000-40000
#
# Connect -> NodePort -> Port (Pod) -> TargetPort (Container Port)
# NodePort (30000) -> Port (30000) -> TargetPort (8080)
#
DEPLOYMENT_PORT_NAME__CONTAINER_WAS = "tomcat"
DEPLOYMENT_PORT_NAME__CONTAINER_DB = "mariadb"
DEPLOYMENT_PORT_EXPOSE__CONTAINER_WAS = int(30000)
DEPLOYMENT_PORT_EXPOSE__CONTAINER_DB = int(30001)
DEPLOYMENT_PORT__CONTAINER_WAS = int(8080)
DEPLOYMENT_PORT__CONTAINER_DB = int(3306)


def node_list():
    print( "node_list()" )

    res = []

    v1 = client.CoreV1Api()

    ret = v1.list_node(watch=False)
    for i in ret.items:
        if i.metadata.namespace == "kube-system":
            continue

        ipaddr = i.metadata.annotations["projectcalico.org/IPv4Address"].split("/")[0]
        ipaddr_internal = i.metadata.annotations["projectcalico.org/IPv4IPIPTunnelAddr"]

        #print( i.spec )
        #print( i.metadata )
        print( "%s\t%s\t%s\t%s" % (i.metadata.name, ipaddr, ipaddr_internal, i.metadata.uid) )

        data = { "node_name": i.metadata.name, "ip": ipaddr }
        res.append( data )

    return res

def deployment_list():
    print( "deployment_list()" )

    res = []

    v1 = client.AppsV1Api()

    ret = v1.list_deployment_for_all_namespaces(watch=False)
    for i in ret.items:
        if i.metadata.namespace == "kube-system":
            continue

        #print( i.metadata )
        print( "%s\t%s" % (i.metadata.namespace, i.metadata.name) )

        data = { "name": i.metadata.name }
        res.append( data )

    return res

def pod_list():
    print( "pod_list()" )

    res = []

    v1 = client.CoreV1Api()

    ret = v1.list_pod_for_all_namespaces(watch=False)
    for i in ret.items:
        if i.metadata.namespace == "kube-system":
            continue

        selector = i.metadata.labels["app"]

        #print( i.spec )
        #print( i.metadata )
        print( "%s\t%s\t%s\t%s\t%s" %
                (i.status.pod_ip, i.metadata.namespace, i.metadata.name,
                    i.spec.node_name, selector) )

        data = { "node_name": i.spec.node_name, "selector": selector }
        res.append( data )

    return res

def service_list():
    print( "service_list()" )

    res = []

    v1 = client.CoreV1Api()

    ret = v1.list_service_for_all_namespaces(watch=False)
    for i in ret.items:
        if i.metadata.namespace == "kube-system":
            continue

        ports = []
        selector = ""
        if i.spec.selector != None:
            selector = i.spec.selector["app"]

        for port_list in i.spec.ports:
            data = { "name": port_list.name, "node_port": port_list.node_port,
                    "port": port_list.port, "target_port": port_list.target_port,
                    "protocol": port_list.protocol }
            ports.append( data )

        #print( i.spec )
        #print( i.metadata )
        print( "%s\t%s\t%s\t%s\t%s\t%s" %
                (i.spec.cluster_ip, i.spec.external_i_ps,
                    i.metadata.namespace, i.metadata.name, i.metadata.uid, selector) )
        #print( i.spec.ports )

        data = { "selector": selector, "node_port": ports }
        res.append( data )

    return res

def list_all():
    print( "list_all" )

    _node_list = node_list()
    _deployment_list = deployment_list()
    _pod_list = pod_list()
    _service_list = service_list()

    print( "-----------------------" )
    print( "node_list:", _node_list )
    print( "deployment:", _deployment_list )
    print( "pod list:", _pod_list )
    print( "service list:", _service_list )

    info = []
    for pod in _pod_list:
        data = { "pod": pod }

        for deployment in _deployment_list:
            if pod["selector"] == deployment["name"]:
                data["deployment"] = deployment

        for service in _service_list:
            if pod["selector"] == service["selector"]:
                data["service"] = service

        for node in _node_list:
            if pod["node_name"] == node["node_name"]:
                data["node"] = node

        info.append( data )

    print( "-----------------------" )
    print( info )
    json_print = json.dumps( info, indent = 2 )
    print( json_print )

    return info


# -----------------------------------


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

    external_ips = ["0.0.0.0"] # Worker Node IPs

    core_v1_api = client.CoreV1Api()

    body = client.V1Service(
        api_version = "v1",
        kind = "Service",
        metadata = client.V1ObjectMeta(
            name = DEPLOYMENT_SERVICE_NAME
        ),
        spec = client.V1ServiceSpec(
            #type = "LoadBalancer",
            type = "NodePort",
            #external_i_ps = external_ips,
            selector = { "app": DEPLOYMENT_NAME },
            ports = [
                client.V1ServicePort(
                    name = DEPLOYMENT_PORT_NAME__CONTAINER_WAS,
                    node_port = DEPLOYMENT_PORT_EXPOSE__CONTAINER_WAS,
                    port = DEPLOYMENT_PORT_EXPOSE__CONTAINER_WAS,
                    target_port = DEPLOYMENT_PORT__CONTAINER_WAS
                ),
                client.V1ServicePort(
                    name = DEPLOYMENT_PORT_NAME__CONTAINER_DB,
                    node_port = DEPLOYMENT_PORT_EXPOSE__CONTAINER_DB,
                    port = DEPLOYMENT_PORT_EXPOSE__CONTAINER_DB,
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
    #node_list()
    #pod_list()
    #service_list()
    list_all()

    """
    try:
        ret = create_deployment()
        print( ret )
    except Exception as e:
        #traceback.print_exc()
        #print( "error = ", e )
        #print( "error code = ", e.status )

        if e.status == 409:
            print( "AlreadyExists, 409" )

    try:
        ret = create_service()
        print( ret )
    except Exception as e:
        #traceback.print_exc()
        #print( "error = ", e )
        #print( "error code = ", e.status )

        if e.status == 422:
            print( "Unprocessable Entity, 422" )
    """

