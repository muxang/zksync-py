import random
import time

from utils.base_op import ZkSyncBaseOp
from zksync2.manage_contracts.contract_encoder_base import BaseContractEncoder
from interaction.constent import ETH_ADDRESS, USDC_ADDRESS
from interaction.utils import approve

with open("interaction/abi/spacefi_router.json", "r") as f:
    contract_abi = f.read()

contract_address = "0x70B86390133d4875933bE54AE2083AAEbe18F2dA"

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
    contract = zksync_base_op.get_contract_instance(contract_address, contract_abi)
    token_in_address = ETH_ADDRESS
    token_out_address = USDC_ADDRESS
    path = [token_in_address, token_out_address]
    # 获取amountOut
    while True:
        try:
            amount_out = contract.functions.getAmountsOut(amount_in, path).call()
            break
        except Exception as e:
            print(f"账户 {address} 交互 {dapp.name} 购买操作时, 获取amountOut错误, 等待10秒后重试: {e}")
            time.sleep(10)
    # 滑点设置
    amount_out_min = amount_out[1] * 999 // 1000
    # deadline = now + 30 minutes
    deadline = int(time.time()) + 30 * 60
    # 实例化mute合约
    contract_encoder = BaseContractEncoder(zksync_base_op.zk_web3, contract_abi)
    # buy 参数
    buy_params = (amount_out_min, path, address, deadline)
    # Encode arguments
    call_data = contract_encoder.encode_method("swapExactETHForTokens", args=buy_params)
    try:
        tx_hash = zksync_base_op.contract_call(call_data, dapp, value=amount_in)
    except Exception as e:
        raise Exception(f"账户 {address} 交互 {dapp.name} 购买操作时, 调用合约失败, 等待10秒后重试: {e}")

    return tx_hash

def sell(zksync_base_op: ZkSyncBaseOp, address, dapp):
    # 获取当前账户的 ETH 余额
    while True:
        try:
            usdc_balance, usdc_wei_balance = zksync_base_op.get_erc20_balance(USDC_ADDRESS)
            break
        except Exception as e:
            print(f"账户 {address} 交互 {dapp.name} 卖出操作时, 获取USDC余额错误, 等待10秒后重试: {e}")
            time.sleep(10)
    # 获取合约实例
    contract = zksync_base_op.get_contract_instance(contract_address, contract_abi)
    amount_in = usdc_wei_balance
    token_in_address = USDC_ADDRESS
    token_out_address = ETH_ADDRESS
    path = [token_in_address, token_out_address]
    # 获取amountOut
    while True:
        try:
            amount_out = contract.functions.getAmountsOut(amount_in, path).call()
            break
        except Exception as e:
            print(f"账户 {address} 交互 {dapp.name} 卖出操作时, 获取amountOut错误, 等待10秒后重试: {e}")
            time.sleep(10)
    # 滑点设置
    amount_out_min = amount_out[1] * 999 // 1000
    # deadline = now + 30 minutes
    deadline = int(time.time()) + 30 * 60
    # 实例化mute合约
    contract_encoder = BaseContractEncoder(zksync_base_op.zk_web3, contract_abi)
    # buy 参数
    sell_params = (amount_in, amount_out_min, path, address, deadline)
    # Encode arguments
    call_data = contract_encoder.encode_method("swapExactTokensForETH", args=sell_params)
    try:
        tx_hash = zksync_base_op.contract_call(call_data, dapp)
    except Exception as e:
        raise Exception(f"账户 {address} 交互 {dapp.name} 卖出操作时, 调用合约失败, 等待10秒后重试: {e}")

    return tx_hash

def interact_with_gemswap(zksync_base_op: ZkSyncBaseOp, address, dapp):
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
