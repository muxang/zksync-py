import random
import time

from utils.base_op import ZkSyncBaseOp
from zksync2.manage_contracts.contract_encoder_base import BaseContractEncoder
from interaction.constent import ETH_ADDRESS, USDC_ADDRESS
from interaction.utils import approve, fee2hex


# 读取abi
with open("interaction/abi/izumi.json", "r") as f:
    swap_abi = f.read()
with open("interaction/abi/izumi_pool.json", "r") as f:
    pool_abi = f.read()
with open("interaction/abi/izumi_quoter.json", "r") as f:
    quoter_abi = f.read()
    

swap_address = "0x9606eC131EeC0F84c95D82c9a63959F2331cF2aC"
pool_address = "0x6ac81d4c43C86c8DbD4842c1eb0fd1a1c2C16b97"
quoter_address = "0x377EC7c9ae5a0787F384668788a1654249059dD6"

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
    pool = zksync_base_op.get_contract_instance(pool_address, pool_abi)
    quoter = zksync_base_op.get_contract_instance(quoter_address, quoter_abi)
    # 获取pool fee
    while True:
        try:
            pool_fee = pool.functions.fee().call()
            break
        except Exception as e:
            print(f"账户 {address} 交互 {dapp.name} 购买操作时, 获取pool_fee错误, 等待10秒后重试: {e}")
            time.sleep(10)
    token_in_address = ETH_ADDRESS
    token_out_address = USDC_ADDRESS
    # 获取path bytes
    path = bytes.fromhex(token_in_address[2:] + fee2hex(pool_fee)[2:] + token_out_address[2:])
    # deadline = now + 10 minutes
    deadline = int(time.time()) + 600
    # 获取amountOut
    while True:
        try:
            amount_out, pointAfterList = quoter.functions.swapAmount(amount_in, path).call()
            break
        except Exception as e:
            print(f"账户 {address} 交互 {dapp.name} 购买操作时, 获取amountOut错误, 等待10秒后重试: {e}")
            time.sleep(10)
    # 滑点设置
    amount_out_min = amount_out * 999 // 1000
    swap_amount_params = {
        'path': path,
        'recipient': address,
        'amount': amount_in,
        'minAcquired': amount_out_min,
        'deadline': deadline
    }
    contract_encoder = BaseContractEncoder(zksync_base_op.zk_web3, swap_abi)
    swap_amount_call = contract_encoder.encode_method(fn_name="swapAmount", args=(swap_amount_params,))
    refunde_eth_call = contract_encoder.encode_method(fn_name="refundETH", args=())
    function_calls = [swap_amount_call, refunde_eth_call]
    multi_call = contract_encoder.encode_method(fn_name="multicall", args=(function_calls,))
    try:
        tx_hash = zksync_base_op.contract_call(multi_call, dapp, value=amount_in)
    except Exception as e:
        raise Exception(f"账户 {address} 交互 {dapp.name} 购买操作时, 调用合约错误: {e}")

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
    pool = zksync_base_op.get_contract_instance(pool_address, pool_abi)
    quoter = zksync_base_op.get_contract_instance(quoter_address, quoter_abi)
    # 获取pool fee
    while True:
        try:
            pool_fee = pool.functions.fee().call()
            break
        except Exception as e:
            print(f"账户 {address} 交互 {dapp.name} 卖出操作时, 获取pool_fee错误, 等待10秒后重试: {e}")
            time.sleep(10)
    
    token_in_address = USDC_ADDRESS
    token_out_address = ETH_ADDRESS
    # 获取path bytes
    path = bytes.fromhex(token_in_address[2:] + fee2hex(pool_fee)[2:] + token_out_address[2:])
    # deadline = now + 10 minutes
    deadline = int(time.time()) + 600
    amount_in = usdc_wei_balance
    # 获取amountOut
    while True:
        try:
            amount_out, pointAfterList = quoter.functions.swapAmount(amount_in, path).call()
            break
        except Exception as e:
            print(f"账户 {address} 交互 {dapp.name} 卖出操作时, 获取amountOut错误, 等待10秒后重试: {e}")
            time.sleep(10)
    # 滑点设置
    amount_out_min = amount_out * 999 // 1000
    swap_amount_params = {
        'path': path,
        'recipient': swap_address,
        'amount': amount_in,
        'minAcquired': amount_out_min,
        'deadline': deadline
    }
    contract_encoder = BaseContractEncoder(zksync_base_op.zk_web3, swap_abi)
    swap_amount_call = contract_encoder.encode_method(fn_name="swapAmount", args=(swap_amount_params,))
    unwrap_weth_call = contract_encoder.encode_method(fn_name="unwrapWETH9", args=(0, address))
    function_calls = [swap_amount_call, unwrap_weth_call]
    multi_call = contract_encoder.encode_method(fn_name="multicall", args=(function_calls,))
    try:
        tx_hash = zksync_base_op.contract_call(multi_call, dapp)
    except Exception as e:
        raise Exception(f"账户 {address} 交互 {dapp.name} 卖出操作时, 调用合约错误: {e}")

    return tx_hash

def interact_with_izumi(zksync_base_op: ZkSyncBaseOp, address, dapp):
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
