import sys_path
from signers.signers import Signers
from utils.get_env import EnvMnemonicKey

# 初始化 Signers 类
mnemonic_words = EnvMnemonicKey("ZKSYNC_TEST_MNEMONIC")
index_start = 0
number = 5
chain_id = 1
signers = Signers(mnemonic_words.mnemonic, index_start, number, chain_id)
signers_list = signers.get_signers

# 输出生成的签名者对象列表
print("生成的签名者对象列表：")
for signer in signers_list:
    print(signer.address)