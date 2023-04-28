import random
import time

from utils.base_op import ZkSyncBaseOp
from zksync2.manage_contracts.contract_encoder_base import BaseContractEncoder

with open("interaction/abi/multichain.json", "r") as f:
    contract_abi = f.read()

contract_address = "0xff7104537F33937c66Ac0a65609EB8364Be75c7A"

def bridge(zksync_base_op: ZkSyncBaseOp, address, dapp):
    # 获取当前账户的 ETH 余额
    while True:
        try:
            eth_balance, wei_balance = zksync_base_op.get_eth_balance()
            break
        except Exception as e:
            print(f"账户 {address} 交互 {dapp.name} 跨链操作时, 获取ETH余额错误, 等待10秒后重试: {e}")
            time.sleep(10)
    # 随机生成0.01-0.02之间的ETH数量, 作为手续费
    eth_amount = random.uniform(0.01, 0.02)
    print(f"账户 {address} 交互 {dapp.name} 跨链操作时, 预留的ETH数量为: {eth_amount}")
    amount_in = wei_balance - zksync_base_op.zk_web3.to_wei(eth_amount, "ether")
    if amount_in < zksync_base_op.zk_web3.to_wei(0.005, "ether"):
        raise Exception(f"账户 {address} 交互 {dapp.name} 跨链操作时, ETH余额不足, 无法购买")
    # 实例化encoder
    contract_encoder = BaseContractEncoder(zksync_base_op.zk_web3, contract_abi)
    # params
    anyswap_v6_erc20_address = "0x7BcD44c0B91bE28827426f607424E1A8A02d4E69"
    recepient = str(address)
    to_chain_id = 42161
    bridge_params = (anyswap_v6_erc20_address, recepient, to_chain_id)
    # Encode arguments
    call_data = contract_encoder.encode_method("anySwapOutNative", args=bridge_params)
    try:
        tx_hash = zksync_base_op.contract_call(call_data, dapp, value=amount_in)
    except Exception as e:
        raise Exception(f"账户 {address} 执行 {dapp.name} 跨链交易失败: {e}")

    return tx_hash

def interact_with_bridge(zksync_base_op: ZkSyncBaseOp, address, dapp):
    # bridge
    while True:
        try:
            bridge_tx_hash = bridge(zksync_base_op, address, dapp)
        except Exception as e:
            print(f"账户 {address} 交互 {dapp.name} 跨链操作时, 调用bridge失败, 等待10秒后重试: {e}")
            time.sleep(10)
            continue

        try:
            while True:
                try:
                    # Wait for transaction to be included in a block
                    tx_receipt = zksync_base_op.zk_web3.zksync.wait_for_transaction_receipt(
                        bridge_tx_hash, timeout=240, poll_latency=0.5
                    )
                except Exception as e:
                    print(f"账户 {address} 等待 {dapp.name} 跨链交易 {bridge_tx_hash.hex()} 被打包时错误, 10秒后重试: {e}")
                    # 等待10秒后重试
                    time.sleep(10)
                    continue

                if tx_receipt['status'] != 1:
                    raise Exception(f"账户 {address} 执行 {dapp.name} 跨链交易 {bridge_tx_hash.hex()} 失败")
                print(f"账户 {address} 执行 {dapp.name} 跨链交易 {bridge_tx_hash.hex()} 成功")
                return tx_receipt['transactionHash'].hex()
        except Exception as e:
            print(f"10秒后重试: {e}")
            time.sleep(10)
            continue