import random
import time

from utils.base_op import ZkSyncBaseOp
from zksync2.manage_contracts.contract_encoder_base import BaseContractEncoder

with open("interaction/abi/nexon.json", "r") as f:
    contract_abi = f.read()

contract_address = "0x1BbD33384869b30A323e15868Ce46013C82B86FB"

def mint(zksync_base_op: ZkSyncBaseOp, address, dapp):
    # 获取当前账户的 ETH 余额
    while True:
        try:
            eth_balance, wei_balance = zksync_base_op.get_eth_balance()
            break
        except Exception as e:
            print(f"账户 {address} 交互 {dapp.name} mint操作时, 获取ETH余额错误, 等待10秒后重试: {e}")
            time.sleep(10)
    # 随机生成0.01-0.2之间的ETH数量, 作为手续费
    eth_amount = random.uniform(0.01, 0.2)
    amount_fee = zksync_base_op.zk_web3.to_wei(eth_amount, "ether")
    amount_fee = amount_fee if amount_fee < wei_balance else zksync_base_op.zk_web3.to_wei(0.001, "ether")
    amount_in = wei_balance - amount_fee
    if amount_in < 1:
        raise Exception(f"账户 {address} 交互 {dapp.name} mint操作时, ETH余额不足, 无法购买")
    # 获取合约实例
    contract = zksync_base_op.get_contract_instance(contract_address, contract_abi)
    # 实例化encoder
    contract_encoder = BaseContractEncoder(zksync_base_op.zk_web3, contract_abi)
    # Encode arguments
    call_data = contract_encoder.encode_method("mint", args=())
    try:
        tx_hash = zksync_base_op.contract_call(call_data, dapp, value=amount_in)
    except Exception as e:
        raise Exception(f"账户 {address} 交互 {dapp.name} mint操作时, 调用合约错误: {e}")

    return tx_hash

def redeem(zksync_base_op: ZkSyncBaseOp, address, dapp):
    # 获取当前账户的 nETH 余额
    while True:
        try:
            neth_balance, neth_wei_balance = zksync_base_op.get_erc20_balance(contract_address)
            if neth_wei_balance > 0:
                break
        except Exception as e:
            print(f"账户 {address} 交互 {dapp.name} redeem操作时, 获取nETH余额错误, 等待10秒后重试: {e}")
            time.sleep(10)
    # 获取合约实例
    contract = zksync_base_op.get_contract_instance(contract_address, contract_abi)
    amount_in = neth_wei_balance
    # 实例化encoder
    contract_encoder = BaseContractEncoder(zksync_base_op.zk_web3, contract_abi)
    # 取回 参数
    redeem_params = (amount_in,)
    # Encode arguments
    call_data = contract_encoder.encode_method("redeem", args=redeem_params)
    try:
        tx_hash = zksync_base_op.contract_call(call_data, dapp)
    except Exception as e:
        raise Exception(f"账户 {address} 交互 {dapp.name} redeem操作时, 调用合约错误: {e}")

    return tx_hash

def interact_with_nexon(zksync_base_op: ZkSyncBaseOp, address, dapp):
    # mint
    while True:
        try:
            mint_tx_hash = mint(zksync_base_op, address, dapp)
        except Exception as e:
            print(f"账户 {address} 执行 {dapp.name} mint交易失败, 10秒后重试: {e}")
            time.sleep(10)
            continue

        try:
            while True:
                try:
                    # Wait for transaction to be included in a block
                    tx_receipt = zksync_base_op.zk_web3.zksync.wait_for_transaction_receipt(
                        mint_tx_hash, timeout=240, poll_latency=0.5
                    )
                except Exception as e:
                    print(f"等待账户 {address} 执行 {dapp.name} mint交易 {mint_tx_hash.hex()} 被打包时错误, 10秒后重试: {e}")
                    time.sleep(10)
                    continue

                if tx_receipt['status'] != 1:
                    raise Exception(f"账户 {address} 执行 {dapp.name} mint交易 {mint_tx_hash.hex()} 失败")
                print(f"账户 {address} 执行 {dapp.name} mint交易 {mint_tx_hash.hex()} 成功")
                break
        except Exception as e:
            print(f"10秒后重试: {e}")
            time.sleep(10)
            continue
        break
    
    # redeem
    while True:
        try:
            redeem_tx_hash = redeem(zksync_base_op, address, dapp)
        except Exception as e:
            print(f"账户 {address} 执行 {dapp.name} redeem交易失败, 10秒后重试: {e}")
            time.sleep(10)
            continue
    
        try:
            while True:
                try:
                    # Wait for transaction to be included in a block
                    tx_receipt = zksync_base_op.zk_web3.zksync.wait_for_transaction_receipt(
                        redeem_tx_hash, timeout=240, poll_latency=0.5
                    )
                except Exception as e:
                    print(f"等待账户 {address} 执行 {dapp.name} redeem交易 {redeem_tx_hash.hex()} 被打包时错误, 10秒后重试: {e}")
                    # 等待10秒后重试
                    time.sleep(10)
                    continue

                if tx_receipt['status'] != 1:
                    raise Exception(f"账户 {address} 执行 {dapp.name} redeem交易 {redeem_tx_hash.hex()} 失败")
                print(f"账户 {address} 执行 {dapp.name} redeem交易 {redeem_tx_hash.hex()} 成功")
                return tx_receipt['transactionHash'].hex()
        except Exception as e:
            print(f"10秒后重试: {e}")
            time.sleep(10)
            continue