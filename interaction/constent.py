ETH_ADDRESS = "0x5AEa5775959fBC2557Cc8789bC1bf90A239D9a91"
USDC_ADDRESS = "0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4"

SYNC_ROUTER_ADDRESS = "0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295"
SYNC_POOL_ADDRESS = "0x80115c708E12eDd42E504c1cD52Aea96C547c05c"
SYNC_BUY_DATA = "0x2cc4081e0000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000af147c1000000000000000000000000000000000000000000000000000000006443eba10000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000016345785d8a00000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000080115c708e12edd42e504c1cd52aea96c547c05c00000000000000000000000000000000000000000000000000000000000000800000000000000000000000004a2072a41ff717c1adc786f795041163cf63d5a4000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000600000000000000000000000005aea5775959fbc2557cc8789bc1bf90a239d9a91000000000000000000000000218ac84fb802985e99336cd9dfbe71fc54da4bce00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000"
SYNC_SELL_DATA = "0x2cc4081e000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000268ca32d51cec80000000000000000000000000000000000000000000000000000000064255ac20000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000600000000000000000000000003355df6d4c9c3035724fd0e3914de96a5a83aaf400000000000000000000000000000000000000000000000000000000012c5c940000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000080115c708e12edd42e504c1cd52aea96c547c05c00000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000600000000000000000000000003355df6d4c9c3035724fd0e3914de96a5a83aaf4000000000000000000000000218ac84fb802985e99336cd9dfbe71fc54da4bce00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000"


SYNC_POOL_ABI = [
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
    }
]

ERC20_ABI = [
    {
        'constant': False,
        'inputs': [
            {
                'name': '_spender',
                'type': 'address'
            },
            {
                'name': '_value',
                'type': 'uint256'
            }
        ],
        'name': 'approve',
        'outputs': [
            {
                'name': '',
                'type': 'bool'
            }
        ],
        'payable': False,
        'stateMutability': 'nonpayable',
        'type': 'function'
    }
]