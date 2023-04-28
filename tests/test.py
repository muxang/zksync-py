import random
from time import sleep
from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3
from web3_proxy_providers import HttpWithProxyProvider

import sys_path
from utils.get_env import EnvPrivateKey
from zksync2.core.types import Token, EthBlockParams
from zksync2.module.module_builder import ZkSyncBuilder
from zksync2.provider.eth_provider import EthereumProvider

ZKSYNC_TEST_URL = "https://zksync2-testnet.zksync.dev"
ETH_TEST_URL = "https://rpc.ankr.com/eth_goerli"
# ETH_MAIN_URL = "https://nd-002-127-980.p2pify.com/ba74b64c9df4d653894b356c0323d4c5"
# ETH_MAIN_URL = "https://eth-mainnet.g.alchemy.com/v2/0CRhhUjcQkKvnp8A5VPs_A3OcJC5GHkd"

proxy = "http://wukong01-zone-resi:li123123@pr.pyproxy.com:16666"

import dapp.dapp_manager as dapp_manager

def deposit(amount: float):
    env = EnvPrivateKey("ZKSYNC_TEST_KEY")
    zksync = ZkSyncBuilder.build(ZKSYNC_TEST_URL, proxy_url=proxy)
    provider = HttpWithProxyProvider(endpoint_uri=ETH_TEST_URL, proxy_url=proxy)
    eth_web3 = Web3(provider)
    account: LocalAccount = Account.from_key(env.key)
    eth_provider = EthereumProvider(zksync, eth_web3, account)
    wei_amount = Web3.to_wei(amount, "ether")
    eth_token = Token.create_eth()
    before_deposit = eth_provider.get_l1_balance(eth_token, EthBlockParams.LATEST)
    print(f"Before: {before_deposit}")
    # 随机生成700000-800000之间的数
    l2_gas_limit = 700000 + int(random.random() * 100000)
    return
    l1_tx_hash = eth_provider.deposit(token=Token.create_eth(), amount=before_deposit, l2_gas_limit=l2_gas_limit)
    print(f"Tx hash: {l1_tx_hash.hex()}")
    # TODO: when L2 tx

    after = eth_provider.get_l1_balance(eth_token, EthBlockParams.LATEST)
    print(f"After : {after}")


if __name__ == "__main__":
    deposit(0.1)
