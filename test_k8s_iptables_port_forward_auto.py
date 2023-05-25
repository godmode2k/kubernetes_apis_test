#
# Kubernetes APIs test
# hjkim, 2022.05.25
#
# Reference:
# - https://github.com/kubernetes-client/python
# - https://kubernetes.io/docs/reference/kubernetes-api/
# - https://kubernetes.io/docs/reference/kubectl/cheatsheet/
#



import requests
import json
import datetime
import traceback
import sys
import time
import os
import math
import iptc
import pymysql
from kubernetes import client, config



# ---------------------------------------------------------



# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()


DEFAULT_NAMESPACE = "default"

# kubectl server
# DO NOT CHANGE KUBECTL_SERVER_IP
KUBECTL_SERVER_IP = ""


# ---------------------------------------------------------



class test_kubernetes_apis():
    def __init__(self):
        pass

    def __del__(self):
        pass

    def node_list(self):
        res = []

        v1 = client.CoreV1Api()

        ret = v1.list_node(watch=False)
        for i in ret.items:
            if i.metadata.namespace == "kube-system":
                continue

            ipaddr = i.metadata.annotations["alpha.kubernetes.io/provided-node-ip"]

            #ipaddr = i.metadata.annotations["projectcalico.org/IPv4Address"].split("/")[0]
            #ipaddr_internal = i.metadata.annotations["projectcalico.org/IPv4IPIPTunnelAddr"]

            #print( i.spec )
            #print( i.metadata )

            data = { "node_name": i.metadata.name, "ip": ipaddr }
            res.append( data )

        return res

    def deployment_list(self):
        res = []

        v1 = client.AppsV1Api()

        ret = v1.list_deployment_for_all_namespaces(watch=False)
        for i in ret.items:
            if i.metadata.namespace == "kube-system":
                continue

            #print( i.metadata )

            data = { "name": i.metadata.name }
            res.append( data )

        return res

    def pod_list(self):
        res = []

        v1 = client.CoreV1Api()

        ret = v1.list_pod_for_all_namespaces(watch=False)
        for i in ret.items:
            if i.metadata.namespace == "kube-system":
                continue

            selector = ""
            if "app" in i.metadata.labels.keys():
                selector = i.metadata.labels["app"]
            else:
                continue

            if i.metadata.deletion_timestamp != None and i.status.phase in ('Pending', 'Running'):
                status = "Terminating"
            else:
                status = i.status.phase

            #print( i.spec )
            #print( i.metadata )

            data = { "node_name": i.spec.node_name, "selector": selector, "image": i.spec.containers[0].image, "status": status }
            res.append( data )

        return res

    def service_list(self):
        res = []

        v1 = client.CoreV1Api()

        ret = v1.list_service_for_all_namespaces(watch=False)
        for i in ret.items:
            if i.metadata.namespace == "kube-system":
                continue

            ports = []
            selector = ""
            if i.spec.selector != None:
                if "app" in i.spec.selector.keys():
                    selector = i.spec.selector["app"]
                else:
                    continue


            for port_list in i.spec.ports:
                data = { "name": port_list.name, "node_port": port_list.node_port,
                        "port": port_list.port, "target_port": port_list.target_port,
                        "protocol": port_list.protocol }
                ports.append( data )

            #print( i.spec )
            #print( i.metadata )

            data = { "name": i.metadata.name, "selector": selector, "ports": ports }
            res.append( data )

        return res


    def create_open_port(self, src_ip, dst_ip, dport, init = False):
        print( "create_open_port()" )

        if init == True:
            '''
            chain = iptc.Chain( iptc.Table(iptc.Table.FILTER), "FORWARD" )
            rule = iptc.Rule()
            rule.target = rule.create_target( "ACCEPT" )

            chain.insert_rule( rule )
            '''

        chain = iptc.Chain( iptc.Table(iptc.Table.NAT), "PREROUTING" )
        rule = iptc.Rule()
        rule.protocol = "tcp"
        rule.match = rule.create_match( "tcp" )
        rule.match.dport = dport
        rule.target = rule.create_target( "DNAT" )
        if dport.find("-") > 0:
            rule.target.to_destination = dst_ip + ":" + dport.replace(":", "-")
        else:
            rule.target.to_destination = dst_ip + ":" + dport
        chain.insert_rule( rule )

        chain = iptc.Chain( iptc.Table(iptc.Table.NAT), "POSTROUTING" )
        rule = iptc.Rule()
        rule.protocol = "tcp"
        rule.match = rule.create_match( "tcp" )
        rule.match.dport = dport
        rule.target = rule.create_target( "SNAT" )
        rule.target.to_source = src_ip
        chain.insert_rule( rule )

        chain = iptc.Chain( iptc.Table(iptc.Table.FILTER), "INPUT" )
        rule = iptc.Rule()
        rule.protocol = "tcp"
        rule.match = rule.create_match( "tcp" )
        rule.match.dport = dport
        rule.target = rule.create_target( "ACCEPT" )
        chain.insert_rule( rule )

        chain = iptc.Chain( iptc.Table(iptc.Table.FILTER), "FORWARD" )
        rule = iptc.Rule()
        rule.protocol = "tcp"
        match = rule.create_match( "tcp" )
        match.dport = dport
        match = rule.create_match( "state" )
        match.state = "NEW,RELATED,ESTABLISHED"
        rule.target = rule.create_target( "ACCEPT" )
        chain.insert_rule( rule )

    def delete_port(self, dport):
        print( "delete_port()" )

        chain = iptc.Chain( iptc.Table(iptc.Table.NAT), "PREROUTING" )
        for rule in chain.rules:
            for match in rule.matches:
                if dport == match.dport:
                    chain.delete_rule( rule )

        chain = iptc.Chain( iptc.Table(iptc.Table.NAT), "POSTROUTING" )
        for rule in chain.rules:
            for match in rule.matches:
                if dport == match.dport:
                    chain.delete_rule( rule )

        chain = iptc.Chain( iptc.Table(iptc.Table.FILTER), "INPUT" )
        for rule in chain.rules:
            for match in rule.matches:
                if dport == match.dport:
                    chain.delete_rule( rule )

        chain = iptc.Chain( iptc.Table(iptc.Table.FILTER), "FORWARD" )
        for rule in chain.rules:
            for match in rule.matches:
                if dport == match.dport:
                    chain.delete_rule( rule )

    def portforward_add(self, deployment_name, deployment_service_name):
        print( "portforward_add()" )

        _node_list = self.node_list()
        _deployment_list = self.deployment_list()
        _pod_list = self.pod_list()
        _service_list = self.service_list()


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

        for pod in info:
            port_forward_deployment_name = None
            port_forward_service = None
            port_forward_node_ip = None

            if "deployment" in pod and "service" in pod and "node" in pod:
                pass
            else:
                continue

            port_forward_deployment_name = pod["deployment"]["name"]
            port_forward_service_name = pod["service"]["name"]
            port_forward_service_ports = pod["service"]["ports"]
            port_forward_node_ip = pod["node"]["ip"]

            if port_forward_deployment_name != deployment_name:
                continue
            if port_forward_service_name != deployment_service_name:
                continue

            src_ip = KUBECTL_SERVER_IP

            if ( port_forward_deployment_name != None and
                port_forward_service_name != None and
                port_forward_service_ports != None and
                port_forward_node_ip != None ):

                dst_ip = port_forward_node_ip
                dports = []

                for service_port in port_forward_service_ports:
                    dports.append( service_port["node_port"] )

                for dport in dports:
                    self.create_open_port( src_ip, dst_ip, str(dport) )

                break

    def portforward_del(self, deployment_name, deployment_service_name, container_user_id):
        print( "portforward_del()" )

        _node_list = self.node_list()
        _deployment_list = self.deployment_list()
        _pod_list = self.pod_list()
        _service_list = self.service_list()


        found_user = False

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

        for service in _service_list:
            found_service = False
            service_data = { "pod": {}, "deployment": {"name":""}, "node": {"ip":""} }

            for pod in _pod_list:
                if len(service["selector"]) > 0 and service["selector"] == pod["selector"]:
                    found_service = True
                    break

            if found_service != True:
                if service["name"] == "kubernetes":
                    continue

                if container_user_id == "admin-":
                    pass
                else:
                    if service["name"].find(container_user_id) < 0:
                        continue

                service_data["service"] = service
                info.append( service_data )


        for pod in info:
            port_forward_deployment_name = None
            port_forward_service = None
            port_forward_node_ip = None

            if "deployment" in pod and "service" in pod and "node" in pod:
                pass
            else:
                continue

            port_forward_deployment_name = pod["deployment"]["name"]
            port_forward_service_name = pod["service"]["name"]
            port_forward_service_ports = pod["service"]["ports"]
            port_forward_node_ip = pod["node"]["ip"]


            if ( port_forward_deployment_name != None and
                port_forward_service_name != None ):

                if ( deployment_name == None and
                    deployment_service_name == None ):
                    continue

                if ( len(deployment_name) <= 0 and
                    len(deployment_service_name) <= 0 ):
                    continue

                if len(deployment_name) > 0:
                    if port_forward_deployment_name != deployment_name:
                        continue

                if len(deployment_service_name) > 0:
                    if port_forward_service_name != deployment_service_name:
                        continue
            else:
                continue


            src_ip = KUBECTL_SERVER_IP


            if ( port_forward_deployment_name != None and
                port_forward_service_name != None and
                port_forward_service_ports != None and
                port_forward_node_ip != None ):
                if container_user_id == "admin-":
                    pass
                else:
                    if len(deployment_name) > 0:
                        if port_forward_deployment_name.find(container_user_id) < 0:
                            break
                    if len(deployment_service_name) > 0:
                        if port_forward_service_name.find(container_user_id) < 0:
                            break
                found_user = True


                dst_ip = port_forward_node_ip
                dports = []

                for service_port in port_forward_service_ports:
                    dports.append( service_port["node_port"] )

                for dport in dports:
                    self.delete_port( str(dport) )

                break

        return found_user

    def portforward_all(self):
        print( "portforward_all()" )

        _node_list = self.node_list()
        _deployment_list = self.deployment_list()
        _pod_list = self.pod_list()
        _service_list = self.service_list()


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

        for pod in info:
            port_forward_deployment_name = None
            port_forward_deployment_image = None
            port_forward_service = None
            port_forward_node_ip = None

            if "deployment" in pod and "service" in pod and "node" in pod:
                pass
            else:
                continue

            port_forward_deployment_name = pod["deployment"]["name"]
            port_forward_deployment_image = pod["pod"]["image"]
            port_forward_service_name = pod["service"]["name"]
            port_forward_service_ports = pod["service"]["ports"]
            port_forward_node_ip = pod["node"]["ip"]

            if port_forward_deployment_name == "":
                print( "port_forward_deployment_name == NULL" )
                continue
            if not "gnjab60b.kr.private-ncr.ntruss.com" in port_forward_deployment_image:
                print( "gnjab60b.kr.private-ncr.ntruss.com not found" )
                print( " -> ", port_forward_deployment_image )
                continue

            src_ip = KUBECTL_SERVER_IP

            if ( port_forward_deployment_name != None and
                port_forward_service_name != None and
                port_forward_service_ports != None and
                port_forward_node_ip != None ):

                dst_ip = port_forward_node_ip
                dports = []

                for service_port in port_forward_service_ports:
                    dports.append( service_port["node_port"] )

                for dport in dports:
                    self.create_open_port( src_ip, dst_ip, str(dport) )


if __name__ == "__main__":
    try:
        if KUBECTL_SERVER_IP == "":
            raise ValueError( "Set SERVER IP" )

        obj = test_kubernetes_apis()
        obj.portforward_all()
    except Exception as e:
        traceback.print_exc()



