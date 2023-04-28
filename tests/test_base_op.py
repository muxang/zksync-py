import sys_path
from eth_utils import to_checksum_address
from signers.signers import Signers
from utils.get_env import EnvMnemonicKey
from utils.base_op import ZkSyncBaseOp
from web3 import Web3
from web3_proxy_providers import HttpWithProxyProvider

# Test ZkSyncBaseOp class
def test_zksync_base_op():
    # Create a mock signer
    mnemonic_words = EnvMnemonicKey("ZKSYNC_TEST_MNEMONIC")
    index_start = 3
    number = 1
    chain_id = 280
    signers = Signers(mnemonic_words.mnemonic, index_start, number, chain_id)
    signers_list = signers.get_signers

    l2_rpc_url = "https://zksync2-testnet.zksync.dev"
    proxy = "http://wukong01-zone-resi:li123123@pr.pyproxy.com:16666"

    # Create an instance of ZkSyncBaseOp
    zk_sync_base_op = ZkSyncBaseOp(l2_rpc_url, proxy, signers_list[0])

    # Test deposit() method
    ETH_TEST_URL = "https://rpc.ankr.com/eth_goerli"
    provider = HttpWithProxyProvider(endpoint_uri=ETH_TEST_URL, proxy_url=proxy)
    amount = 0.1
    eth_web3 = Web3(provider)
    tx_hash = zk_sync_base_op.deposit(eth_web3, amount)
    print(f"Deposit Transaction Hash: {tx_hash.hex()}")
    tx_receipt = eth_web3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Deposit Transaction Receipt: {tx_receipt['status']}")

    # Test get_eth_balance() method
    while True:
        eth_balance = zk_sync_base_op.get_eth_balance()
        if eth_balance > 0:
            print(f"ETH Balance: {eth_balance}")
            break

    # Test transfer_eth() method
    amount = 0.01
    print(f"Transfer ETH to: {signers_list[0].address}")
    to = to_checksum_address(signers_list[0].address)
    tx_hash = zk_sync_base_op.transfer_eth(to, amount)
    print(f"ETH Transfer Transaction Hash: {tx_hash.hex()}")
    tx_receipt = zk_sync_base_op.zk_web3.zksync.wait_for_transaction_receipt(tx_hash)
    print(f"ETH Transfer Transaction Receipt: {tx_receipt['status']}")

    # Test get_erc20_balance() method
    contract_address = "0x0faF6df7054946141266420b43783387A78d82A9"
    erc20_balance = zk_sync_base_op.get_erc20_balance(contract_address)
    print(f"ERC20 Balance: {erc20_balance}")

    # Test transfer_erc20() method
    amount = 100
    tx_hash = zk_sync_base_op.transfer_erc20(to, amount, contract_address)
    print(f"ERC20 Transfer Transaction Hash: {tx_hash.hex()}")
    tx_receipt = zk_sync_base_op.zk_web3.zksync.wait_for_transaction_receipt(tx_hash)
    print(f"ERC20 Transfer Transaction Receipt: {tx_receipt['status']}")

# Run the test
test_zksync_base_op()
