import json
import requests
from optparse import OptionParser


def get_token(username,password,domainName,project):
    url = 'https://iam.myhuaweicloud.com/v3/auth/tokens'
    header = {"Content-Type":"application/json;charset=utf8"}
    body = {
        "auth": {
            "identity": {
                "methods": [
                    "password"
                ],
                "password": {
                    "user": {
                        "name": username,
                        "password": password,
                        "domain": {
                            "name": domainName
                        }
                    }
                }
            },
            "scope": {
                "project": {
                    "name": project
                }
            }
        }
    }
    response = requests.post(url=url,headers=header,data=json.dumps(body))
    res = json.loads(response.text).get('token').get('catalog')
    headers = response.headers.get('X-Subject-Token')
    data = dict()
    for i in res:
        if i.get('name') == "bms":
            data['url'] = i.get('endpoints')[0]
            data['X-Subject-Token'] = headers
    return data


def get_bms(data):
    #https://{endpoint}/v1/{project_id}/cloudservers/detail?offset=1&limit=100
    url = "{}/baremetalservers/detail".format(data['url']['url'])
    header = {"X-Auth-Token":data['X-Subject-Token'],"Content-Type": "application/json;charset=UTF-8"}
    response = requests.get(url=url,headers=header)
    res = json.loads(response.text)
    return res


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--username', type=str, dest='username')
    parser.add_option('--password', type=str, dest='password')
    parser.add_option('--domain', type=str, dest='domain')
    parser.add_option('--project', type=str, dest='project')
    (options, args) = parser.parse_args()
    username = options.username
    password = options.password
    domain = options.domain
    project = options.project
    data = get_token(username,password,domain,project)
    print(get_bms(data))

