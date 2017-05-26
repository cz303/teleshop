import json
import os
import urlparse

from peewee import *

print os

url = urlparse.urlparse(os.environ['DATABASE_URL'])
base = PostgresqlDatabase(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)


class BaseModel(Model):
    class Meta:
        database = base


class Category(BaseModel):
    id = PrimaryKeyField(primary_key=True)
    name = CharField()


class Product(BaseModel):
    id = PrimaryKeyField(primary_key=True)
    title = CharField(null=True)
    description = TextField(null=True)
    img = TextField()
    price = IntegerField(null=True)
    category = ForeignKeyField(Category)
    count = IntegerField(null=True)


class Users(BaseModel):
    id = IntegerField(unique=True)
    name = CharField(null=True)
    is_admin = BooleanField(default=False)
    data = TextField(default="{}")


class Order(BaseModel):
    id = PrimaryKeyField(primary_key=True)
    user = ForeignKeyField(Users)
    product = ForeignKeyField(Product)
    count = IntegerField(null=True)


base.connect()
base.create_tables([Category, Product, Users, Order], safe=True)


def get_user(chat):
    return Users.get_or_create(id=chat.id, name=chat.username)


def up_user(id):
    try:
        user = Users.get(Users.id == int(id))
        user.is_admin = True
        user.save()
    except:
        Users.create(id=int(id), is_admin=True)


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


def set_user_data(user, data):
    user.data = json.dumps(data)
    user.save()
