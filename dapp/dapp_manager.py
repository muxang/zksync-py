import random
from .dapp_list import dapp_list
from database.db import db, AccountDapp, DappCombinations, create_tables
import utils.my_logger as my_logger

all_combinations = []

def generate_combinations(arr, size):
    result = []
    def f(start, prefix):
        if len(prefix) == size:
            result.append(prefix[:])
        else:
            for i in range(start, len(arr)):
                f(i + 1, prefix + [arr[i]])

    f(0, [])
    return result


def create_combinations():
    # 查询数据库中是否已经存在组合
    existing_combinations = DappCombinations.select()
    if existing_combinations.count() > 0:
        print(f"已存在 {existing_combinations.count()} 个组合")
        # 返回组合
        for combination in existing_combinations:
            all_combinations.append(eval(combination.combination))
        return
    for size in range(3, 8):
        combinations = generate_combinations(dapp_list, size)
        all_combinations.extend(combinations)
        # 存入数据库
        with db.atomic():
            for combination in combinations:
                DappCombinations.create(combination=str(combination))
    print(f"已生成 {len(all_combinations)} 个组合")

create_tables()
create_combinations()

def assign_dapps_to_wallet(address):
    print(f"为用户 {address} 分配dapp")
    # 检查数据库中是否已经为该钱包分配过dapp
    existing_dapps = AccountDapp.select().where(AccountDapp.address == address)
    
    if existing_dapps.count() > 0:
        print(f"用户 {address} 已分配过dapp")
        return
    
    # 随机选择一个 DApp 组合
    print(f"共有 {len(all_combinations)} 个组合")
    random_index = random.randrange(len(all_combinations))
    print(f"随机选择第 {random_index} 个组合")
    selected_combination = all_combinations.pop(random_index)
    print(f"选择的组合为 {selected_combination}")


    # 将选择的 DApp 与钱包关联并插入数据库
    with db.atomic():
        for dapp in selected_combination:
            AccountDapp.create(
                address=address,
                name=dapp["name"],
                cAddress=dapp["address"]
            )

    # 从 DappCombinations 表中删除已经选择的组合
    try:
        DappCombinations.delete().where(DappCombinations.combination == str(selected_combination)).execute()
    except Exception as e:
        raise Exception(f"删除组合 {selected_combination} 失败: {e}")