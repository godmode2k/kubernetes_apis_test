# hjkim, 2022.06.17


import traceback
import json
import base64
from kubernetes import client, config

# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()


DEFAULT_NAMESPACE = "default"

#DEPLOYMENT_IMAGE = "127.0.0.1:5000/test_img:1.0"
DEPLOYMENT_IMAGE = "10.0.2.5:5000/test_img_apm:1.0"
DEPLOYMENT_NAME = "test1-img"
DEPLOYMENT_SERVICE_NAME = "test1-img-service"
DEPLOYMENT_INGRESS_NAME = "test1-img-ingress"
DEPLOYMENT_VOLUME_NAME1 = "test1-img-volume1"
DEPLOYMENT_SECRET_NAME1 = "chap-secret1"
DEPLOYMENT_PERSISTENT_VOLUME_NAME1 = "iscsi-pv1"
DEPLOYMENT_PERSISTENT_VOLUME_CLAIM_NAME1 = "iscsi-pvc1"
# By default, the range of the service NodePorts is 30000-32768.
# This range contains 2768 ports, which means that you can create up to 2768 services with NodePorts.
# 30000: 8080 (WAS: Tomcat9)
# 30001: 3306 (MariaDB)
# --service-node-port-range=30000-40000
DEPLOYMENT_PORT_NAME__CONTAINER_WAS = "was-tomcat"
DEPLOYMENT_PORT_NAME__CONTAINER_DB = "db-mariadb"
DEPLOYMENT_PORT_EXPOSE__CONTAINER_WAS = int(30000)
DEPLOYMENT_PORT_EXPOSE__CONTAINER_DB = int(30001)
DEPLOYMENT_PORT__CONTAINER_WAS = int(8080)
DEPLOYMENT_PORT__CONTAINER_DB = int(3306)


def node_list():
    print("Listing nodes with their IPs:")

    res = []

    v1 = client.CoreV1Api()

    ret = v1.list_node(watch=False)
    for i in ret.items:
        if i.metadata.namespace == "kube-system":
            continue

        #ipaddr = i.metadata.annotations["projectcalico.org/IPv4Address"].split("/")[0]
        #ipaddr_internal = i.metadata.annotations["projectcalico.org/IPv4IPIPTunnelAddr"]

        for j in i.metadata.annotations:
            if j == "flannel.alpha.coreos.com/public-ip":
                #print( i.metadata.annotations["flannel.alpha.coreos.com/public-ip"] )
                ipaddr = i.metadata.annotations["flannel.alpha.coreos.com/public-ip"]
                ipaddr_internal = ipaddr
                break


        #print( i.spec )
        #print( i.metadata )
        print( "%s\t%s\t%s\t%s" % (i.metadata.name, ipaddr, ipaddr_internal, i.metadata.uid) )

        data = { "node_name": i.metadata.name, "ip": ipaddr }
        res.append( data )

    return res

def deployment_list():
    print("Listing deployments with their IPs:")

    res = []

    v1 = client.AppsV1Api()

    ret = v1.list_deployment_for_all_namespaces(watch=False)
    for i in ret.items:
        if i.metadata.namespace == "kube-system":
            continue

        #print( i.metadata )
        print("%s\t%s" % (i.metadata.namespace, i.metadata.name))

        data = { "name": i.metadata.name }
        res.append( data )

    return res

def pod_list():
    print("Listing pods with their IPs:")

    res = []

    v1 = client.CoreV1Api()

    ret = v1.list_pod_for_all_namespaces(watch=False)
    for i in ret.items:
        if i.metadata.namespace == "kube-system":
            continue

        #selector = i.metadata.labels["app"]
        if "app" in i.metadata.labels.keys():
            selector = i.metadata.labels["app"]
        else:
            continue

        status = ""
        if i.metadata.deletion_timestamp != None and i.status.phase in ('Pending', 'Running'):
            status = 'Terminating'
        else:
            status = i.status.phase


        #print( i.spec )
        #print( i.metadata )
        print("%s\t%s\t%s\t%s\t%s\t%s" %
                (i.status.pod_ip, i.metadata.namespace, i.metadata.name,
                    i.spec.node_name, selector,
                    i.spec.containers[0].image))

        data = { "node_name": i.spec.node_name, "selector": selector,
                "image": i.spec.containers[0].image, "status": status }
        res.append( data )

    return res

def service_list():
    print("Listing services with their IPs:")

    res = []

    v1 = client.CoreV1Api()

    ret = v1.list_service_for_all_namespaces(watch=False)
    for i in ret.items:
        if i.metadata.namespace == "kube-system":
            continue

        ports = []
        selector = ""
        if i.spec.selector != None:
            #selector = i.spec.selector["app"]
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
        print("%s\t%s\t%s\t%s\t%s\t%s" %
                (i.spec.cluster_ip, i.spec.external_i_ps,
                    i.metadata.namespace, i.metadata.name, i.metadata.uid, selector))
        #print( i.spec.ports )

        data = { "name": i.metadata.name, "selector": selector, "ports": ports }
        res.append( data )

    return res

def ingress_list():
    #print("ingress_list()")

    res = []

    networking_v1_api = client.NetworkingV1Api()

    ret = networking_v1_api.list_ingress_for_all_namespaces(watch=False)
    for i in ret.items:
        if i.metadata.namespace == "kube-system":
            continue

        #print( i.spec )
        #print( "---" )
        #print( i.metadata )

        service_name = ""
        paths = []
        for rule in i.spec.rules:
            for path in rule.http.paths:
                #print( "-->", path.backend.service.name )
                service_name = path.backend.service.name
                path_endpoint = path.path
                paths.append( path_endpoint )

        data = { "ingress_name": i.metadata.name, "paths": paths, "service_name": service_name }
        res.append( data )

    return res


def list_all():
    print("Listing all with their IPs:")

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
    #json_print = json.dumps( info, indent = 2 )
    #print( json_print )

    return info




def create_deployment(new_deployment_name, new_volume_name, pvc_name = None, new_device_path = None, mount_path = None):
    print( "create_deployment()" )

    apps_v1_api = client.AppsV1Api()


    volume_mounts = []
    volumes = []
    #if (pvc_name != None and mount_path != None):
    if ( pvc_name != None ):
        if ( mount_path != None ):
            volume_mounts = [
                client.V1VolumeMount(
                    #name = DEPLOYMENT_VOLUME_NAME1,
                    name = new_volume_name,

                    #mount_path = "/path/to/container"
                    mount_path = mount_path
                )
            ]

        volumes = [
            client.V1Volume(
                #name = DEPLOYMENT_VOLUME_NAME1,
                name = new_volume_name,

                #persistent_volume_claim =
                #    client.V1PersistentVolumeClaimVolumeSource(
                #        #claim_name = DEPLOYMENT_PERSISTENT_VOLUME_CLAIM_NAME1
                #        claim_name = pvc_name
                #    )

                nfs = client.V1NFSVolumeSource(
                    path = "/nfs_home/k8s_storage/id1",
                    server = "10.0.2.16"
                )
            )
        ]

    #command = ["/bin/sh", "-c", "..."]
    #lifecycle = client.V1Lifecycle(
    #    post_start = client.V1LifecycleHandler(
    #        _exec = client.V1ExecAction(
    #            command = command
    #        )
    #    )
    #)



    container = client.V1Container(
        name = new_deployment_name,
        image = DEPLOYMENT_IMAGE,
        ports = [
            client.V1ContainerPort( container_port = DEPLOYMENT_PORT_EXPOSE__CONTAINER_WAS ),
            client.V1ContainerPort( container_port = DEPLOYMENT_PORT_EXPOSE__CONTAINER_DB )
        ],
        volume_mounts = volume_mounts
    )

    if ( new_volume_name != None and new_device_path != None ):
        container.volume_devices = [
            client.V1VolumeDevice(
                name = new_volume_name,
                device_path = new_device_path
            )
        ]

    template = client.V1PodTemplateSpec(
        metadata = client.V1ObjectMeta( labels = { "app" : new_deployment_name} ),
        spec = client.V1PodSpec(
            containers = [container],
            volumes = volumes
        )
    )

    spec = client.V1DeploymentSpec(
        replicas = 1,
        selector = client.V1LabelSelector(
            match_labels = { "app" : new_deployment_name }
        ),
        template = template
    )

    deployment = client.V1Deployment(
        api_version = "apps/v1",
        kind = "Deployment",
        metadata = client.V1ObjectMeta( name = new_deployment_name ),
        spec = spec
    )

    return apps_v1_api.create_namespaced_deployment(
        namespace = DEFAULT_NAMESPACE,
        body = deployment
    )

def create_service(service_name, ingress_mode = False):
    print( "create_service()" )

    core_v1_api = client.CoreV1Api()

    if ingress_mode == True:
        service_type = "ClusterIP"
    else:
        service_type = "NodePort"

    body = client.V1Service(
        api_version = "v1",
        kind = "Service",
        metadata = client.V1ObjectMeta(
            name = service_name
        ),
        spec = client.V1ServiceSpec(
            type = service_type,
            #type = "LoadBalancer",
            #type = "NodePort",
            #external_i_ps = [""],
            selector = { "app": DEPLOYMENT_NAME },
            ports = [
                client.V1ServicePort(
                    name = DEPLOYMENT_PORT_NAME__CONTAINER_WAS,
                    #node_port = DEPLOYMENT_PORT_EXPOSE__CONTAINER_WAS,
                    port = DEPLOYMENT_PORT__CONTAINER_WAS,
                    target_port = DEPLOYMENT_PORT__CONTAINER_WAS
                ),
                client.V1ServicePort(
                    name = DEPLOYMENT_PORT_NAME__CONTAINER_DB,
                    #node_port = DEPLOYMENT_PORT_EXPOSE__CONTAINER_DB,
                    port = DEPLOYMENT_PORT__CONTAINER_DB,
                    target_port = DEPLOYMENT_PORT__CONTAINER_DB
                )
            ]
        )
    )

    return core_v1_api.create_namespaced_service(
        namespace = DEFAULT_NAMESPACE,
        body = body
    )

def create_ingress(ingress_name, host, service_name, service_ports, namespace = DEFAULT_NAMESPACE):
    print( "create_ingress()" )

    networking_v1_api = client.NetworkingV1Api()

    paths = []
    for port in service_ports:
        #_name = port["name"]
        _port = port["port"]

        endpoint = service_name + "/" + str(_port)

        path = client.V1HTTPIngressPath(
            path = endpoint, # "/test_path1"
            path_type = "Exact",
            backend = client.V1IngressBackend(
                service = client.V1IngressServiceBackend(
                    port = client.V1ServiceBackendPort(number = _port), # 80
                    name = service_name # "test_path_svc"
                )
            )
        )
        paths.append( path )

    body = client.V1Ingress(
        api_version = "networking.k8s.io/v1",
        kind = "Ingress",
        metadata = client.V1ObjectMeta(
            name = ingress_name,
            annotations = {
                "nginx.ingress.kubernetes.io/rewrite-target": "/"
            }
        ),
        spec = client.V1IngressSpec(
            rules = [
                client.V1IngressRule(
                    #host = "example.com",
                    http = client.V1HTTPIngressRuleValue(
                        #paths = [ client.V1HTTPIngressPath(
                        #    path = "/",
                        #    path_type = "Exact",
                        #    backend = client.V1IngressBackend(
                        #        service = client.V1IngressServiceBackend(
                        #            port = client.V1ServiceBackendPort(
                        #                number = 0
                        #            ),
                        #            name = DEPLOYMENT_SERVICE_NAME
                        #        )
                        #    )
                        #) 
                        #]
                        paths = paths
                    )
                )
            ]
        )
    )

    # Creation of the Deployment in specified namespace
    # (Can replace "default" with a namespace you may have created)
    networking_v1_api.create_namespaced_ingress(
        namespace = namespace, # "default",
        body = body
    )


def delete_container(deployment_name, service_name, ingress_name):
    print( "delete_container()" )

    apps_v1_api = client.AppsV1Api()
    core_v1_api = client.CoreV1Api()
    networking_v1_api = client.NetworkingV1Api()

    delete_options = client.V1DeleteOptions(
        propagation_policy = "Foreground", grace_period_seconds = 5
    )

    # delete deployment
    ret_deployment = apps_v1_api.delete_namespaced_deployment(
        namespace = DEFAULT_NAMESPACE,
        name = deployment_name,
        body = delete_options
    )

    # delete service
    ret_service = core_v1_api.delete_namespaced_service(
        namespace = DEFAULT_NAMESPACE,
        name = service_name,
        body = delete_options
    )

    ret_ingress = networking_v1_api.delete_namespaced_ingress(
        namespace = DEFAULT_NAMESPACE,
        name = ingress_name
    )

    return ret_deployment, ret_service, ret_ingress

def create_volume(_host, _username, _password, _iqn, _lun,
        new_secret_name, new_pv_name, storage_class_name, capacity_storage_size, new_volume_mode):
    print( "create_volume()" )

    #apps_v1_api = client.AppsV1Api()
    core_v1_api = client.CoreV1Api()


    # $ sudo kubectl get chap-secret -o wide
    # $ sudo kubectl get pv (or persistentvolumes) -o wide
    # $ sudo kubectl get pvc -o wide
    # $ sudo kubectl get storageclass -o wide
    #
    # $ sudo kubectl delete chap-secret
    # $ sudo kubectl delete pvc iscsi-pvc1
    # $ sudo kubectl delete pv (or persistentvolumes) iscsi-pv1
    # $ sudo kubectl delete storageclass storage-test1
    

    ret = None

    # account for iSCSI
    HOST = _host # "127.0.0.1:3260" # portal
    USERNAME = _username # "iscsi_test"
    PASSWORD = _password # "iscsi_test"
    USERNAME = str( base64.b64encode(USERNAME.encode("utf-8")), "utf-8" )
    PASSWORD = str( base64.b64encode(PASSWORD.encode("utf-8")), "utf-8" )
    #IQN = "iqn.2022-07.test.com:lun1"
    #LUN = 1
    IQN = _iqn # "iqn.2022-07.test2.com:lun2"
    LUN = _lun # 2


    #"""
    body = client.V1Secret(
        api_version = "v1",
        kind = "Secret",
        metadata = client.V1ObjectMeta(
            #name = "chap-secret"
            name = new_secret_name
        ),
        type = "kubernetes.io/iscsi-chap",
        data = {
            "node.session.auth.username": USERNAME,
            "node.session.auth.password": PASSWORD
        }
    )

    ret = core_v1_api.create_namespaced_secret(
        namespace = DEFAULT_NAMESPACE,
        body = body
    )
    #print( "iSCSI: ", ret )
    #"""



    body = client.V1PersistentVolume(
        api_version = "v1",
        kind = "PersistentVolume",
        metadata = client.V1ObjectMeta(
            #name = DEPLOYMENT_PERSISTENT_VOLUME_NAME1
            name = new_pv_name
        ),
        spec = client.V1PersistentVolumeSpec(
            #"""
            #selector = { "app": DEPLOYMENT_NAME },
            #volumeMode = "Filesystem",
            #access_modes = [ "ReadWriteOnce" ],
            #capacity = { "storage": "1Gi" },
            #
            ## Local, NAS, ...
            #local = client.V1LocalVolumeSource(
            #    path = "/path/to/host"
            #    # SEE: target (container) mount path
            #    # "creates deployment method"
            #),
            ## FIXME:
            ##node_affinity = client.V1VolumeNodeAffinity(),
            #"""

            access_modes = [ "ReadWriteOnce" ],
            #volume_mode = "Filesystem",
            #volume_mode = "Block",
            volume_mode = new_volume_mode,
            #persistent_volume_reclaim_policy = "Retain",
            #persistent_volume_reclaim_policy = "Delete",
            persistent_volume_reclaim_policy = "Recycle",
            # for only (ignore size)
            #capacity = { "storage": "10Gi" },
            capacity = { "storage": capacity_storage_size },


            #"""
            # iSCSI
            iscsi = client.V1ISCSIPersistentVolumeSource(
                # Target Host IP:PORT
                #target_port = "127.0.0.1:3260", # portal
                # IQN: "iqn.YYYY-MM.name.com (reverse: com.name....):tag"
                #iqn = "iqn.2022-07.test.com:lun1",
                #lun = 1,
                target_portal = HOST,
                iqn = IQN,
                lun = LUN,
                fs_type = "ext4",
                read_only = False,
                chap_auth_session = True,
                secret_ref = client.V1SecretReference(
                    #name = "chap-secret"
                    name = new_secret_name
                )
            ),
            #"""

            #mount_options = [],
            storage_class_name = storage_class_name,
        )
    )

    ret = core_v1_api.create_persistent_volume(
        body = body
    )
    #print( "iSCSI: ", ret )



    """
    # creates pvc -> creates deployment
    body = client.V1PersistentVolumeClaim(
        api_version = "v1",
        kind = "PersistentVolumeClaim",
        metadata = client.V1ObjectMeta(
            name = DEPLOYMENT_PERSISTENT_VOLUME_CLAIM_NAME1
        ),
        spec = client.V1PersistentVolumeClaimSpec(
            selector = { "app": DEPLOYMENT_NAME },
            access_modes = [ "ReadWriteOnce" ],
            #storage_class_name = "",
            #persistent_volume_reclaim_policy = "delete",
            resources = client.V1ResourceRequirements(
                # request: 0.5 vCore, 1GiB RAM, 500MiB Storage (max: 1 vCore, 2GiB RAM, 1GiB Storage)
                #limits = { "memory", "2Gi", "cpu": "1000m", "storage": "1Gi" },
                #requests = { "memory", "1Gi", "cpu": "500m", "storage": "500Mi" }

                # prevent overcommitted (cpu)
                #limits = { "memory", "2Gi", "cpu": "100m", "storage": "1Gi" },
                #requests = { "memory", "1Gi", "cpu": "100m", "storage": "500Mi" }

                requests = { "storage": "100Mi" }
            )
        )
    )

    ret = core_v1_api.create_namespaced_persistent_volume_claim(
        namespace = DEFAULT_NAMESPACE,
        body = body
    )
    #print( "iSCSI: ", ret )
    """

def create_pvc(new_pvc_name, storage_class_name, storage_size, new_volume_mode):
#def create_pvc(new_deployment_name, new_pvc_name, storage_size):
    core_v1_api = client.CoreV1Api()

    body = client.V1PersistentVolumeClaim(
        api_version = "v1",
        kind = "PersistentVolumeClaim",
        metadata = client.V1ObjectMeta(
            name = new_pvc_name
        ),
        spec = client.V1PersistentVolumeClaimSpec(
            #selector = { "app": new_deployment_name },
            access_modes = [ "ReadWriteOnce" ],
            #volume_mode = "Filesystem",
            #volume_mode = "Block",
            volume_mode = new_volume_mode,
            #persistent_volume_reclaim_policy = "delete",
            resources = client.V1ResourceRequirements(
                # request: 0.5 vCore, 1GiB RAM, 500MiB Storage (max: 1 vCore, 2GiB RAM, 1GiB Storage)
                #limits = { "memory", "2Gi", "cpu": "1000m", "storage": "1Gi" },
                #requests = { "memory", "1Gi", "cpu": "500m", "storage": "500Mi" }

                # prevent overcommitted (cpu)
                #limits = { "memory", "2Gi", "cpu": "100m", "storage": "1Gi" },
                #requests = { "memory", "1Gi", "cpu": "100m", "storage": "500Mi" }

                #requests = { "storage": "100Mi" }
                #limits = { "storage": storage_size },
                requests = { "storage": storage_size }
            ),
            storage_class_name = storage_class_name
        )
    )

    ret = core_v1_api.create_namespaced_persistent_volume_claim(
        namespace = DEFAULT_NAMESPACE,
        body = body
    )
    #print( "iSCSI: ", ret )

def create_storage_class(new_storage_class_name):
    #core_v1_api = client.CoreV1Api()
    storage_v1_api = client.StorageV1Api()

    # https://kubernetes.io/docs/concepts/storage/storage-classes/
    body = client.V1StorageClass(
        api_version = "storage.k8s.io/v1",
        kind = "StorageClass",
        metadata = client.V1ObjectMeta(
            name = new_storage_class_name
        ),
        provisioner = "kubernetes.io/no-provisioner",
        #allow_volume_expansion = True,
        parameters = {
            #"type": "",
            #"iopsPerGB": "10",
            # ...
            "fsType": "ext4"
        }
    )

    ret = storage_v1_api.create_storage_class(
        body = body
    )
    #print( "ret: ", ret )



"""
def add_volume(new_name, new_deployment_name, pvc_name):
    core_v1_api = client.CoreV1Api()


    container = client.V1Container(
        name = new_deployment_name,
        image = DEPLOYMENT_IMAGE,
        ports = [
            client.V1ContainerPort( container_port = DEPLOYMENT_PORT_EXPOSE__CONTAINER_WAS ),
            client.V1ContainerPort( container_port = DEPLOYMENT_PORT_EXPOSE__CONTAINER_DB )
        ],
        volume_mounts = volume_mounts
    )

    body = client.V1Pod(
        api_version = "v1",
        kind = "Pod",
        metadata = client.V1ObjectMeta(
            name = new_name
        ),
        spec = client.V1PodSpec(
            containers = [container],

            containers = [
                name = "",
                image = "",
                command = [ "/bin/sh", "-c" ],
                args = [ "tail -f /dev/null" ]
                volume_devices = {
                    name = "",
                    device_path = ""
                }
            ],
            volumes = 
                name = "..."
                persistent_volume_claim = ( claim_name = "" )
        )
    )
"""



if __name__ == "__main__":
    #node_list()
    #pod_list()
    #service_list()
    #list_all()


    """
    # TEST

    try:
        new_storage_class_name = "storage-test1"

        ret = create_storage_class( new_storage_class_name )
        #print( ret )
    except Exception as e:
        traceback.print_exc()
        print( "error = ", e )
        #print( "error code = ", e.status )


    try:
        host = "127.0.0.1:3260"
        username = "iscsi_test"
        password = "iscsi_test"

        #iqn = "iqn.2022-07.test.com:lun1"
        #lun = 1
        #new_secret_name = "chap-secret1"
        #new_pv_name = "iscsi-pv1"

        iqn = "iqn.2022-07.test2.com:lun2"
        lun = 1
        new_secret_name = "chap-secret2"
        new_pv_name = "iscsi-pv2"

        capacity_storage_size = "5Gi" # for label (ignore size)
        new_volume_mode = "Filesystem"
        #new_volume_mode = "Block"

        storage_class_name = "storage-test1"

        ret = create_volume(
                host, username, password, iqn, lun,
                new_secret_name, new_pv_name, storage_class_name, capacity_storage_size, new_volume_mode )
        #print( ret )
    except Exception as e:
        traceback.print_exc()
        print( "error = ", e )
        #print( "error code = ", e.status )
    """


    """
    try:
        #pvc_name = "iscsi-pvc1"
        #storage_size = "100Mi"

        new_pvc_name = "iscsi-pvc2"
        storage_size = "2Gi"
        new_volume_mode = "Filesystem"
        #new_volume_mode = "Block"

        storage_class_name = "storage-test1"

        #new_deployment_name = "test2-img"

        ret = create_pvc( new_pvc_name, storage_class_name, storage_size, new_volume_mode )
        #ret = create_pvc( new_deployment_name, new_pvc_name, storage_size )
        #print( ret )
    except Exception as e:
        traceback.print_exc()
        print( "error = ", e )
        #print( "error code = ", e.status )

        #if e.status == 409:
        #    print( "AlreadyExists, 409" )
    """


    """
    try:
        #new_deployment_name = "test1-img"
        #new_volume_name = "test1-volume1"
        #pvc_name = "iscsi-pvc1"

        new_deployment_name = "test2-img"
        new_volume_name = "test2-volume1"
        pvc_name = "iscsi-pvc2"

        # FIXME: restrict host volumes
        # lsblk: show all of host volumes (/dev/sd*)
        # df -hT: overlay / (mounted): host volume

        # FIXME: fdisk -l
        # Raw Block Volume
        #new_device_path = "/dev/xvda"
        #mount_path = None

        # Filesystem (mounted)
        #new_device_path = None
        #mount_path = None
        #mount_path = "/test_mnt"

        ret = create_deployment( new_deployment_name, new_volume_name )
        #ret = create_deployment(
        #        new_deployment_name, new_volume_name, pvc_name,
        #        new_device_path, mount_path )
        #print( ret )
    except Exception as e:
        traceback.print_exc()
        print( "error = ", e )
        #print( "error code = ", e.status )

        if e.status == 409:
            print( "AlreadyExists, 409" )
    """

    """
    try:
        new_deployment_name = "test2-img"

        #ret = add_volume()
        #print( ret )
    except Exception as e:
        traceback.print_exc()
        print( "error = ", e )
        #print( "error code = ", e.status )
    """




    # NFS
    try:
        #new_deployment_name = "test1-img"
        #new_volume_name = "test1-volume1"
        #pvc_name = "iscsi-pvc1"

        new_deployment_name = "test2-img"
        new_volume_name = "test2-volume1"
        pvc_name = "iscsi-pvc2"

        # FIXME: restrict host volumes
        # lsblk: show all of host volumes (/dev/sd*)
        # df -hT: overlay / (mounted): host volume

        # FIXME: fdisk -l
        # Raw Block Volume
        #new_device_path = "/dev/xvda"
        #mount_path = None

        # Filesystem (mounted)
        #new_device_path = None
        #mount_path = None
        #mount_path = "/test_mnt"

        #ret = create_deployment( new_deployment_name, new_volume_name )
        #ret = create_deployment(
        #        new_deployment_name, new_volume_name, pvc_name,
        #        new_device_path, mount_path )


        new_deployment_name = "test2-img"
        new_volume_name = "test2-volume1"
        pvc_name = ""
        new_device_path = None
        mount_path = "/test_mnt"
        ret = create_deployment(
                new_deployment_name, new_volume_name, pvc_name,
                new_device_path, mount_path )
        #print( ret )


        ingress_name = new_deployment_name + "-ingress"
        host = ""
        service_name = new_deployment_name + "-svc"

        create_service( service_name, True )

        container_target_port = [DEPLOYMENT_PORT__CONTAINER_WAS, DEPLOYMENT_PORT__CONTAINER_DB]
        container_target_port_name = [DEPLOYMENT_PORT_NAME__CONTAINER_WAS, DEPLOYMENT_PORT_NAME__CONTAINER_DB]
 
        service_ports = []
        service_ports.append( {"name": container_target_port_name[0],
                                "port": container_target_port[0], "target_port": container_target_port[0]} )
        service_ports.append( {"name": container_target_port_name[1],
                                "port": container_target_port[1], "target_port": container_target_port[1]} )

        create_ingress( ingress_name, host, service_name, service_ports, namespace = DEFAULT_NAMESPACE )

    except Exception as e:
        traceback.print_exc()
        print( "error = ", e )
        #print( "error code = ", e.status )

        if e.status == 409:
            print( "AlreadyExists, 409" )










    """
    try:
        ret = create_service()
        #print( ret )
    except Exception as e:
        traceback.print_exc()
        print( "error = ", e )
        #print( "error code = ", e.status )

        if e.status == 422:
            print( "Unprocessable Entity, 422" )
    """


    #try:
    #    deployment_name = "aaaaa"
    #    service_name = "aaaaa-service"
    #    ret = delete_container( deployment_name, service_name )
    #    #print( ret )
    #except Exception as e:
    #    traceback.print_exc()
    #    print( "error = ", e )
    #    #print( "error code = ", e.status )





# --------------------------------------




