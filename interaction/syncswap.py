import random
import time
from web3 import Web3
from utils.base_op import ZkSyncBaseOp
from interaction.utils import hex_string_to_array, format_to_hex64, array_to_hex_string, approve
from interaction.constent import ETH_ADDRESS, USDC_ADDRESS, SYNC_POOL_ADDRESS, SYNC_BUY_DATA, SYNC_SELL_DATA, SYNC_POOL_ABI

def get_buy_call_data(contract, to_address, in_amount, name):
    input_amount_wei = Web3.to_wei(in_amount, 'ether')
    input_amount_hex_str = format_to_hex64(input_amount_wei)
    while True:
        try:
            output_amount = contract.functions.getAmountOut(ETH_ADDRESS, input_amount_wei, to_address).call() * 999 // 1000
            break
        except Exception as e:
            print(f"账户 {to_address} 交互 {name} 购买操作时, 获取amountOut错误, 等待10秒后重试: {e}")
            time.sleep(10)

    output_amount_hex_str = format_to_hex64(output_amount)
    # deadline = now + 3 hours + 20 minutes
    deadline = format_to_hex64(int(time.time()) + 3 * 3600 + 20 * 60)
    to_address_hex_str = format_to_hex64(to_address)

    buy_array = hex_string_to_array(SYNC_BUY_DATA)
    buy_array[2] = output_amount_hex_str
    buy_array[3] = deadline
    buy_array[8] = input_amount_hex_str
    buy_array[17] = to_address_hex_str

    return array_to_hex_string(buy_array)

def get_sell_call_data(contract, to_address, in_amount, name):
    input_amount_hex_str = format_to_hex64(in_amount)
    while True:
        try:
            output_amount = contract.functions.getAmountOut(USDC_ADDRESS, in_amount, to_address).call() * 999 // 1000
            break
        except Exception as e:
            print(f"账户 {to_address} 交互 {name} 卖出操作时, 获取amountOut错误, 等待10秒后重试: {e}")
            time.sleep(10)
    output_amount_hex_str = format_to_hex64(output_amount)
    # deadline = now + 3 hours + 20 minutes
    deadline = format_to_hex64(int(time.time()) + 3 * 3600 + 20 * 60)
    to_address_hex_str = format_to_hex64(to_address)

    sell_array = hex_string_to_array(SYNC_SELL_DATA)
    sell_array[2] = output_amount_hex_str
    sell_array[3] = deadline
    sell_array[8] = input_amount_hex_str
    sell_array[17] = to_address_hex_str

    return array_to_hex_string(sell_array)

def buy(zksync_base_op: ZkSyncBaseOp, address, dapp):
    # 获取当前账户的 ETH 余额
    while True:
        try:
            eth_balance, wei_balance = zksync_base_op.get_eth_balance()
            break
        except Exception as e:
            print(f"账户 {address} 交互 {dapp.name} 购买操作时, 获取ETH余额错误, 等待10秒后重试: {e}")
            time.sleep(10)
    # 随机生成0.01-0.3之间的ETH数量, 用于交易
    eth_amount = random.uniform(0.01, 0.3)
    amount_in = zksync_base_op.zk_web3.to_wei(eth_amount, "ether")
    amount_fee = zksync_base_op.zk_web3.to_wei(0.002, "ether")
    amount_in = amount_in if wei_balance > (amount_in + amount_fee) else wei_balance - amount_fee
    if amount_in <= 0:
        raise Exception(f"账户 {address} 交互 {dapp.name} 购买操作时, ETH余额不足")
    # 获取合约实例
    try:
        contract = zksync_base_op.get_contract_instance(SYNC_POOL_ADDRESS, SYNC_POOL_ABI)
    except Exception as e:
        raise Exception(f"账户 {address} 交互 {dapp.name} 购买操作时, 获取合约实例失败: {e}")
    # 获取buy函数的callData
    buy_call_data = get_buy_call_data(contract, address, eth_amount, dapp.name)
    # 调用contract call
    try:
        tx_hash = zksync_base_op.contract_call(buy_call_data, dapp, value=amount_in)
    except Exception as e:
        raise Exception(f"账户 {address} 交互 {dapp.name} 购买操作时, 调用合约失败: {e}")
    return tx_hash

def sell(zksync_base_op: ZkSyncBaseOp, address, dapp):
    # 获取当前账户的 USDC 余额
    while True:
        try:
            usdc_balance, usdc_wei_balance = zksync_base_op.get_erc20_balance(USDC_ADDRESS)
            break
        except Exception as e:
            print(f"账户 {address} 交互 {dapp.name} 卖出操作时, 获取USDC余额错误, 等待10秒后重试: {e}")
            time.sleep(10)
    # 获取合约实例
    contract = zksync_base_op.get_contract_instance(SYNC_POOL_ADDRESS, SYNC_POOL_ABI)
    # 获取sell函数的callData
    sell_call_data = get_sell_call_data(contract, address, usdc_wei_balance, dapp.name)
    # 调用contract call
    try:
        tx_hash = zksync_base_op.contract_call(sell_call_data, dapp)
    except Exception as e:
        raise Exception(f"账户 {address} 交互 {dapp.name} 卖出操作时, 调用合约失败: {e}")
    return tx_hash

def interact_with_syncswap(zksync_base_op: ZkSyncBaseOp, address, dapp):
    # buy
    while True:
        try:
            buy_tx_hash = buy(zksync_base_op, address, dapp)
        except Exception as e:
            print(f"账户 {address} 交互 {dapp.name} 购买操作时失败, 等待10秒后重试: {e}")
            time.sleep(10)
            continue
        try:
            while True:
                try:
                    # Wait for transaction to be included in a block
                    tx_receipt = zksync_base_op.zk_web3.zksync.wait_for_transaction_receipt(
                        buy_tx_hash, timeout=240, poll_latency=0.5
                    )
                except Exception as e:
                    print(f"账户 {address} 等待 {dapp.name} 买入交易 {buy_tx_hash.hex()} 被打包时错误, 10秒后重试: {e}")
                    # 等待10秒后重试
                    time.sleep(10)
                    continue

                if tx_receipt['status'] != 1:
                    raise Exception(f"账户 {address} 执行 {dapp.name} 买入交易 {buy_tx_hash.hex()} 失败, 状态码: {tx_receipt['status']}")
                print(f"账户 {address} 执行 {dapp.name} 买入交易 {buy_tx_hash.hex()} 成功")
                break
        except Exception as e:
            print(f"10秒后重试: {e}")
            time.sleep(10)
            continue
        break
    
    # approve
    while True:
        try:
            approve_tx_hash = approve(zksync_base_op, dapp)
        except Exception as e:
            print(f"账户 {address} 交互 {dapp.name} approve 操作时失败, 等待10秒后重试: {e}")
            time.sleep(10)
            continue

        try:
            while True:
                try:
                    # Wait for transaction to be included in a block
                    tx_receipt = zksync_base_op.zk_web3.zksync.wait_for_transaction_receipt(
                        approve_tx_hash, timeout=240, poll_latency=0.5
                    )
                except Exception as e:
                    print(f"账户 {address} 等待 {dapp.name} approve 交易 {approve_tx_hash.hex()} 被打包时错误, 10秒后重试: {e}")
                    # 等待10秒后重试
                    time.sleep(10)
                    continue

                if tx_receipt['status'] != 1:
                    raise Exception(f"账户 {address} 执行 {dapp.name} approve 交易 {approve_tx_hash.hex()} 失败, 状态码: {tx_receipt['status']}")
                print(f"账户 {address} 执行 {dapp.name} approve 交易 {approve_tx_hash.hex()} 成功")
                break
        except Exception as e:
            print(f"10秒后重试: {e}")
            time.sleep(10)
            continue
        break
    
    # sell
    while True:
        try:
            sell_tx_hash = sell(zksync_base_op, address, dapp)
        except Exception as e:
            print(f"账户 {address} 交互 {dapp.name} 卖出操作时失败, 等待10秒后重试: {e}")
            time.sleep(10)
            continue

        try:
            while True:
                try:
                    # Wait for transaction to be included in a block
                    tx_receipt = zksync_base_op.zk_web3.zksync.wait_for_transaction_receipt(
                        sell_tx_hash, timeout=240, poll_latency=0.5
                    )
                except Exception as e:
                    print(f"账户 {address} 等待 {dapp.name} 卖出交易 {sell_tx_hash.hex()} 被打包时错误, 10秒后重试: {e}")
                    # 等待10秒后重试
                    time.sleep(10)
                    continue

                if tx_receipt['status'] != 1:
                    raise Exception(f"账户 {address} 执行 {dapp.name} 卖出交易 {sell_tx_hash.hex()} 失败, 状态码: {tx_receipt['status']}")
                print(f"账户 {address} 执行 {dapp.name} 卖出交易 {sell_tx_hash.hex()} 成功")
                return tx_receipt['transactionHash'].hex()
        except Exception as e:
            print(f"10秒后重试: {e}")
            time.sleep(10)
            continue
