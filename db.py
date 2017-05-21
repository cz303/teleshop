from peewee import *

base = SqliteDatabase("base.db")

DeferredCategory = DeferredRelation()


class BaseModel(Model):
    class Meta:
        database = base


class Product(BaseModel):
    id = PrimaryKeyField(primary_key=True)
    title = CharField()
    description = TextField()
    img = TextField()
    price = IntegerField()
    category = ForeignKeyField(DeferredCategory)
    count = IntegerField()


class Category(BaseModel):
    id = PrimaryKeyField(primary_key=True)
    name = CharField()
    products = ForeignKeyField(Product, null=True)


class Order(BaseModel):
    id = PrimaryKeyField(primary_key=True)
    user_id = IntegerField()
    product = ForeignKeyField(Product)
    count = IntegerField()


class Users(BaseModel):
    id = IntegerField()
    name = CharField()
    is_admin = BooleanField(default=False)
    orders = ForeignKeyField(Order, null=True,default=False)


DeferredCategory.set_model(Category)

base.connect()
base.create_tables([Users, Order, Category, Product], safe=True)


def get_user(chat):
    return Users.get_or_create(id=chat.id, name=chat.username,)


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
