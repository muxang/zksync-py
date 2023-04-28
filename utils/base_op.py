import random
import time
from eth_typing import HexStr, HexAddress
from eth_utils import to_checksum_address
from decimal import Decimal
from web3 import Web3
from zksync2.core.types import ZkBlockParams, EthBlockParams, Token
from zksync2.module.module_builder import ZkSyncBuilder
from zksync2.signer.eth_signer import PrivateKeyEthSigner
from zksync2.transaction.transaction_builders import TxFunctionCall
from zksync2.manage_contracts.erc20_contract import ERC20ContractRead, ERC20Encoder, _erc_20_abi_default
from zksync2.provider.eth_provider import EthereumProvider
from typing import Tuple
from okx.Funding import FundingAPI

class ZkSyncBaseOp:
    def __init__(self, zk_web3: Web3, signer: PrivateKeyEthSigner, chain_id: int):
        self.zk_web3 = zk_web3
        self.signer = signer
        self.chain_id = chain_id

    def get_eth_balance(self) -> Tuple[float, int]:
        # Get WEI balance of ETH address
        balance_wei = self.zk_web3.zksync.get_balance(
            self.signer.address, EthBlockParams.LATEST.value)

        # Convert WEI balance to ETH
        balance_eth = self.zk_web3.from_wei(balance_wei, "ether")

        # Return the ETH balance of the ETH address
        return balance_eth, balance_wei

    def transfer_eth(self, to_address: HexAddress, amount: float) -> bytes:
        # Get chain id of zkSync network
        chain_id = self.zk_web3.zksync.chain_id

        # Get nonce of ETH address on zkSync network
        nonce = self.zk_web3.zksync.get_transaction_count(
            self.signer.address, ZkBlockParams.COMMITTED.value
        )

        # Get current gas price in Wei
        gas_price = self.zk_web3.zksync.gas_price

        # Create transaction
        tx_func_call = TxFunctionCall(
            chain_id=chain_id,
            nonce=nonce,
            from_=self.signer.address,
            to=to_checksum_address(to_address),
            value=self.zk_web3.to_wei(amount, "ether"),
            data=HexStr("0x"),
            gas_limit=0,  # UNKNOWN AT THIS STATE
            gas_price=gas_price,
            max_priority_fee_per_gas=gas_price,
        )

        # ZkSync transaction gas estimation
        estimate_gas = self.zk_web3.zksync.eth_estimate_gas(tx_func_call.tx) * 10 // 15
        print(f"Estimated gas for transaction is: {estimate_gas}")
        print(f"Fee price for transaction is: {self.zk_web3.from_wei(gas_price, 'gwei')} gwei")
        print(f"Fee for transaction is: {self.zk_web3.from_wei(estimate_gas * gas_price, 'ether')}")

        # Convert transaction to EIP-712 format
        print(f"singer address: {self.signer.address}")
        tx_712 = tx_func_call.tx712(estimate_gas)
        print(f"Transaction EIP-712 format: {tx_712}")

        # Sign message & encode it
        signed_message = self.signer.sign_typed_data(tx_712.to_eip712_struct())

        # Encode signed message
        msg = tx_712.encode(signed_message)

        # Send transaction to zkSync network
        tx_hash = self.zk_web3.zksync.send_raw_transaction(msg)

        return tx_hash
    
    def get_contract_instance(self, contract_address: HexAddress, abi):
        # Get readable contract instance
        contract = self.zk_web3.zksync.contract(address=contract_address, abi=abi)
        return contract

    def get_erc20_balance(
            self,
            contract_address: HexAddress,
            abi=_erc_20_abi_default()
        ) -> Tuple[float, int]:

        # Get readable contract instance
        contract = ERC20ContractRead(
            web3=self.zk_web3.zksync, contract_address=contract_address, abi=abi
        )

        # Get decimals of the contract
        contract_decimals = contract.decimals()

        # Query contract's balance
        erc20_balance = contract.balance_of(self.signer.address)

        # Return Formated Balance
        return float(Decimal(erc20_balance) / Decimal(10) ** contract_decimals), erc20_balance
    
    def get_erc20_allowance(
            self,
            contract_address: HexAddress,
            spender_address: HexAddress,
            abi=_erc_20_abi_default()
        ) -> Tuple[float, int]:

        # Get readable contract instance
        contract = ERC20ContractRead(
            web3=self.zk_web3.zksync, contract_address=contract_address, abi=abi
        )

        # Get decimals of the contract
        contract_decimals = contract.decimals()

        # Query contract's balance
        allow_balance = contract.allowance(self.signer.address, spender_address)

        # Return Formated Balance
        return float(Decimal(allow_balance) / Decimal(10) ** contract_decimals), allow_balance

    def approve_erc20(
        self,
        spender_address: HexAddress,
        amount: int,
        contract_address: HexAddress,
        abi=_erc_20_abi_default()
    ) -> HexStr:

        # Get chain id of zkSync network
        chain_id = self.zk_web3.zksync.chain_id

        # Get current gas price in Wei
        gas_price = self.zk_web3.zksync.gas_price

        # Get nonce of ETH address on zkSync network
        nonce = self.zk_web3.zksync.get_transaction_count(
            self.signer.address, ZkBlockParams.COMMITTED.value
        )

        erc20_encoder = ERC20Encoder(self.zk_web3, abi)

        # approve parameters
        approve_params = (spender_address, amount)

        # Encode arguments
        call_data = erc20_encoder.encode_method("approve", args=approve_params)

        # Create transaction
        func_call = TxFunctionCall(
            chain_id=chain_id,
            nonce=nonce,
            from_=self.signer.address,
            to=contract_address,
            data=call_data,
            gas_limit=0,  # UNKNOWN AT THIS STATE
            gas_price=gas_price,
            max_priority_fee_per_gas=gas_price,
        )

        # ZkSync transaction gas estimation
        estimate_gas = self.zk_web3.zksync.eth_estimate_gas(func_call.tx) * 10 // 15

        # Convert transaction to EIP-712 format
        tx_712 = func_call.tx712(estimated_gas=estimate_gas)

        # Sign message & encode it
        signed_message = self.signer.sign_typed_data(tx_712.to_eip712_struct())

        # Encode signed message
        msg = tx_712.encode(signed_message)

        # Transfer ERC-20 token
        tx_hash = self.zk_web3.zksync.send_raw_transaction(msg)

        return tx_hash

    def transfer_erc20(
        self,
        to: HexAddress,
        amount: float,
        contract_address: HexAddress,
        abi=_erc_20_abi_default()
    ) -> HexStr:

        # Get chain id of zkSync network
        chain_id = self.zk_web3.zksync.chain_id

        # Get current gas price in Wei
        gas_price = self.zk_web3.zksync.gas_price

        # Get nonce of ETH address on zkSync network
        nonce = self.zk_web3.zksync.get_transaction_count(
            self.signer.address, ZkBlockParams.COMMITTED.value
        )

        erc20_encoder = ERC20Encoder(self.zk_web3, abi)

        amountBN=self.zk_web3.to_wei(amount, "mwei"),
        print(f"amountBN: {amountBN}")

        # Transfer parameters
        transfer_params = (to, amountBN)

        # Encode arguments
        call_data = erc20_encoder.encode_method("transfer", args=transfer_params)

        # Create transaction
        func_call = TxFunctionCall(
            chain_id=chain_id,
            nonce=nonce,
            from_=self.signer.address,
            to=contract_address,
            data=call_data,
            gas_limit=0,  # UNKNOWN AT THIS STATE
            gas_price=gas_price,
            max_priority_fee_per_gas=gas_price,
        )

        # ZkSync transaction gas estimation
        estimate_gas = self.zk_web3.zksync.eth_estimate_gas(func_call.tx) * 10 // 15
        print(f"Estimated gas for transaction is: {estimate_gas}")
        print(f"Fee price for transaction is: {self.zk_web3.from_wei(gas_price, 'gwei')} gwei")
        print(f"Fee for transaction is: {self.zk_web3.from_wei(estimate_gas * gas_price, 'ether')}")

        # Convert transaction to EIP-712 format
        tx_712 = func_call.tx712(estimated_gas=estimate_gas)

        # Sign message & encode it
        signed_message = self.signer.sign_typed_data(tx_712.to_eip712_struct())

        # Encode signed message
        msg = tx_712.encode(signed_message)

        # Transfer ERC-20 token
        tx_hash = self.zk_web3.zksync.send_raw_transaction(msg)

        return tx_hash

    def deposit(self, eth_web3: Web3):
        eth_provider = EthereumProvider(self.zk_web3, eth_web3, self.signer.credentials)
        eth_balance = None
        limit_balance = eth_web3.to_wei(0.5, "ether")
        eth_token = Token.create_eth()
        # 持续查询账户余额, 直到账户余额大于 0.5 ETH
        while True:
            try:
                eth_balance = eth_provider.get_l1_balance(eth_token, EthBlockParams.LATEST)
                if eth_balance >= limit_balance:
                    break
            except Exception as e:
                print(f"账户 {self.signer.address} 执行 ETH 跨链到 zkSync 时, 余额查询失败, 60s 后重试...")
                time.sleep(60)
                continue
            print(f"账户 {self.signer.address} ETH 余额 {eth_web3.from_wei(eth_balance, 'ether')} 不足 0.5 ETH, 不满足跨链到zkSync要求, 10分钟后重新查询余额...")
            time.sleep(600)
        l2_gas_limit = 700000 + int(random.random() * 100000)
        l1_tx_hash = eth_provider.deposit(token=Token.create_eth(), amount=eth_balance, l2_gas_limit=l2_gas_limit)

        return l1_tx_hash

    def withdraw_from_okx(self, cli: FundingAPI):
        # 获取账户余额
        while True:
            result = cli.get_balances("ETH")
            availBal = result["data"][0]["availBal"]
            if float(availBal) > 0.5:
                wait_time = random.randint(600, 7200)
                print(f"okx ETH 可用余额: {availBal}, 等待 {wait_time} 秒后提现...")
                time.sleep(wait_time)
                break
            elif availBal == 0:
                # 等待10分钟后重试
                print(f"okx ETH 可用余额: {availBal}, 等待 10 分钟后重试...")
                time.sleep(600)
                continue
        # 获取当前手续费
        result = cli.get_currencies("ETH")
        minFee = result["data"][0]["minFee"]
        chain = result["data"][0]["chain"]
        # 接收地址
        to_addr = to_checksum_address(self.signer.address)
        # 提现
        result = cli.withdrawal(ccy="ETH", amt=availBal, dest="4", toAddr=to_addr, fee=minFee, chain=chain)
        if result["code"] != "0":
            raise Exception(f"withdrawal failed: {result['msg']}")
        wdId = result["data"][0]["wdId"]
        return availBal, wdId

    def contract_call(
        self,
        call_data: HexStr,
        dapp,
        value = 0
    ) -> HexStr:

        # Get contract address
        contract_address = dapp.cAddress

        # Get chain id of zkSync network
        chain_id = self.zk_web3.zksync.chain_id

        # Get current gas price in Wei
        gas_price = self.zk_web3.zksync.gas_price

        # Get nonce of ETH address on zkSync network
        nonce = self.zk_web3.zksync.get_transaction_count(
            self.signer.address, ZkBlockParams.COMMITTED.value
        )

        # Create transaction
        func_call = TxFunctionCall(
            chain_id=chain_id,
            nonce=nonce,
            from_=self.signer.address,
            to=contract_address,
            data=call_data,
            gas_limit=0,  # UNKNOWN AT THIS STATE
            gas_price=gas_price,
            max_priority_fee_per_gas=0,
            value=value,
        )

        # ZkSync transaction gas estimation
        estimate_gas = self.zk_web3.zksync.eth_estimate_gas(func_call.tx) // 3

        # Convert transaction to EIP-712 format
        tx_712 = func_call.tx712(estimated_gas=estimate_gas)

        # Sign message & encode it
        signed_message = self.signer.sign_typed_data(tx_712.to_eip712_struct())

        # Encode signed message
        msg = tx_712.encode(signed_message)

        # Transfer ERC-20 token
        tx_hash = self.zk_web3.zksync.send_raw_transaction(msg)

        return tx_hash

    def copy(self):
        return ZkSyncBaseOp(self.zk_web3, self.signer, self.chain_id)