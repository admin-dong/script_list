
#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@FileName    :DataFromKubernetes.py
@Describe    :
@DateTime    :2021/04/14 16:55:26
@Author      :yangyang
'''
from Excute import Excute
import json,argparse,sys

defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)

class K8SData(object):
    def __init__(self, rootURl, CAPath):
        self.excutor = Excute(CAPath)
        self.rootURl = rootURl

    def getNamespace(self):
        """
        Get All Namespaces Informations
        """
        url = self.rootURl + "/api/v1/namespaces"
        response = self.excutor.excute(url)
        responseInstance = json.loads(response)
        namespaceList = []
        items = responseInstance.get('items')
        if not items:
            return namespaceList
        services = []
        for item in items:
            namespace = {}
            namespaceMsg = item.get('metadata')
            if not namespaceMsg:
                continue
            name = namespaceMsg.get('name')
            if name:
                namespace['name'] = name
                requestsCpu, requestsMemory, limitsCpu, limitsMemory = self.__getNamespaceDesc(name)
                if requestsCpu:
                    namespace['requestsCpu'] = requestsCpu
                if requestsMemory:
                    namespace['requestsMemory'] = requestsMemory
                if limitsCpu:
                    namespace['limitsCpu'] = limitsCpu
                if limitsMemory:
                    namespace['limitsMemory'] = limitsMemory

            try:
                labels = namespaceMsg.get('labels')
            except:
                labels = None
            if not labels:
                namespaceList.append(namespace)
                continue

            region = labels.get('region')
            env = labels.get('env')
            if region:
                namespace['region'] = region
            if env:
                namespace['env'] = env
                namespace['cluster_name'] = env
                namespace['overdue'] = "true"
            namespaceList.append(namespace)
            serviceList = self.__getServices(name, env)
            if serviceList:
                services += serviceList    
        
        return namespaceList, services

    
    def __getNamespaceDesc(self, name):
        url = self.rootURl+ "/api/v1/namespaces/" + name +'/resourcequotas'
        response = self.excutor.excute(url)
        responseInstance = json.loads(response)
        requestsCpu = requestsMemory = limitsCpu =limitsMemory = None
        items = responseInstance.get('items')
        if not items:
            return requestsCpu, requestsMemory, limitsCpu, limitsMemory
        try:
            desc = items[0]['spec']['hard']
        except:
            return requestsCpu, requestsMemory, limitsCpu, limitsMemory
        requestsCpu = desc.get('requests.cpu')
        requestsMemory = desc.get('requests.memory')
        limitsCpu = desc.get('limits.cpu')
        limitsMemory = desc.get('limits.memory')

        return requestsCpu, requestsMemory, limitsCpu, limitsMemory
        

    def __getWorkloads(self, workloadType):
        """
        Get All Workloads Informations About Namespace xxx
        """
        workloads = []
        services = []
        # 1
        namespaceList = self.getNamespace()[0]
        for namespace in namespaceList:
            if not namespace['name']:
                continue
            url = self.rootURl+ '/apis/apps/v1/namespaces/' + namespace['name'] + '/' + workloadType
            response = self.excutor.excute(url)
            items = json.loads(response).get('items')
            if not items:
                continue

            for item in items:
                # 2
                try:
                    containers = item['spec']['template']['spec']['containers']
                except:
                    containers = None
                if not containers:
                    continue
                
                try:
                    volumes = item['spec']['template']['spec']['volumes']
                except:
                    volumes = None
                
                # Get VolumesList Information
                volumeMap = {}
                if volumes:
                    for volume in volumes:
                        volumeName = volume.get('name')
                        if volume.get('configMap'):
                            volumeMap[volumeName] = volume.get('configMap')
                            volume.get('configMap')['type'] = 'configMap'
                        elif volume.get('secret'):
                            volumeMap[volumeName] = volume.get('secret')
                            volume.get('secret')['type'] = 'secret'

                workload = {}
                try:
                    name = item['metadata']['name']
                except:
                    name = None
                if name:
                    workload['name'] = name
                
                try:
                    replicas = item['spec']['replicas']
                except:
                    replicas = None
                if replicas:
                    workload['replicas'] = replicas
                workload['overdue'] = "true"
                workload['classification'] = workloadType
                workload['namespace'] = namespace['name']
                workload['region'] = namespace['region']
                workload['env'] = namespace['env']
                workload['cluster_name'] = namespace['cluster_name']
                containerList = []
                # Cpu(0.01=1m) Memory(1Gi=1024Mi)
                requestsCpuSum = requestsMemorySum = limitsCpuSum = limitsMemorySum = 0
                # 3
                for container in containers:
                    result = {}
                    
                    containerName = container.get('name')
                    if containerName:
                        result['name'] = containerName

                    imageName = container.get('image')
                    if imageName:
                        result['imageName'] = imageName

                    try:
                        limits = container['resources']['limits']
                        requests = container['resources']['requests']
                    except:
                        limits = None
                        requests = None

                    requestsCpu = requestsMemory = limitsCpu = limitsMemory = None
                    if all([limits, requests]):
                        requestsCpuStr = requests.get('cpu')
                        if requestsCpuStr:
                            requestsCpu = int(requestsCpuStr.rstrip('m'))*0.001 if 'm' in requestsCpuStr else int(requestsCpuStr)
                            
                        requestsMemoryStr = requests.get('memory')
                        if requestsMemoryStr:
                            if 'Gi' in requestsMemoryStr:
                                requestsMemory = int(requestsMemoryStr.rstrip('Gi'))*1024
                            elif 'Mi' in requestsMemoryStr:
                                requestsMemory = int(requestsMemoryStr.rstrip('Mi'))

                        limitsCpuStr = limits.get('cpu')
                        if limitsCpuStr:
                            limitsCpu = int(limitsCpuStr.rstrip('m'))*0.001 if 'm' in limitsCpuStr else int(limitsCpuStr)

                        limitsMemoryStr = limits.get('memory')
                        if limitsMemoryStr:
                            if 'Gi' in limitsMemoryStr:
                                limitsMemory = int(limitsMemoryStr.rstrip('Gi'))*1024
                            elif 'Mi' in limitsMemoryStr:
                                limitsMemory = int(limitsMemoryStr.rstrip('Mi'))

                    if requestsCpu:
                        requestsCpuSum += requestsCpu
                    if requestsMemory:
                        requestsMemorySum += requestsMemory
                    if limitsCpu:
                        limitsCpuSum += limitsCpu
                    if limitsMemory:
                        limitsMemorySum += limitsMemory

                    if volumeMap:
                        try:
                            volumeMounts = [ volume.get('name') for volume in container['volumeMounts'] ]
                        except:
                            volumeMounts = []

                        if volumeMounts:
                            configMap = []
                            secret = []
                            for volume in volumeMounts:
                                if not volumeMap.get(volume): continue
                                try:
                                    if volumeMap[volume].get('type') == 'configMap':
                                        configMap.append(volume)
                                    elif volumeMap[volume].get('type') == 'secret':
                                        secret.append(volume)
                                except:
                                    continue
                        
                            if configMap:
                                result['configMap'] = ','.join(configMap)
                            if secret:
                                result['secret'] = ','.join(secret)

                    containerList.append(result)
                workload['containers'] = containerList
                if requestsCpu != 0:
                    workload['requestsCpu'] = str(requestsCpuSum)
                if requestsMemory != 0:
                    workload['requestsMemory'] = str(requestsMemorySum)+'Mi'
                if limitsCpu != 0:
                    workload['limitsCpu'] = str(limitsCpuSum)
                if limitsMemory != 0:
                    workload['limitsMemory'] = str(limitsMemorySum)+'Mi'
                workloads.append(workload)

        return workloads

    def getDeployments(self):
        return self.__getWorkloads('deployments')

    def getStatefulsets(self):

        return self.__getWorkloads('statefulsets')

    def getDaemonsets(self):
        return self.__getWorkloads('daemonsets')

    def __getServices(self, namespace, env):
        url = self.rootURl+ '/api/v1/namespaces/' + namespace + '/services'
        response = self.excutor.excute(url)
        items = json.loads(response).get('items')
        if not items:
            return None
        serviceList = []
        for item in items:
            instance = {}
            # instance['serviceNamespace'] = namespace
            try:
                workload = item['metadata']['labels']['app']
            except:
                workload = None
            if workload:
                instance['serviceWorkload'] = workload
                instance['serviceNamespace'] = namespace

                instance['serviceenv'] = env
                instance['serviceCluster'] = env
                instance['overdue'] = "true"

            # ports = None

                spec = item.get('spec')
                if not spec:
                    continue
                
                try:
                    serviceName = item['metadata']['name']
                except:
                    serviceName = None
    
                portList = spec.get('ports')
                if portList:
                    ports = [ str(item.get('port')) for item in portList if item.get('port') ]
                serviceType = spec.get('type')
                serviceIP = spec.get('clusterIP')
    
                if serviceType:
                    instance['serviceType'] = serviceType
                if serviceIP and serviceIP != 'None':
                    instance['serviceIP'] = serviceIP
                if ports:
                    instance['servicePort'] = ports
                if serviceName:
                    instance['serviceName'] = serviceName
                    serviceList.append(instance)

        return serviceList

    def getNodes(self):
        NodeMap = self.__getNodesMapFromPods()
        nodeList = []
        url = self.rootURl+ '/api/v1/nodes'
        response = self.excutor.excute(url)
        responseInstance = json.loads(response)
        items = responseInstance.get('items')
        if not items:
            return nodeList
        for item in items:
            if item.get('metadata'):
                metadata = item.get('metadata')
            else:
                continue
            name = metadata.get('name')

            try:
                labels = item['metadata']['labels']
            except:
                labels = None
            try:
                addresses = item['status']['addresses']
            except:
                addresses = []
            
            address = None
            if addresses:
                for item in addresses:
                    if item.get('type') == 'InternalIP':
                        address = item.get('address')
                        break

            if labels:
                nodeType = labels.get('caicloud.io/role')
                env = labels.get('env')
                region = labels.get('region')
                
            if NodeMap.get(address):
                for namespace in NodeMap[address].keys():
                    for app in NodeMap[address][namespace]:
                        instance = {}
                        if name:
                            instance['name'] = name
                        if nodeType:
                            instance['type'] = nodeType
                        if region:
                            instance['region'] = region
                        instance['overdue'] = "true"
                        if env:
                            instance['env'] = env
                            instance['cluster_name'] = env
                        if address:
                            instance['ip'] = address
                        instance['namespace'] = namespace
                        instance['app'] = app
                        nodeList.append(instance)
            
        return nodeList
    
    def __getNodesMapFromPods(self):
        nodesMap = {}
        url = self.rootURl+ '/api/v1/pods'
        response = self.excutor.excute(url)
        responseInstance = json.loads(response)
        items = responseInstance.get('items')
        if not items:
            return nodesMap
        nodesMap = {}
        for item in items:
            try:
                nodeIP = item['status']['hostIP']
            except:
                continue
            
            try:
                namespace = item['metadata']['namespace']
            except:
                namespace = None
            
            try:
                app = item['metadata']['labels']['app']
            except:
                app = None
            
            if not nodesMap.get(nodeIP):
                nodesMap[nodeIP] = {}

            if namespace and namespace not in nodesMap[nodeIP].keys():
                nodesMap[nodeIP][namespace] = []
            if app:
                nodesMap[nodeIP][namespace].append(app)

        return nodesMap

        
    def getLoadbalance(self):
        pass

    def outputData(self, outputType):
        if outputType.lower() == 'namespace':
        #     return json.dumps({'CIT_Namespace': self.getNamespace()}, ensure_ascii=False, indent=2)
            return json.dumps({
                    'CIT_Namespace': self.getNamespace()[0], 
                    'CIT_k8sService': self.getNamespace()[1], 
                }, ensure_ascii=False, indent=2)
        elif outputType.lower() == 'workload':
            return json.dumps({
                    'CIT_workload': self.getDeployments() + self.getStatefulsets() + self.getDaemonsets(),
                }, ensure_ascii=False, indent=2)

        elif outputType.lower() == 'node':
            return json.dumps({'CIT_node_info': self.getNodes()}, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--type', type=str, help='Namespace/Workload/Nodes/LoadBalance')
    parser.add_argument('--api', type=str, help='Kubernetes Platform Base Url')
    parser.add_argument('--ca', type=str, help='CA Files Parent Package Path')
    args = parser.parse_args()
    if args.type.lower() not in ['namespace','workload','node','loadbalance']:
        raise Exception(json.dumps({
            'ERROR': 'Type Error , Domain Contains [ Namespace/Workload/Node/LoadBalance ] '
        }, ensure_ascii=False, indent=2))
    instance = K8SData(args.api, args.ca)
    output = instance.outputData(args.type)
    print(output)
