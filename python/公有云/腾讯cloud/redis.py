# !/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib, hmac, json, time
from datetime import datetime
import requests
from optparse import OptionParser


def signature():    
    algorithm = "TC3-HMAC-SHA256"
    date = datetime.utcfromtimestamp(int(time.time())).strftime("%Y-%m-%d")
    service = "redis"
    host = "redis.tencentcloudapi.com"
    # ************* 步骤 1：拼接规范请求串 *************
    http_request_method = "POST"
    canonical_uri = "/"
    canonical_querystring = ""
    ct = "application/json"
    payload = json.dumps(params)
    canonical_headers = "content-type:%s\nhost:%s\n" % (ct, host)
    signed_headers = "content-type;host"
    hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    canonical_request = (http_request_method + "\n" +
                        canonical_uri + "\n" +
                        canonical_querystring + "\n" +
                        canonical_headers + "\n" +
                        signed_headers + "\n" +
                        hashed_request_payload)

    # ************* 步骤 2：拼接待签名字符串 *************
    credential_scope = date + "/" + service + "/" + "tc3_request"
    hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    string_to_sign = (algorithm + "\n" +
                    str(int(time.time())) + "\n" +
                    credential_scope + "\n" +
                    hashed_canonical_request)

    # ************* 步骤 3：计算签名 *************
    # 计算签名摘要函数
    def sign(key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()
    secret_date = sign(("TC3" + secret_key).encode("utf-8"), date)
    secret_service = sign(secret_date, service)
    secret_signing = sign(secret_service, "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    # ************* 步骤 4：拼接 Authorization *************
    authorization = (algorithm + " " +
                    "Credential=" + secret_id + "/" + credential_scope + ", " +
                    "SignedHeaders=" + signed_headers + ", " +
                    "Signature=" + signature)
    return authorization


def post_redis(sign):
        url = "https://redis.tencentcloudapi.com/"
        header = {
            "Content-Type":"application/json",
            "X-TC-Action":"DescribeInstances",
            "X-TC-Version":"2018-04-12",
            "X-TC-Region":region,
            "X-TC-Timestamp":str(int(time.time())),
            "Authorization":sign
        }
        response = requests.post(url=url,headers=header,data=json.dumps(params))
        res = json.loads(response.text)
        return res


if __name__ == '__main__':
    parser = OptionParser()
    params = {"Limit":1000,"Offset":0}
    parser.add_option('--secret_id', type=str, dest='secret_id')
    parser.add_option('--secret_key', type=str, dest='secret_key')
    parser.add_option('--region', type=str, dest='region')
    (options, args) = parser.parse_args()
    secret_id = options.secret_id
    secret_key = options.secret_key
    region = options.region
    sign = signature()
    print(post_redis(sign))

