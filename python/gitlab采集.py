# /usr/bin/python
# coding=utf-8
import sys
import requests
import json
from optparse import OptionParser
from pyDes import *
from binascii import a2b_hex


def des_decrypt(message):
    k = des('shdevopsshdevops', ECB, padmode=PAD_PKCS5)
    return k.decrypt(a2b_hex(message)).decode('utf8')


parser = OptionParser()
parser.add_option('--tokenString', type=str,dest='tokenString')
parser.add_option('--url', type=str, dest='url')
(options, args) = parser.parse_args()
tokenString = des_decrypt(options.tokenString)
#tokenString = options.tokenString
url = options.url
num = 1
reload(sys)
sys.setdefaultencoding('utf8')


def get_data(num):
    urll = 'http://{}/api/v4/projects?per_page=100&page={}'.format(url, num)
    header = {
        "PRIVATE-TOKEN": tokenString,
    }
    req = requests.get(headers=header, url=urll)
    status = str(req.status_code)
    if '200' in status:
        version = "v4"
        aaa = json.loads(json.dumps(req.json()))
        return aaa, version
    else:
        urll = 'http://{}/api/v3/projects/all?per_page=100&page={}'.format(
            url, num)
        header = {
            "PRIVATE-TOKEN": tokenString,
        }
        req = requests.get(headers=header, url=urll)
        aaa = json.loads(json.dumps(req.json()))
        version = "v3"
        return aaa, version


def get_gdata(num, b):
    gurll = 'http://{}/api/{}/groups?per_page=100&page={}'.format(url, b, num)
    header = {
        "PRIVATE-TOKEN": tokenString,
    }
    greq = requests.get(headers=header, url=gurll)
    status = str(greq.status_code)
    if '200' in status:
        groups = json.loads(json.dumps(greq.json()))
        return groups


a, b = get_data(num)
cc = []
g_list = list()
cc.append(get_data(num)[0])

if get_gdata(num, b):
    g_list.append(get_gdata(num, b))
while num <= 10000:

    if get_data(num)[0]:
        num += 1
        data = get_data(num)[0]
        cc.append(data)
    else:
        break
while num <= 10000:
    if get_gdata(num, b):
        num += 1
        data = get_gdata(num, b)
        g_list.append(data)
    else:
        break
git_data = []

for i in cc:
    for d in i:
        item = dict()
        owner_list = []
        owneruser_list = []
        mastername_list = []
        masterusername_list = []
        id = d.get('id')
        item["id"] = id
        if str(d.get('archived')):
            item["archived"] = d.get('archived')
        item["type"] = "gitlab"
        item["overdue"] = "true"
        if d.get('name'):
            item["name"] = d.get('name')
        group_id = d.get('namespace').get('id')
        if d.get('http_url_to_repo'):
            item["http_url_to_repo"] = d.get('http_url_to_repo')
        if d.get('owner'):
            item["master_name"] = [d.get('owner').get('name')]
            item["masterusername"] = [d.get('owner').get('username')]

        else:
            if d.get('namespace'):
                if b == "v4":
                    if "/" not in d.get('namespace').get('full_path'):
                        item["groups"] = d.get('namespace').get('name')
                        group = str(d.get('namespace').get('name'))
                    else:
                        full_path = d.get('namespace').get('full_path')
                        item["groups"] = full_path.split("/", 1)[0]
                        group = str(full_path.split("/", 1)[0])
                else:
                    if "/" not in d.get('namespace').get('path'):
                        item["groups"] = d.get('namespace').get('name')
                        group = str(d.get('namespace').get('name'))
                    else:
                        full_path = d.get('namespace').get('path')
                        item["groups"] = full_path.split("/", 1)[0]
                        group = str(full_path.split("/", 1)[0])
            prourl = 'http://{}/api/{}/projects/{}/members'.format(url, b, id)
            headere = {
                "PRIVATE-TOKEN": tokenString,
            }
            reqs = requests.get(headers=headere, url=prourl)
            p_owners = json.loads(json.dumps(reqs.json()))
            if p_owners:
                for h in p_owners:
                    p_name = h.get('name')
                    p_username = h.get('username')
                    p_num = str(h.get('access_level'))
                    if '50' in p_num:
                        owner_list.append(p_name)
                        owneruser_list.append(p_username)
                    if '40' in p_num:
                        mastername_list.append(p_name)
                        masterusername_list.append(p_username)
                    else:
                        grourl = 'http://{}/api/{}/groups/{}/members'.format(
                            url, b, group_id)
                        headerc = {
                            "PRIVATE-TOKEN": tokenString,
                        }
                        reqsa = requests.get(headers=headerc, url=grourl)
                        g_owners = json.loads(json.dumps(reqsa.json()))
                        for j in g_owners:
                            g_name = j.get('name')
                            g_username = j.get('username')
                            g_num = str(j.get('access_level'))
                            if '50' in g_num:
                                owner_list.append(g_name)
                                owneruser_list.append(g_username)
                            if '40' in g_num:
                                mastername_list.append(g_name)
                                masterusername_list.append(g_username)

            else:
                grourl = 'http://{}/api/{}/groups/{}/members'.format(
                    url, b, group_id)
                headerc = {
                    "PRIVATE-TOKEN": tokenString,
                }
                reqsa = requests.get(headers=headerc, url=grourl)
                g_owners = json.loads(json.dumps(reqsa.json()))
                for j in g_owners:
                    g_name = j.get('name')
                    g_username = j.get('username')
                    g_num = str(j.get('access_level'))
                    if '50' in g_num:
                        owner_list.append(g_name)
                        owneruser_list.append(g_username)
                    if '40' in g_num:
                        mastername_list.append(g_name)
                        masterusername_list.append(g_username)
            item["owner"] = list(set(owner_list))
            item["owner_username"] = list(set(owneruser_list))
            if mastername_list != []:
                item["master_name"] = list(set(mastername_list))
                item["masterusername"] = list(set(masterusername_list))
            else:
                for i in g_list:
                    for n in i:
                        if group == str(n.get('name')):
                            sourceid = n.get('id')
                            sgrourl = 'http://{}/api/{}/groups/{}/members'.format(
                                url, b, sourceid)
                            headerc = {
                                "PRIVATE-TOKEN": tokenString,
                            }
                            sreqsa = requests.get(headers=headerc, url=sgrourl)
                            if "404" not in sreqsa.text:
                                sg_mem = json.loads(json.dumps(sreqsa.json()))
                                for j in sg_mem:
                                    g_name = j.get('name')
                                    g_username = j.get('username')
                                    g_num = str(j.get('access_level'))
                                    if '40' in g_num:
                                        mastername_list.append(g_name)
                                        masterusername_list.append(g_username)
                if mastername_list != []:
                    item["master_name"] = list(set(mastername_list))
                    item["masterusername"] = list(set(masterusername_list))

        git_data.append(item)
msg_dict = dict()
msg_dict["CIT_codebase"] = git_data
msg = json.dumps(msg_dict, ensure_ascii=False)
print(msg)

# ---
# - hosts: all
#   gather_facts: no
#   tasks:
#     - file: 
#         path: /tmp/cmdb_tmp/
#         state: directory
        
#     - copy:
#         src: ./gitlab.py
#         dest: /tmp/cmdb_tmp/gitlab.py

#     - shell: python  /tmp/cmdb_tmp/gitlab.py --tokenString "{{tokenString}}" --url "{{url}}"
      
#     - file:
#         path: /tmp/cmdb_tmp/
#         state: absent
        
      