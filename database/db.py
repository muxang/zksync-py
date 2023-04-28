# 文件：db.py

from peewee import SqliteDatabase, Model, CharField, PrimaryKeyField, CompositeKey

# 定义数据库模型
db = SqliteDatabase('zksync.db')

class Account(Model):
    address = CharField(primary_key=True)
    proxy = CharField(null=True)
    deposit_okx_address = CharField(null=True)
    withdraw_from_okx = CharField(null=True)
    bridge_to_zk = CharField(null=True)
    bridge_to_arb = CharField(null=True)
    deposit_to_okx = CharField(null=True)

    class Meta:
        database = db
        table_name = 'accounts'

class AccountDapp(Model):
    address = CharField()
    name = CharField()
    cAddress = CharField()
    hash = CharField(null=True)

    class Meta:
        database = db
        table_name = 'account_dapps'
        primary_key = CompositeKey('address', 'name')

class DappCombinations(Model):
    id = PrimaryKeyField()
    combination = CharField()

    class Meta:
        database = db
        table_name = 'dapp_combinations'

class ImageName(Model):
    id = PrimaryKeyField()
    names = CharField()

    class Meta:
        database = db
        table_name = 'image_names'

# 创建表
def create_tables():
    with db:
        db.create_tables([Account, AccountDapp, DappCombinations, ImageName], safe=True)
        print("创建数据库表成功")
    

# 关闭数据库连接
def close_db():
    db.close()