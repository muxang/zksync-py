import os
import sys_path
from interaction.constent import ETH_ADDRESS, USDC_ADDRESS, SYNC_ROUTER_ADDRESS, SYNC_POOL_ADDRESS, SYNC_BUY_DATA, SYNC_SELL_DATA, SYNC_POOL_ABI, ERC20_ABI
from decimal import Decimal
from web3 import Web3

from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_typing import HexStr, HexAddress

from zksync2.core.types import ZkBlockParams
from zksync2.manage_contracts.erc20_contract import ERC20ContractWrite, ERC20ContractRead, ERC20Encoder, _erc_20_abi_default
from zksync2.module.module_builder import ZkSyncBuilder
from zksync2.signer.eth_signer import PrivateKeyEthSigner
from zksync2.transaction.transaction_builders import TxFunctionCall

from utils.get_env import EnvPrivateKey

# Byte-format private key
env = EnvPrivateKey("ZKSYNC_TEST_KEY")
PRIVATE_KEY = env.key


def get_erc20_balance(
    zk_web3: ZkSyncBuilder,
    address: HexAddress,
    contract_address: HexAddress,
    abi
) -> float:
    """
    Get ERC20 balance of ETH address on zkSync network

    :param zk_web3:
        Instance of ZkSyncBuilder that interacts with zkSync network

    :param address:
        ETH address that you want to get ERC-20 balance of.

    :param contract_address:
        ETH address that you want to get ERC-20 balance of.

    :return:
        ERC20 formated balance of the requested address
    """

    # Get readable contract instance
    contract = ERC20ContractRead(
        web3=zk_web3.zksync, contract_address=contract_address, abi=abi
    )

    # Get decimals of the contract
    contract_decimals = contract.decimals()

    # Query contract's balance
    erc20_balance = contract.balance_of(address)

    # Return Formated Balance
    return float(Decimal(erc20_balance) / Decimal(10) ** contract_decimals)


def transfer_erc20(
    zk_web3: ZkSyncBuilder,
    account: LocalAccount,
    to: HexAddress,
    contract_address: HexAddress,
    amount: int,
) -> HexStr:
    """
    Transfer ERC20 token to a specific address on zkSync network

    :param zk_web3:
        Instance of ZkSyncBuilder that interacts with zkSync network.

    :param account:
        From which account the transfer will be made.

    :param to:
        ETH address that you want to transfer tokens to.

    :param contract_address:
        ERC-20 contract address that the transfer will be made within.

    :param amount:
        ERC-20 token amount to be sent.

    :return:
        The transaction hash of the deposit transaction.
    """

    # Get chain id of zkSync network
    chain_id = zk_web3.zksync.chain_id

    # Signer is used to generate signature of provided transaction
    signer = PrivateKeyEthSigner(account, chain_id)

    # Get current gas price in Wei
    gas_price = zk_web3.zksync.gas_price

    # Get nonce of ETH address on zkSync network
    nonce = zk_web3.zksync.get_transaction_count(
        account.address, ZkBlockParams.COMMITTED.value
    )

    erc20_encoder = ERC20Encoder(zk_web3)

    # Transfer parameters
    transfer_params = (to, amount)

    # Encode arguments
    call_data = erc20_encoder.encode_method("transfer", args=transfer_params)

    # Create transaction
    func_call = TxFunctionCall(
        chain_id=chain_id,
        nonce=nonce,
        from_=account.address,
        to=contract_address,
        data=call_data,
        gas_limit=0,  # UNKNOWN AT THIS STATE
        gas_price=gas_price,
        max_priority_fee_per_gas=gas_price,
    )

    # ZkSync transaction gas estimation
    estimate_gas = zk_web3.zksync.eth_estimate_gas(func_call.tx)
    print(f"Fee for transaction is: {estimate_gas * gas_price}")

    # Convert transaction to EIP-712 format
    tx_712 = func_call.tx712(estimated_gas=estimate_gas)
    print(f"Tx 712 : {tx_712}")

    # Sign message & encode it
    signed_message = signer.sign_typed_data(tx_712.to_eip712_struct())
    print(f"Signed tx 712 : {signed_message}")

    # Encode signed message
    msg = tx_712.encode(signed_message)
    print(f"Msg  : {msg}")

    # Transfer ERC-20 token
    tx_hash = zk_web3.zksync.send_raw_transaction(msg)

    print(f"Tx hash: {tx_hash.hex()}")

    # Wait for transaction to be included in a block
    tx_receipt = zk_web3.zksync.wait_for_transaction_receipt(
        tx_hash, timeout=240, poll_latency=0.5
    )
    print(f"Tx status: {tx_receipt['status']}")
    print(f"Tx hash: {tx_receipt['transactionHash'].hex()}")


syncPoolABI = [
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_tokenIn",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "_amountIn",
                "type": "uint256"
            },
            {
                "internalType": "address",
                "name": "_sender",
                "type": "address"
            }
        ],
        "name": "getAmountOut",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "_amountOut",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "_reserve0",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "_reserve1",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getProtocolFee",
        "outputs": [
            {
                "internalType": "uint24",
                "name": "_protocolFee",
                "type": "uint24"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]


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


if __name__ == "__main__":
    # Some ERC20 Address
    ETH_Address = "0x5AEa5775959fBC2557Cc8789bC1bf90A239D9a91"
    USDC_Address = "0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4"
    sync_pool = "0x80115c708E12eDd42E504c1cD52Aea96C547c05c"
    proxy = "http://wukong01-zone-resi:li123123@pr.pyproxy.com:16666"

    # url = "https://zksync2-testnet.zksync.dev"
    url = "https://mainnet.era.zksync.io"

    # Connect to zkSync provider
    zk_web3 = ZkSyncBuilder.build(url=url, proxy_url=proxy)

    with open("interaction/abi/izumi_quoter.json", "r") as f:
        contract_abi = f.read()

    contract_address = "0x377EC7c9ae5a0787F384668788a1654249059dD6"

    contract = zk_web3.zksync.contract(
        address=contract_address, abi=contract_abi)

    token_in_address = ETH_ADDRESS
    token_out_address = USDC_ADDRESS
    print(fee2hex(2000))
    path = bytes.fromhex(
        token_in_address[2:] + fee2hex(2000)[2:] + token_out_address[2:])
    # pathHex = token_in_address[2:] + fee2hex(2000) + token_out_address

    print(path)

    amount, other = contract.functions.swapAmount(1000000000000000000, path).call(
        {
            "chainId": zk_web3.zksync.chain_id,
        }
    )

    print(amount)
    print(other)

    with open("interaction/abi/spacefi_router.json", "r") as f:
        contract_abi = f.read()
    contract_address = "0xbE7D1FD1f6748bbDefC4fbaCafBb11C6Fc506d1d"
    contract = zk_web3.zksync.contract(
        address=contract_address, abi=contract_abi)
    token_in_address = ETH_ADDRESS
    token_out_address = USDC_ADDRESS
    path = [token_in_address, token_out_address]
    amount_out = contract.functions.getAmountsOut(1000000000000000000, [token_in_address,token_out_address]).call()
    print(amount_out[1])

    exit()

    # Get account object by providing byte-format private key
    account: LocalAccount = Account.from_key(PRIVATE_KEY)

    # print(
    #     f"ERC-20 Balance before transfer : {get_erc20_balance(zk_web3=zk_web3, address=account.address, contract_address=USDC_Address, abi=_erc_20_abi_default())}"
    # )

    # Perform ERC-20 transfer
    # transfer_erc20(
    #     zk_web3=zk_web3,
    #     account=account,
    #     to="0xA1a1Ce05bc6616B177ce1CA2B292A2F933723fe3",
    #     contract_address=SERC20_Address,
    #     amount=100000000,
    # )

    # print(
    #     f"ERC-20 Balance after transfer : {get_erc20_balance(zk_web3=zk_web3, address=account.address, contract_address=SERC20_Address, abi=_erc_20_abi_default())}"
    # )

    contract = zk_web3.zksync.contract(address=sync_pool, abi=syncPoolABI)
    # fee = contract.functions.getProtocolFee().call(
    #     {
    #         "chainId": zk_web3.zksync.chain_id,
    #     }
    # )
    # print(fee)
    # reverses = contract.functions.getReserves().call(
    #     {
    #         "chainId": zk_web3.zksync.chain_id,
    #     }
    # )
    # print(reverses)
    # print(ETH_Address)
    # print(account.address)
    amountout = contract.functions.getAmountOut(USDC_Address, zk_web3.to_wei("1866", "mwei"), account.address).call(
        {
            "chainId": zk_web3.zksync.chain_id,
        }
    )
    print(amountout)
    print(ERC20_ABI)
    erc20_contract = zk_web3.zksync.contract(
        address=USDC_ADDRESS, abi=ERC20_ABI)
    # 获取approve函数的callData
    approve_call_data = erc20_contract.functions.approve(SYNC_ROUTER_ADDRESS, zk_web3.to_wei("1866", "mwei")).build_transaction(
        {
            "from": account.address,
            "chainId": zk_web3.zksync.chain_id,
        }
    )
    print(approve_call_data)
