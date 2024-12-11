#!/bin/bash

dns_servers=("8.8.8.8" "1.1.1.1")  # 可信任的 DNS 服务器 IP 地址列表

check_dns_hijack() {
  local dns_server="$1"
  local test_domain="infra-iaas-1312767721.cos.ap-shanghai.myqcloud.com
"  # 用于测试的域名

  local dns_lookup_output
  dns_lookup_output=$(nslookup "$test_domain" "$dns_server" 2>&1)

  if echo "$dns_lookup_output" | grep -q "NXDOMAIN"; then
    echo "正常：DNS 解析结果返回 NXDOMAIN，不受 DNS 劫持影响：$dns_server"
  elif echo "$dns_lookup_output" | grep -q "REFUSED"; then
    echo "正常：DNS 服务器拒绝解析请求，不受 DNS 劫持影响：$dns_server"
  else
    echo "注意：可能受 DNS 劫持影响：$dns_server"
  fi
}

for dns_server in "${dns_servers[@]}"; do
  check_dns_hijack "$dns_server"
done

# 脚本解释
# 定义 DNS 服务器列表：dns_servers 数组包含了两个可信任的 DNS 服务器 IP 地址（"8.8.8.8" 和 "1.1.1.1"）。
# 定义检查函数：check_dns_hijack 函数接收一个 DNS 服务器地址作为参数，并使用 nslookup 命令尝试解析一个特定的测试域名。根据 nslookup 的输出，函数会判断 DNS 是否可能受到劫持。
# 解析测试域名：测试域名被硬编码在脚本中，用于检查 DNS 解析行为。
# 检查响应：
# 如果响应包含 "NXDOMAIN"，表示域名不存在，这是正常的响应，不受 DNS 劫持影响。
# 如果响应包含 "REFUSED"，表示 DNS 服务器拒绝解析请求，这通常也是正常的响应，不受 DNS 劫持影响。
# 如果以上两种情况都不满足，则输出警告信息，提示可能受到 DNS 劫持影响。
# 遍历 DNS 服务器列表：脚本通过遍历 dns_servers 数组，对每个 DNS 服务器调用 check_dns_hijack 函数。