# -*- coding: utf8 -*-
import requests
import datetime
import uuid
import json
import warnings
warnings.filterwarnings("ignore")

class pushNotification(object):
    def __init__(self):
        #redfish user
        self.username = 'root'
        #redfish pwd
        self.password = 'devvops'
        #网络协议
        self.agreement = 'https://'
        #redfish_Sessions
        self.Sessions_route = '/redfish/v1/SessionService/Sessions'
        #redfish_Temperature
        self.route = '/redfish/v1/Chassis/System.Embedded.1/Thermal'
        #service Address
        self.ServerAddress = ['192.168.1.121', '192.168.1.122', '192.168.1.133', '192.168.1.170', '192.168.1.155', '192.168.1.162']

    def post_Sessions(self, ServerAddress):
        url = self.agreement + ServerAddress + self.Sessions_route
        header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        data = {
            "UserName": self.username,
            "Password": self.password
        }
        response = requests.post(
            url=url, headers=header, data=json.dumps(data), verify=False)
        return response.headers['X-Auth-Token']

    def post_Temperature(self, ServerAddress, Sessions):
        url = self.agreement + ServerAddress + self.route
        header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Sessions
        }
        response = requests.get(url=url, headers=header, verify=False)
        return json.loads(response.text)
    
    def Post_Temperature_summary(self):
        IpAddress = self.ServerAddress
        deviceSummary = []
        for ip in IpAddress:
            Sessions = self.post_Sessions(ip)
            Temperature = self.post_Temperature(ip,Sessions)
            for device in Temperature['Temperatures']:
                deviceSummary.append({
                    'id':str(uuid.uuid1()),
                    'hostIP':ip,
                    'deviceName':device['Name'],
                    'deviceTemperature':device['ReadingCelsius'],
                    'deviceStatus':device['Status']['Health'],
                    'collectTime':str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                })
        return {'CIT_hostTemperatureInfo':deviceSummary}

if __name__ == '__main__':
    instance = pushNotification()
    print(json.dumps(instance.Post_Temperature_summary(),ensure_ascii=False))
