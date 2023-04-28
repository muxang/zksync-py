import time
import requests
from eth_abi import encode
from eth_utils import is_hex_address, is_hex, to_hex
from utils.base_op import ZkSyncBaseOp
from .constent import USDC_ADDRESS, SYNC_ROUTER_ADDRESS

def hex_string_to_array(hex_string):
    if not is_hex(hex_string) or not hex_string.startswith("0x"):
        raise ValueError("Input must be a hex string starting with '0x'.")

    first_element_length = 10
    other_elements_length = 64

    result = [hex_string[:first_element_length]]

    for i in range(first_element_length, len(hex_string), other_elements_length):
        result.append(hex_string[i:i + other_elements_length])

    return result


def format_to_hex64(input_value):
    if isinstance(input_value, int):
        hex_value = to_hex(input_value)[2:]
    elif isinstance(input_value, str) and is_hex_address(input_value):
        hex_value = input_value[2:]
    else:
        raise ValueError("Input must be an integer or an Ethereum address string.")

    while len(hex_value) < 64:
        hex_value = "0" + hex_value

    return hex_value


def encode_string(input_string):
    encoded_data = encode(["string"], [input_string])
    encoded_data_hex = to_hex(encoded_data)

    offset_hex = encoded_data_hex[:66]
    length_hex = encoded_data_hex[66:130]
    data_hex = encoded_data_hex[130:]

    return [offset_hex, length_hex, data_hex]


def array_to_hex_string(arr):
    return "".join(arr)

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

def approve(zksync_base_op: ZkSyncBaseOp, dapp):
    # 获取当前账户的 USDC 余额, 直到余额大于0
    while True:
        try:
            usdc_balance, usdc_wei_balance = zksync_base_op.get_erc20_balance(USDC_ADDRESS)
            if usdc_balance > 0:
                break
        except Exception as e:
            print(f"账户 {zksync_base_op.signer.address} 执行 {dapp.name} approve 操作时, 获取USDC余额失败, 10s后重试: {e}")
            time.sleep(10)
    # approve
    while True:
        try:
            tx_hash = zksync_base_op.approve_erc20(dapp.cAddress, usdc_wei_balance, USDC_ADDRESS)
            break
        except Exception as e:
            print(f"账户 {zksync_base_op.signer.address} 执行 {dapp.name} approve 操作时, approve失败, 10s后重试: {e}")
            time.sleep(10)
    return tx_hash

def num2hex(num: int) -> str:
    if num < 10:
        return str(num)
    str_hex = 'ABCDEF'
    return str_hex[num - 10]
  
def fee2hex(fee: int) -> str:
    n0 = fee % 16
    n1 = (fee // 16) % 16
    n2 = (fee // 256) % 16
    n3 = (fee // 4096) % 16
    n4 = 0
    n5 = 0
    return '0x' + num2hex(n5) + num2hex(n4) + num2hex(n3) + num2hex(n2) + num2hex(n1) + num2hex(n0)