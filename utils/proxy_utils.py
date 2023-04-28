import socket
import socks
import requests

def test_proxy(proxy_str, timeout=5):
    proxy_parts = proxy_str.split('@')
    proxy_auth = proxy_parts[0].split(':')
    proxy_address = proxy_parts[1].split(':')

    username = proxy_auth[0]
    password = proxy_auth[1]
    ip = proxy_address[0]
    port = int(proxy_address[1])

    socks.set_default_proxy(socks.SOCKS5, ip, port,
                            rdns=True, username=username, password=password)
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


def read_file_lines_to_array(filename):
    """
    读取文件多行数据到数组

    Args:
        filename (str): 文件名

    Returns:
        list: 包含文件中所有行数据的数组
    """
    # 打开文件并读取数据
    with open(filename, 'r') as file:
        # 读取文件中的所有行
        lines = file.readlines()

    # 创建一个空数组，用于存储读取到的数据
    data = []

    # 遍历每一行数据，并添加到数组中（可以根据需要对每一行数据进行处理）
    for line in lines:
        # 去除行尾的换行符
        line = line.strip()
        # 将行数据添加到数组中
        data.append(line)

    # 返回包含文件中所有行数据的数组
    return data
