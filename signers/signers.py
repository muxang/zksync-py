from mnemonic import Mnemonic
from bip_utils import Bip44, Bip44Coins, Bip44Changes
from eth_account import Account
from eth_account.signers.local import LocalAccount
from zksync2.signer.eth_signer import PrivateKeyEthSigner

class Signers:
    def __init__(self, mnemonic, index_start, number, chain_id):
        self.signers = []
        mnemo = Mnemonic("english")
        seed = mnemo.to_seed(mnemonic)
        bip_obj = Bip44.FromSeed(seed, Bip44Coins.ETHEREUM)
        for i in range(index_start, index_start + number):
            wallet = bip_obj.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i)
            private_key = wallet.PrivateKey().Bip32Key().Raw().ToHex()
            account: LocalAccount = Account.from_key(private_key)
            signer = PrivateKeyEthSigner(account, chain_id)
            self.signers.append(signer)
    
    @property
    def get_signers(self):
        return self.signers