import random
import time
import threading
import copy

import requests
import utils.my_logger as my_logger
from signers.signers import Signers
from utils.get_env import EnvKey
from utils.base_op import ZkSyncBaseOp
from database.db import Account, create_tables
from dapp.dapp_manager import assign_dapps_to_wallet
from interaction.interaction_manager import first_phase_interaction, second_phase_interaction
from interaction.multichain import interact_with_bridge
from dapp.dapp_list import cross_dapp
from eth_utils import to_checksum_address
from zksync2.module.module_builder import ZkSyncBuilder
from zksync2.signer.eth_signer import PrivateKeyEthSigner
from okx.Funding import FundingAPI
from web3 import Web3

main_info = my_logger.get_logger('main_info', 'logs/mainInfo.log')
main_error = my_logger.get_logger('main_error', 'logs/mainError.log')
okx_deposit_addr = my_logger.get_logger('okx_deposit_address', 'logs/okx_deposit_address.log')
fetch_proxy_log = my_logger.get_logger('fetch_proxy_log', 'logs/fetch_proxy.log')

# 为每个账户分配okx充值地址
def fetch_okx_deposit_addr(signers_list):
    # 遍历api_key
    for i in range(len(api_key)):
        fundingAPI = FundingAPI(api_key[i], secret_key[i], passphrase, False, flag, debug=False)
        results = fundingAPI.get_deposit_address("ETH")
        if results["code"] != "0":
            raise Exception(f"获取okx充币地址失败: {results['msg']}")
        data = results["data"]
        if len(data) == 0:
            raise Exception(f"okx充币地址返回数据为空: {results['data']}")
        count = 0
        for item in data:
            if item["ccy"] == "ETH" and item["chain"] == "ETH-Arbitrum one":
                index = 20 * i + count
                count += 1
                if index >= len(signers_list):
                    return True
                from_address = signers_list[index].address
                to_address = item["addr"]
                try:
                    account = Account.get_or_none(Account.address == from_address)
                    if account is None:
                        account = Account.create(address=from_address, proxy=None, deposit_okx_address=None, withdraw_from_okx=None, bridge_to_zk=None, bridge_to_arb=None, deposit_to_okx=None)
                        account.save()
                except Exception as e:
                    raise e
                
                try:
                    if account.deposit_okx_address is None:
                        account.deposit_okx_address = to_address
                        account.save()
                        okx_deposit_addr.info(f"序号: {index} 账户地址: {from_address}, okx充值地址: {to_address}")
                    else:
                        if account.deposit_okx_address != to_address:
                            raise Exception(f"当前分配地址与之前分配地址不同: {to_address}")
                except Exception as e:
                    raise e
    return True

# 读取proxy文件
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

# 为每个账户分配proxy
def fetch_proxy(signers_list, proxy_list):
    for i in range(len(signers_list)):
        try:
            account = Account.get_or_none(Account.address == signers_list[i].address)
            if account is None:
                raise Exception("账户不存在")
        except Exception as e:
            raise e
        if account.proxy is None:
            account.proxy = proxy_list[i]
            account.save()
            fetch_proxy_log.info(f"序号: {i} 账户地址: {signers_list[i].address}, proxy地址: {proxy_list[i]}")
        else:
            if account.proxy != proxy_list[i]:
                raise Exception("账户proxy不匹配")
    return True

# 创建zkSyncBaseOp对象
def create_zksync_base_op(signer, proxy, chain_id):
    """
    创建ZKSyncBaseOp对象

    Args:
        signer (Signer): Signer对象
        proxy (str): 代理地址

    Returns:
        ZKSyncBaseOp: ZKSyncBaseOp对象
    """
    # 初始化 zkSync 网络
    zk_web3 = ZkSyncBuilder.build(url=l2_rpc_url, proxy_url=proxy)
    # 创建ZKSyncBaseOp对象
    zksync_base_op = ZkSyncBaseOp(zk_web3, signer, chain_id)
    return zksync_base_op

# 预交互
def pre_interaction(zksync_base_op: ZkSyncBaseOp):
    # 查询数据库中accounts表中是否有该signer的记录
    try:
        account = Account.get_or_none(
            Account.address == zksync_base_op.signer.address)
        if account is None:
            raise Exception(f"account {zksync_base_op.signer.address} not exist")
    except Exception as e:
        raise e
    # 如果withdraw_from_okx不存在
    if account.withdraw_from_okx is None:
        while True:
            try:
                fundingAPI = FundingAPI(api_key[0], secret_key[0], passphrase, False, flag, debug=False)
                amount, wdId = withdraw_from_okx(zksync_base_op, fundingAPI)
                account.withdraw_from_okx = wdId + ":" + str(amount)
                account.save()
                main_info.info(f"从okx提现 {amount} 成功")
                break
            except Exception as e:
                main_error.error(f"从okx提现失败: {e}")
                main_info.info(f"从okx提现失败, 60s后重试...")
                time.sleep(60)
    else:
        main_info.info(f"已经提现过")
    # 如果bridge_to_zk不存在
    if account.bridge_to_zk is None:
        while True:
            try:
                eth_web3 = Web3(Web3.HTTPProvider(eth_rpc_url))
                break
            except Exception as e:
                main_error.error(f"连接以太坊节点失败: {e}")
                main_info.info(f"连接以太坊节点失败, 5s后重试...")
                time.sleep(5)

        # 持续查询gas price, 直到gas price小于 25 gwei
        while True:
            try:
                gas_price = eth_web3.eth.gas_price
            except Exception as e:
                main_error.error(f"查询gas price失败: {e}")
                main_info.info(f"查询gas price失败, 5s后重试...")
                time.sleep(5)
            if gas_price <= eth_web3.to_wei(30, "gwei"):
                main_info.info(f"gas price: {gas_price} 小于 30 gwei, 可以开始bridge to zk")
                break
            main_info.info(f"gas price: {gas_price}, 60s后重试...")
            time.sleep(60)

        while True:
            try:
                tx_hash = deposit_to_zksync(eth_web3, zksync_base_op)
                account.bridge_to_zk = tx_hash.hex()
                account.save()
                main_info.info(f"bridge to zk成功, tx_hash: {tx_hash.hex()}")
                break
            except Exception as e:
                main_error.error(f"bridge to zk失败: {e}")
                main_info.info(f"bridge to zk失败, 60s后重试...")
                time.sleep(60)
        # 等待  zksync 余额大于 0.5 ETH
        while True:
            try:
                eth_balance, wei_balance = zksync_base_op.get_eth_balance()
            except Exception as e:
                main_error.error(f"查询余额失败: {e}")
                main_info.info(f"查询余额失败, 60s后重试...")
                time.sleep(60)
            if wei_balance >= zksync_base_op.zk_web3.to_wei(0.5, "ether"):
                main_info.info(f"zksync余额: {wei_balance}, 可以开始交互")
                break
            main_info.info(f"zksync余额: {wei_balance}, 60s后重试...")
            time.sleep(60)
    else:
        main_info.info(f"已经bridge to zk过")

# 从okx提取资金
def withdraw_from_okx(zksync_base_op: ZkSyncBaseOp, fundingAPI: FundingAPI):
    main_info.info("开始从okx提现...")
    # 提现
    try:
        availBal, wdId = zksync_base_op.withdraw_from_okx(fundingAPI)
    except Exception as e:
        raise e
    while True:
        try:
            result = fundingAPI.get_withdrawal_history(wdId=wdId)
        except Exception as e:
            main_error.error(f"{wdId} 提现 {availBal} 异常: {e}")
            main_info.info(f"{wdId} 提现 {availBal} 异常, 60s后重试...")
            time.sleep(60)
            continue
        state = result["data"][0]["state"]
        if state == "2":
            return availBal, wdId
        elif state == "-1":
            raise Exception(f"{wdId} 提现 {availBal} 失败")
        else:
            main_info.info(f"{wdId} 提现 {availBal} 进行中, 等待1分钟...")
            time.sleep(60)

# 跨链到zksync
def deposit_to_zksync(eth_web3: Web3, zksync_base_op: ZkSyncBaseOp):
    try:
        tx_hash = zksync_base_op.deposit(eth_web3)
    except Exception as e:
        raise e
    while True:
        try:
            tx_receipt = eth_web3.eth.wait_for_transaction_receipt(tx_hash, timeout=240, poll_latency=0.5)
        except Exception as e:
            main_error.error(f"查询交易 {tx_hash} 回执失败: {e}")
            main_info.info(f"查询交易 {tx_hash} 回执失败, 60s后重试...")
            time.sleep(60)
            continue
        state = tx_receipt["status"]
        if state == 1:
            return tx_hash
        elif state == 0:
            raise Exception(f"交易 {tx_hash} 失败")

# 第一阶段交互
def perform_tasks(zksync_base_op: ZkSyncBaseOp):
    assign_dapps_to_wallet(zksync_base_op.signer.address)
    first_phase_interaction(zksync_base_op)

# 跨链到arb
def cross_to_arb(zksync_base_op: ZkSyncBaseOp):
    try:
        address = zksync_base_op.signer.address
        account = Account.get_or_none(Account.address == address)
    except Exception as e:
        raise e
    if account is None:
        raise Exception(f"账户 {address} 不存在")
    if account.bridge_to_arb not in [None, ""]:
        main_info.info(f"用户 {address} 已经跨链到arb")
        return
    while True:
        try:
            tx_hash = interact_with_bridge(
                zksync_base_op=zksync_base_op, address=address, dapp=cross_dapp)
        except Exception as e:
            main_error.error(f"账户 {address} 交互 {cross_dapp.name} 失败: {e}")
            main_info.info(f"账户 {address} 交互 {cross_dapp.name} 失败, 60s后重试...")
            time.sleep(60)
            continue

        if not tx_hash:
            print(f"账户 {address} 交互 {cross_dapp.name} 返回的交易哈希为空, 60s后重试...")
            time.sleep(60)
            continue

        account.bridge_to_arb = tx_hash
        account.save()

        # 随机等待1-5分钟
        time.sleep(random.randint(60, 300))
        # 注册arb交易哈希到multichain
        register_tx_hash_to_multichain(address=address, tx_hash=tx_hash)
        break

def register_tx_hash_to_multichain(address, tx_hash: str):
    url = "https://scanapi.multichain.org/v2/reswaptxns"
    params = {
        "hash": tx_hash,
        "srcChainID": 324,
        "destChainID": 42161
    }
    # 查询数据库, 获取proxy
    try:
        account = Account.get_or_none(Account.address == address)
    except Exception as e:
        raise e
    if account is None:
        raise Exception(f"账户 {address} 不存在")
    if account.proxy is None:
        raise Exception(f"账户 {address} 代理不存在")
    
    proxies = {
        "http": account.proxy,
        "https": account.proxy
    }
    
    while True:
        try:
            response = requests.get(url=url, params=params, proxies=proxies)
            if response.status_code == 200:
                main_info.info(f"账户 {address} 注册arb交易哈希 {tx_hash} 到multichain成功: {response.json()}")
                break
            else:
                raise Exception(f"注册arb交易哈希到multichain失败, 状态码: {response.status_code}")
        except Exception as e:
            main_error.error(f"账户 {address} 注册arb交易哈希到multichain失败: {e}")
            main_info.info(f"账户 {address} 注册arb交易哈希到multichain失败, 60s后重试...")
            time.sleep(60)
            continue

# 第二阶段交互线程
def second_phase_interaction_thread(zksync_base_op: ZkSyncBaseOp):
    while True:
        try:
            second_phase_interaction(zksync_base_op)
            break
        except Exception as e:
            main_error.error(f"账户 {zksync_base_op.signer.address} 第二阶段交互失败: {e}")
            main_info.info(f"账户 {zksync_base_op.signer.address} 第二阶段交互失败, 60s后重试...")
            time.sleep(60)
            continue

# 充币到okx线程
def deposit_to_okx_thread(arb_web3: Web3, signer: PrivateKeyEthSigner):
    isErr = False
    while True:
        try:
            # 随机等待10分钟到2小时
            if isErr == False:
                random_time = random.randint(600, 7200)
                main_info.info(f"账户 {signer.address} 随机等待 {random_time} 秒")
                time.sleep(random_time)
            main_info.info(f"账户 {signer.address} 开始执行提取到交易所")
            deposit_to_okx(arb_web3, signer)
            main_info.info(f"账户 {signer.address} 提取到交易所完成")
            break
        except Exception as e:
            isErr = True
            main_error.error(f"账户 {signer.address} 提取到交易所失败: {e}")
            main_info.info(f"账户 {signer.address} 提取到交易所失败, 60s后重试...")
            time.sleep(60)
            continue

def deposit_to_okx(arb_web3: Web3, signer: PrivateKeyEthSigner):
    # 获取address的deposit_okx_address
    address = signer.address
    try:
        account = Account.get_or_none(Account.address == address)
        if account is None:
            raise Exception("账户不存在")
    except Exception as e:
        raise e
    if account.deposit_to_okx is not None:
        main_info.info(f"账户 {address} 已经提取到交易所")
        return
    if account.deposit_okx_address is None:
        raise Exception("账户没有设置提取地址")
    # 获取address的balance
    while True:
        balance = arb_web3.eth.get_balance(address)
        balance_limit = arb_web3.to_wei(0.05, "ether")
        if balance < balance_limit:
            print(f"账户 {address} 余额 {balance} 不足, 60s后重试...")
            time.sleep(60)
            continue
        break
    # 获取address的nonce
    nonce = arb_web3.eth.get_transaction_count(address)
    # 获取gasPrice
    gasPrice = arb_web3.eth.gas_price
    # to address
    to_address = to_checksum_address(account.deposit_okx_address)
    # 构造交易
    tx = {
        "to": to_address,
        "value": balance,
        "gasPrice": gasPrice,
        "chainId": arb_web3.eth.chain_id,
        "nonce": nonce
    }
    # estimate gas
    try:
        gas = arb_web3.eth.estimate_gas(tx)
    except Exception as e:
        raise e
    # cost
    cost = gas * gasPrice
    tx["gas"] = gas
    tx["value"] = balance - cost
    # 签名交易
    signed_message = signer.credentials.sign_transaction(tx)
    # 发送交易
    while True:
        try:
            tx_hash = arb_web3.eth.send_raw_transaction(
                signed_message.rawTransaction)
            # 等待交易确认
            while True:
                try:
                    receipt = arb_web3.eth.wait_for_transaction_receipt(tx_hash, timeout=240, poll_latency=0.5)
                except Exception as e:
                    main_error.error(f"账户 {address} 提取到交易所失败: {e}")
                    main_info.info(f"账户 {address} 提取到交易所失败, 60s后重试...")
                    time.sleep(60)
                    continue
                if receipt["status"] == 1:
                    account.deposit_to_okx = tx_hash.hex()
                    account.save()
                    return
                raise Exception(f"账户 {address} arb提取到okx交易所交易失败")
        except Exception as e:
            raise e

proxy = "http://wukong01-zone-resi:li123123@pr.pyproxy.com:16666"
arb_rpc_url = EnvKey("ARB_MAIN_URL").key
eth_rpc_url = EnvKey("ETH_MAIN_URL").key
l2_rpc_url = EnvKey("ZKSYNC_MAIN_URL").key
mnemonic_words = EnvKey("MNEMONIC").key
api_key = EnvKey("api_key").key.split(",")
secret_key = EnvKey("secret_key").key.split(",")
passphrase = EnvKey("passphrase").key
flag = "0"

# main
if __name__ == "__main__":
    # 初始化
    main_info.info("初始化数据库")
    create_tables()
    main_info.info("初始化网络实例")
    eth_web3 = Web3(Web3.HTTPProvider(eth_rpc_url))
    main_info.info("ETH Network: {}".format(eth_rpc_url))
    arb_web3 = Web3(Web3.HTTPProvider(arb_rpc_url))
    main_info.info("ARB Network: {}".format(arb_rpc_url))
    zk_web3 = ZkSyncBuilder.build(url=l2_rpc_url, proxy_url=proxy)
    main_info.info("zkSync Network: {}".format(l2_rpc_url))
    chain_id = zk_web3.zksync.chain_id
    main_info.info("获取链ID: {}".format(chain_id))
    # 初始化 Signers 类
    index = 3
    numbers = 2
    signers = Signers(mnemonic_words, index, numbers, chain_id)
    main_info.info(f"初始化Signers, 使用助记词从index: {index} 开始, 生成 {numbers} 个账户")
    # 获取signers列表
    signers_list = signers.get_signers
    # 为每个账户地址分配okx充币地址
    try:
        main_info.info("为每个账户地址分配okx充币地址")
        fetch_okx_deposit_addr(signers_list)
    except Exception as e:
        main_error.error("分配okx地址错误: ")
        raise e
    # 读取文件中的proxy地址
    try:
        main_info.info("读取proxy.txt")
        proxy_list = read_file_lines_to_array("proxy.txt")
    except Exception as e:
        main_error.error("读取proxy.txt错误: ")
        raise e
    # 为每个账户分配proxy
    try:
        main_info.info("为每个账户分配proxy")
        fetch_proxy(signers_list, proxy_list)
    except Exception as e:
        main_error.error("分配proxy错误: ")
        raise e

    threads = []
    for i in range(len(signers_list)):
        signer = signers_list[i]
        proxy = proxy_list[i]
        main_info.info(f"账户 {signer.address} 使用 {proxy} 代理开始执行")
        main_info.info(f"账户 {signer.address} 创建zksync_base_op实例")
        try:
            zksync_base_op = create_zksync_base_op(signers_list[i], proxy_list[i], chain_id)
        except Exception as e:
            main_error.error(f"账户 {signer.address} 创建zksync_base_op实例错误: ")
            raise e
        # 预交互
        while True:
            try:
                main_info.info(f"账户 {signer.address} 开始执行预交互")
                pre_interaction(zksync_base_op)
                main_info.info(f"账户 {signer.address} 预交互完成")
                break
            except Exception as e:
                main_error.error(f"账户 {signer.address} 执行预交互失败: {e}")
                main_info.info(f"账户 {signer.address} 执行预交互失败, 60s后重试...")
                time.sleep(60)
                continue
        # 第一阶段交互
        while True:
            try:
                main_info.info(f"账户 {signer.address} 开始执行第一阶段交互")
                perform_tasks(zksync_base_op)
                main_info.info(f"账户 {signer.address} 第一阶段交互完成")
                break
            except Exception as e:
                main_error.error(f"账户 {signer.address} 执行第一阶段交互失败: {e}")
                main_info.info(f"账户 {signer.address} 执行第一阶段交互失败, 60s后重试...")
                time.sleep(60)
                continue
        # 跨链到arb
        while True:
            try:
                main_info.info(f"账户 {signer.address} 开始执行跨链到arb")
                cross_to_arb(zksync_base_op)
                main_info.info(f"账户 {signer.address} 跨链到arb完成")
                break
            except Exception as e:
                main_error.error(f"账户 {signer.address} 跨链到arb失败: {e}")
                main_info.info(f"账户 {signer.address} 跨链到arb失败, 60s后重试...")
                time.sleep(60)
                continue
        # 提取到交易所
        while True:
            try:
                signer_copy = signer.copy()
                thread = threading.Thread(target=deposit_to_okx_thread, args=(arb_web3, signer_copy))
                thread.start()
                threads.append(thread)
                break
            except Exception as e:
                main_error.error(f"账户 {signer.address} 充值到okx交易线程创建失败: {e}")
                main_info.info(f"账户 {signer.address} 充值到okx交易线程创建失败, 60s后重试...")
                time.sleep(60)
                continue
        # 第二阶段交互
        while True:
            try:
                zksync_base_op_copy = zksync_base_op.copy()
                thread = threading.Thread(target=second_phase_interaction_thread, args=(zksync_base_op_copy,))
                thread.start()
                threads.append(thread)
                break
            except Exception as e:
                main_error.error(f"账户 {signer.address} 第二阶段交互线程创建失败: {e}")
                main_info.info(f"账户 {signer.address} 第二阶段交互线程创建失败, 60s后重试...")
                time.sleep(60)
                continue
    for thread in threads:
        thread.join()
