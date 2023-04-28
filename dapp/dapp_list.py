dapp_list = [
    {
        "id": 1,
        "name": "syncswap",
        "address": "0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295",
    },
    {
        "id": 2,
        "name": "mute",
        "address": "0x8B791913eB07C32779a16750e3868aA8495F5964",
    },
    {
        "id": 3,
        "name": "spacefi",
        "address": "0xbE7D1FD1f6748bbDefC4fbaCafBb11C6Fc506d1d",
    },
    {
        "id": 4,
        "name": "nexon",
        "address": "0x1BbD33384869b30A323e15868Ce46013C82B86FB",
    },
    {
        "id": 5,
        "name": "velocore",
        "address": "0x46dbd39e26a56778d88507d7aEC6967108C0BD36",
    },
    {
        "id": 6,
        "name": "izumi",
        "address": "0x9606eC131EeC0F84c95D82c9a63959F2331cF2aC",
    },
    {
        "id": 7,
        "name": "gemswap",
        "address": "0x70B86390133d4875933bE54AE2083AAEbe18F2dA",
    },
]

class CrossDapp:
    def __init__(self, name, address):
        self.name = name
        self.cAddress = address

cross_dapp = CrossDapp("multichain", "0xff7104537F33937c66Ac0a65609EB8364Be75c7A")
