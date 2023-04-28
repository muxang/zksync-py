import requests
import socket
import socks
import interaction.utils as utils
import interaction.velocore as velocore

def test_proxy(proxy_str, protocol="socks5", timeout=5):
    proxy_parts = proxy_str.split('@')
    proxy_auth = proxy_parts[0].split(':')
    proxy_address = proxy_parts[1].split(':')

    username = proxy_auth[0]
    password = proxy_auth[1]
    ip = proxy_address[0]
    port = int(proxy_address[1])

    socks.set_default_proxy(socks.SOCKS5, ip, port, rdns=True, username=username, password=password)
    socket.socket = socks.socksocket

    test_url = "https://httpbin.org/ip"
    
    try:
        # 检测代理连接可用性
        response = requests.get(test_url, timeout=timeout)
        response.raise_for_status()
    except (requests.exceptions.RequestException, socket.timeout):
        return False, "连接失败", None

    try:
        # 检测代理匿名性
        ip_info = response.json()
        if "origin" not in ip_info:
            return False, "IP被识别", None
        return True, "代理有效且匿名", ip_info['origin']
    except ValueError:
        return False, "解析响应失败", None

proxy_str = "14a31c213822f:e2ac361773@212.236.124.130:12324"
# is_valid, message, proxy_ip = test_proxy(proxy_str)

# if proxy_ip:
#     print(f"代理IP: {proxy_ip}")

# print(message)

def get_exchange_rate():
    url = f"https://www.okx.com/api/v5/market/ticker?instId=ETH-USDC-SWAP"
    response = requests.get(url)
    result = response.json()
    return result['data'][0]['last']

def convert_currency(base_currency, quote_currency, amount):
    exchange_rate = get_exchange_rate()
    if base_currency == "USDC":
        return float(amount) / float(exchange_rate)
    elif quote_currency == "USDC":
        return float(amount) * float(exchange_rate)

# Example usage:
from_currency = "ETH"
amount = "3"
to_currency = "USDC"

converted_amount = convert_currency(from_currency, to_currency, amount)
print(f"{amount} {from_currency} is equal to {converted_amount} {to_currency}")

from_currency = "USDC"
amount = str(converted_amount - 3 * float(amount))
to_currency = "ETH"

converted_amount = convert_currency(from_currency, to_currency, amount)
print(f"{amount} {from_currency} is equal to {converted_amount} {to_currency}")

# from web3 import Web3
# input_amount = Web3.to_wei(1.2, 'mwei')
# print(input_amount)


# data = utils.hex_string_to_array("0xeeaa0e2100000000000000000000000000000000000000000000000000000000000000e0000000000000000000000000218ac84fb802985e99336cd9dfbe71fc54da4bce0000000000000000000000000000000000000000000000000000000001e13380000000000000000000000000ce70b7f5bb44be2f8a7f37f8c162240440fc6218000000000000000000000000218ac84fb802985e99336cd9dfbe71fc54da4bce00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000873686172706c6565000000000000000000000000000000000000000000000000")
# print(data)

# result = utils.encode_string("sharplee")
# print(result)

