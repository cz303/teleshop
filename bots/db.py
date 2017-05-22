import json

from peewee import *

base = SqliteDatabase("base.db")

DeferredCategory = DeferredRelation()


class BaseModel(Model):
    class Meta:
        database = base


class Product(BaseModel):
    id = PrimaryKeyField(primary_key=True)
    title = CharField(null=True)
    description = TextField(null=True)
    img = TextField()
    price = IntegerField(null=True)
    category = ForeignKeyField(DeferredCategory)
    count = IntegerField(null=True)


class Category(BaseModel):
    id = PrimaryKeyField(primary_key=True)
    name = CharField()


class Users(BaseModel):
    id = IntegerField()
    name = CharField()
    is_admin = BooleanField(default=False)
    data = TextField(default="{}")

class Order(BaseModel):
    id = PrimaryKeyField(primary_key=True)
    user = ForeignKeyField(Users)
    product = ForeignKeyField(Product)
    count = IntegerField(null=True)

DeferredCategory.set_model(Category)

base.connect()
base.create_tables([Users, Order, Category, Product], safe=True)


def get_user(chat):
    return Users.get_or_create(id=chat.id, name=chat.username)


def add_category(name):
    return Category.create(name=name)


def update_category(id, name):
    category = Category.get(id=id)
    category.name = name
    category.save()


def delete_category(id):
    for product in Product.get(category=Category.get(id=id)):
        product.delete_instance()
    Category.get(id=id).delete_instance()


def add_product(name, price, category, count):
    cat = Category.get(id=category)
    return Product.create(name=name, price=(price * 100), category=cat, count=count)


def add_count_product(id, count):
    product = Product.get(id=id)
    product.count += count
    product.save()


def change_name_product(id, name):
    product = Product.get(id=id)
    product.name = name
    product.save()


def change_price_product(id, price):
    product = Product.get(id=id)
    product.price = price * 100
    product.save()


def change_category_product(id, category):
    product = Product.get(id=id)
    product.category = Category.get(name=category)
    product.save()


def delete_product(id):
    Product.get(id=id).delete_instance()

def get_user_date(user):
    return json.loads(user.data)

def set_user_data(user,data):
    user.data = json.dumps(data)
    user.save()
