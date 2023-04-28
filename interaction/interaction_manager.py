import random
import time
from random import randint
from database.db import Account, AccountDapp, create_tables, close_db
from utils.base_op import ZkSyncBaseOp
from interaction.muteswap import interact_with_mute
from interaction.syncswap import interact_with_syncswap
from interaction.spacefi import interact_with_spacefi
from interaction.nexon import interact_with_nexon
from interaction.velocore import interact_with_velocore
from interaction.izumi import interact_with_izumi
from interaction.gemswap import interact_with_gemswap

def interact_with_dapp(zksync_base_op: ZkSyncBaseOp, dapp):
    address = zksync_base_op.signer.address
    # 根据 DApp 名称执行相应的交互函数
    print(f"账户 {address} 开始交互 {dapp.name}")
    if dapp.name == 'mute':
        return interact_with_mute(zksync_base_op, address, dapp)
    if dapp.name == 'syncswap':
        return interact_with_syncswap(zksync_base_op, address, dapp)
    if dapp.name == 'spacefi':
        return interact_with_spacefi(zksync_base_op, address, dapp)
    if dapp.name == 'nexon':
        return interact_with_nexon(zksync_base_op, address, dapp)
    if dapp.name == 'velocore':
        return interact_with_velocore(zksync_base_op, address, dapp)
    if dapp.name == 'izumi':
        return interact_with_izumi(zksync_base_op, address, dapp)
    if dapp.name == 'gemswap':
        return interact_with_gemswap(zksync_base_op, address, dapp)

def update_account_dapp_hash(address, dapp_name, tx_hash):
    dapp = AccountDapp.get(AccountDapp.address == address,
                           AccountDapp.name == dapp_name)
    dapp.hash = tx_hash
    dapp.save()


def first_phase_interaction(zksync_base_op: ZkSyncBaseOp):
    address = zksync_base_op.signer.address
    while True:
        assigned_dapps = AccountDapp.select().where(AccountDapp.address == address)
        # 如果所有的DApp都已经交互过，就退出循环
        if all(dapp.hash for dapp in assigned_dapps):
            break

        for dapp in assigned_dapps:
            if not dapp.hash:
                try:
                    tx_hash = interact_with_dapp(zksync_base_op, dapp)
                except Exception as e:
                    print(f"账户 {address} 交互 {dapp.name} 失败, 开始交互下一个DApp: {str(e)}")
                    continue

                if not tx_hash:
                    print(f"账户 {address} 交互 {dapp.name} 返回的交易哈希为空, 开始交互下一个DApp")
                    continue

                # 更新account_dapps表中的hash字段，表示钱包已经与这个DApp交互过
                try:
                    update_account_dapp_hash(address, dapp.name, tx_hash)
                except Exception as e:
                    raise Exception(f"账户 {address} 更新 与 {dapp.name} 交互的交易哈希 {tx_hash} 失败: {str(e)}")

                # 设置随机等待时间 (1分钟到2小时)
                wait_time = random.uniform(1 * 60, 2 * 60 * 60)
                print(f"账户 {address} 交互 {dapp.name} 成功, 等待 {wait_time} 秒后开始交互下一个DApp")
                time.sleep(wait_time)


def second_phase_interaction(zksync_base_op: ZkSyncBaseOp):
    address = zksync_base_op.signer.address
    assigned_dapps = AccountDapp.select().where(AccountDapp.address == address).where(AccountDapp.name != 'ens')
    while True:
        try:
            eth_balance, wei_balance = zksync_base_op.get_eth_balance()
            if wei_balance < zksync_base_op.zk_web3.to_wei('0.0055', 'ether'):
                print(f"账户 {address} ETH余额少于0.0055 ETH, 停止交互")
                break
        except Exception as e:
            print(f"账户 {address} 获取ETH余额失败, 10s后重试: {str(e)}")
            time.sleep(10)

        random_index = randint(0, len(assigned_dapps) - 1)
        dapp = assigned_dapps[random_index]

        # 设置随机等待1到15天, 小数点后保留两位
        wait_time = random.uniform(1, 15)
        print(f"等待 {wait_time} 天后开始交互下一个DApp")
        time.sleep(wait_time * 24 * 60 * 60)

        try:
            tx_hash = interact_with_dapp(zksync_base_op, dapp)
        except Exception as e:
            print(f"账户 {address} 交互 {dapp.name} 失败, 10s后开始交互下一个DApp: {str(e)}")
            time.sleep(10)
            continue

        if not tx_hash:
            print(f"账户 {address} 交互 {dapp.name} 返回的交易哈希为空, 10s后开始交互下一个DApp")
            time.sleep(10)
            continue

        print(f"账户 {address} 交互 {dapp.name} 成功")


    print(f"账户 {address} 交互结束")