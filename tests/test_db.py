# 文件：test_db.py
import sys_path
from database.db import Account, AccountDapp, ImageName, create_tables, close_db

# 测试创建表
def test_create_tables():
    create_tables()
    assert Account.table_exists()
    assert AccountDapp.table_exists()
    assert ImageName.table_exists()

# 测试插入数据
def test_insert_data():
    # 插入 Account 数据
    account = Account.create(address='address1', deposit='100')
    assert account.address == 'address1'
    assert account.deposit == '100'
    account.save()

    # 插入 AccountDapp 数据
    account_dapp = AccountDapp.create(address='address2', name='name1', cAddress='cAddress1', hash='hash1')
    assert account_dapp.address == 'address2'
    assert account_dapp.name == 'name1'
    assert account_dapp.cAddress == 'cAddress1'
    assert account_dapp.hash == 'hash1'
    account_dapp.save()

    # 插入 ImageName 数据
    image_name = ImageName.create(names='name1')
    assert image_name.names == 'name1'
    image_name.save()

# 测试查询数据
def test_query_data():
    # 查询 Account 数据
    account = Account.get(Account.address == 'address1')
    assert account.deposit == '100'

    # 查询 AccountDapp 数据
    account_dapp = AccountDapp.get(AccountDapp.address == 'address2', AccountDapp.name == 'name1')
    assert account_dapp.cAddress == 'cAddress1'

    # 查询 ImageName 数据
    image_name = ImageName.get(ImageName.names == 'name1')
    assert image_name.id == 1

# 测试删除数据
def test_delete_data():
    # 删除 Account 数据
    account = Account.get(Account.address == 'address1')
    account.delete_instance()

    # 删除 AccountDapp 数据
    account_dapp = AccountDapp.get(AccountDapp.address == 'address2', AccountDapp.name == 'name1')
    account_dapp.delete_instance()

    # 删除 ImageName 数据
    image_name = ImageName.get(ImageName.names == 'name1')
    image_name.delete_instance()

# 测试主函数
if __name__ == '__main__':
    test_create_tables()
    test_insert_data()
    test_query_data()
    test_delete_data()
    close_db()
    print('All tests passed!')
