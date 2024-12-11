#!/usr/bin/python
# -*- coding: UTF-8 -*-
from obs import ObsClient
import json
from optparse import OptionParser
import datetime
import time
# 创建ObsClient实例
from pyDes import *
from binascii import a2b_hex


def des_decrypt(message):
    k = des('shdevopsshdevops', ECB, padmode=PAD_PKCS5)
    return k.decrypt(a2b_hex(message)).decode('utf8')


parser = OptionParser()
parser.add_option('--ak', type=str, dest='ak')
parser.add_option('--sk', type=str, dest='sk')
parser.add_option('--zone', type=str, dest='zone')
(options, args) = parser.parse_args()
ak = options.ak
sk = des_decrypt(options.sk)
#sk = options.sk
zone = options.zone

obsClient = ObsClient(
    access_key_id=ak,
    secret_access_key=sk,
    server='https://obs.{zone}.myhuaweicloud.com'.format(zone=zone)
)
# 使用访问OBS
# 关闭obsClient
obsClient.close()
obs_list = []
resp = obsClient.listBuckets(True)

obsname = [i.get('name') for i in resp.get('body').get('buckets')]
server = 'https://obs.{zone}.myhuaweicloud.com'.format(zone=zone)
for i in obsname:
    item = dict()
    lists = []
    tags = obsClient.getBucketTagging(i)
    metadata = obsClient.getBucketMetadata(i, server, 'x-obs-header')
    metaheader = metadata.get('header')
    lists = []
    for p in metaheader:

        h = list(p)
        lists.append(h)
    xx = ['fs-file-interface', 'Enabled']
    if xx in lists:
        item["cluster_type"] = "并行文件系统"
        item["bucket_type"] = "并行文件系统"

    else:
        item["cluster_type"] = "对象存储"
        item["bucket_type"] = "对象存储"
    item["status"] = "active"
    versions = obsClient.getBucketVersioning(i)
    if tags.get('body'):
        item["tag"] = tags.get('body').get('tagSet')
        for i in tags.get('body').get('tagSet'):
            if "PDT" in str(i.split('=')[0]):
                item["product"] = i.split('=')[1]
            if "PJT" in str(i.split('=')[0]):
                item["project"] = i.split('=')[1]
    if versions.get('body'):
        # item["is_MVCC"] = versions.get('body').get('Status')  # 多版本状态
        item["is_MVCC"] = "是"  # 多版本状态
    else:
        item["is_MVCC"] = "否"
    ver = versions.get('body')
    medata = metadata.get('body')
    respp = obsClient.listBuckets(True)
    if respp.get('body'):
        a = respp.get('body').get('buckets')
        if respp.get('body').get('owner'):
            item["account_id"] = respp.get('body').get('owner').get('owner_id')
        for k in a:
            if i == k.get('name'):
                create_dates = k.get('create_date')
                item["create_date"] = str(datetime.datetime.strptime(
                    create_dates, "%Y/%m/%d %H:%M:%S"))
                item["region"] = k.get('location')
                region = k.get('location')
    item["name"] = i
    name = i
    if medata:
        if medata.get('storageClass'):
            item["type"] = medata.get('storageClass')
            if str(medata.get('storageClass')) == "STANDARD":
                item["type"] = "标准存储"
            if str(medata.get('storageClass')) == "WARM":
                item["type"] = "低频访问存储"
            if str(medata.get('storageClass')) == "COLD":
                item["type"] = "归档存储"
        if medata.get('obsVersion'):
            item["version"] = medata.get('obsVersion')
        if medata.get('epid'):
            item["enterprise_project_id"] = medata.get('epid')
        if medata.get('availableZone'):
            item["ha_policy"] = "true"
        else:
            item["ha_policy"] = "false"
        item["endpoint"] = 'obs.{}.myhuaweicloud.com'.format(region)
        item["domian"] = '{}.obs.{}.myhuaweicloud.com'.format(name, region)

        obs_list.append(item)
msg_dict = dict()
msg_dict["CIT_OBS"] = obs_list
msg = json.dumps(msg_dict)
print(msg)
