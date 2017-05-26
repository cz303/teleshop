# coding=utf-8
import os
import telebot
import db
import utils


from flask import Flask, request, abort, jsonify

bot = telebot.TeleBot(os.environ['API_TIKEN'])

server = Flask(__name__)

menu = {
    "shop": "Магазин",
    "basket": "Корзина"
}

ut = utils.Util(bot, db)


def get_menu():
    keyboard = telebot.types.InlineKeyboardMarkup()
    for key in menu.keys():
        keyboard.add(telebot.types.InlineKeyboardButton(text=menu[key], callback_data=key))
    return keyboard


def cat_list(tag, prod=None):
    keyboard = telebot.types.InlineKeyboardMarkup()
    for cat in db.Category.select():
        if prod is not None:
            strs = tag + str(cat.id) + ">" + prod
        else:
            strs = tag + str(cat.id)
        keyboard.add(telebot.types.InlineKeyboardButton(text=cat.name, callback_data=strs))
    return keyboard


# TODO это пиздец
def prod_list(category, is_admin=False):
    keyboad = telebot.types.InlineKeyboardMarkup()
    if is_admin:
        for prod in db.Product.select().where(db.Product.category == db.Category.get(db.Category.id == int(category))):
            price = get_price(prod)
            title = prod.title if prod.title is not None else u"Без имени"
            keyboad.add(telebot.types.InlineKeyboardButton(
                text=u" " + title + u" " + price,
                callback_data="product>" + str(prod.id) + ">" + category))
    else:
        for prod in db.Product.select().where(db.Product.category == db.Category.get(db.Category.id == int(category)),
                                              db.Product.name != None, db.Product.count > 0):
            keyboad.add(telebot.types.InlineKeyboardButton(
                text=u" " + prod.title + u" " + get_price(prod),
                callback_data="product>" + str(prod.id) + ">" + category))
    return keyboad


def get_price(product):
    if product.price is not None:
        return os.environ['currency'] + "{0:.2f}".format(product.price / 100)
    else:
        return os.environ['currency'] + u"0"


def get_orders_list(user):
    keyboard = telebot.types.InlineKeyboardMarkup()
    for order in db.Order.select().where(db.Order.user == user):
        keyboard.add(telebot.types.InlineKeyboardButton(
            text=order.product.title + u" Цена:" + str((order.product.price / 100) * order.count),
            callback_data="order_" + str(order.id)))
    keyboard.add(telebot.types.InlineKeyboardButton(text=u"Оплатить всё", callback_data="check_all"))
    keyboard.add(telebot.types.InlineKeyboardButton(text="Назад", callback_data="start"))
    return keyboard


@bot.message_handler(commands=["start", "help"])
def start(message):
    db.get_user(message.chat)
    key = get_menu()
    bot.send_message(message.chat.id, "Выберете пункт меню:", reply_markup=key)


@bot.callback_query_handler(func=lambda call: ut.routes("start", call))
def start(call):
    key = get_menu()
    bot.send_message(call.message.chat.id, "Выберете пункт меню:", reply_markup=key)


@bot.callback_query_handler(func=lambda call: ut.routes("shop", call))
def shop(call):
    user, cre = db.get_user(call.message.chat)
    key = cat_list("category>")
    if user.is_admin:
        key.add(telebot.types.InlineKeyboardButton(text="Добавить категорию", callback_data="add_category"))
        key.add(telebot.types.InlineKeyboardButton(text="Удалить категорию", callback_data="del_category"))
    key.add(telebot.types.InlineKeyboardButton(text="Меню", callback_data="start"))
    bot.send_message(call.message.chat.id, "Выберете категорию товара:", reply_markup=key)


@bot.callback_query_handler(func=lambda call: ut.routes("category>id:int", call))
def category(call):
    user, cre = db.get_user(call.message.chat)
    save = db.get_user_date(user)
    if user.is_admin:
        key = prod_list(save.get("id"), is_admin=True)
    else:
        key = prod_list(save.get('id'))
    save = db.get_user_date(user)
    db.set_user_data(user, save)
    if user.is_admin:
        key.add(
            telebot.types.InlineKeyboardButton(text="Добавить товар", callback_data="add>product>" + save.get("id")))
        key.add(telebot.types.InlineKeyboardButton(text="Переименовать категорию",
                                                   callback_data="edit>category>rename>" + save.get("id")))
    key.add(telebot.types.InlineKeyboardButton(text="Категории", callback_data="shop"))
    bot.send_message(call.message.chat.id, "Выберете товар:",
                     reply_markup=key)


@bot.callback_query_handler(func=lambda call: ut.routes("product>prod_id:int>cat_id:int", call))
def view_prod(call):
    user, cre = db.get_user(call.message.chat)
    save = db.get_user_date(user)
    ut.send_product(call.message.chat, save.get("prod_id"))


@bot.callback_query_handler(func=lambda call: ut.routes("buy>prod_id:int", call))
def buy_prod(call):
    user, c = db.get_user_date(call.message.chat)
    save = db.get_user_date(user)
    prod = db.Product.get(db.Product.id == save.get("prod_id"))
    order, c = db.Order.get_or_create(user=user, product=prod)
    if order.count is None:
        order.count = 1
    else:
        order.count += 1
    order.save()
    bot.answer_callback_query(callback_query_id=call.id, show_alert=False, text=u"Товар добавлен в корзину")


@bot.callback_query_handler(func=lambda call: ut.routes("add>category", call))
def add_category(call):
    msg = bot.send_message(call.message.chat.id, "Введите нозвание категории")
    bot.register_next_step_handler(msg, ut.process_create_category)


@bot.callback_query_handler(func=lambda call: ut.routes("add>product>cat_id:int", call))
def add_product(call):
    msg = bot.send_message(call.message.chat.id, "Пришлите фото товара")
    bot.register_next_step_handler(msg, ut.process_create_product_photo)


@bot.callback_query_handler(func=lambda call: ut.routes("del>category", call))
def del_view_category(call):
    key = telebot.types.InlineKeyboardMarkup()
    for cat in db.Category.select():
        key.add(telebot.types.InlineKeyboardButton(text=cat.name, callback_data="del>category>" + str(cat.id) + ":int"))
    key.add(telebot.types.InlineKeyboardButton(text="Категории", callback_data="shop"))
    bot.send_message(call.message.chat.id, "Категория удалится вместе с товарами которые в ней",
                     reply_markup=key)


@bot.callback_query_handler(func=lambda call: ut.routes("del>category>cat_id:int", call))
def del_category(call):
    user, c = db.get_user(call.message.chat)
    save = db.get_user_date(user)
    cat = db.Category.get(db.Category.id == int(save.get("cat_id")))
    name = cat.name
    for prod in db.Product.select().where(db.Product.category == cat):
        prod.delete_instance()
    cat.delete_instance()
    key = telebot.types.InlineKeyboardMarkup()
    key.add(telebot.types.InlineKeyboardButton(text="Удалить еще категорию", callback_data="del>category"))
    key.add(telebot.types.InlineKeyboardButton(text="Категории", callback_data="shop"))
    bot.send_message(call.message.chat.id, u"Категория " + name + u" и все товары в ней удалены")


@bot.callback_query_handler(func=lambda call: ut.routes("edit>prod>img>prod_id:int", call))
def edit_prod_photo(call):
    msg = bot.send_message(call.message.chat.id, "Пришлите новое фото товара:")
    bot.register_next_step_handler(msg, ut.edit_prod_img)


@bot.callback_query_handler(func=lambda call: ut.routes("edit>prod>title>prod_id:int", call))
def edit_prod_title(call):
    msg = bot.send_message(call.message.chat.id, "Пришлите новое название")
    bot.register_next_step_handler(msg, ut.edit_prod_title)


@bot.callback_query_handler(func=lambda call: ut.routes("edit>prod>desc>prod_id:int", call))
def edit_prod_desc(call):
    msg = bot.send_message(call.message.chat.id, "Пришлите новое описание")
    bot.register_next_step_handler(msg, ut.edit_prod_description)


@bot.callback_query_handler(func=lambda call: ut.routes("edit>prod>price>prod_id:int", call))
def edit_prod_price(call):
    msg = bot.send_message(call.message.chat.id, "Пришлите новую цену")
    bot.register_next_step_handler(msg, ut.edit_prod_price)


@bot.callback_query_handler(func=lambda call: ut.routes("edit>prod>count>prod_id:int", call))
def edit_prod_count(call):
    msg = bot.send_message(call.message.chat.id, "Пришлите количество товара")
    bot.register_next_step_handler(msg, ut.edit_prod_count)


@bot.callback_query_handler(func=lambda call: ut.routes("edit>prod>category>prod_id:int", call))
def edit_prod_category(call):
    user, c = db.get_user(call.message.chat)
    save = db.get_user_date(user)
    key = cat_list("edit>prod>setcat>", prod=save.get("prod_id"))
    bot.send_message(call.message.chat.id, "Выбирите категорию", reply_markup=key)


@bot.callback_query_handler(func=lambda call: ut.routes("edit>prod>setcat>cat_id:int>prod_id:int", call))
def edit_prod_set_category(call):
    user, c = db.get_user(call.message.chat)
    save = db.get_user_date(user)
    prod = db.Product.get(db.Product.id == save.get("prod_id"))
    cat = db.Category.get(db.Category.id == save.get("cat_id"))
    prod.category = cat
    prod.save()
    ut.send_product(call.message.chat, prod.id)


@bot.callback_query_handler(func=lambda call: ut.routes("edit>category>rename>cat_id:int", call))
def rename_category(call):
    user, c = db.get_user(call.message.chat)
    save = db.get_user_date(user)
    cat = db.Category.get(db.Category.id == save.get("cat_id"))
    msg = bot.send_message(call.message.chat.id, u"Пришлите новое имя категории " + cat.name)
    bot.register_next_step_handler(msg, ut.edit_cat_name)

@bot.callback_query_handler(func=lambda call: ut.routes("del>product>prod_id:int", call))
def del_prod_sclad(call):
    user, c = db.get_user(call.message.chat)
    save = db.get_user_date(user)
    prod = db.Product.get(db.Product.id == save.get("prod_id"))
    for ord in db.Order.select().where(db.Order.product==prod):
        ord.delete_instance()
    cat = prod.category.id
    name = prod.title
    prod.delete_instance()
    key = telebot.types.InlineKeyboardMarkup()
    key.add(telebot.types.InlineKeyboardButton(text="К Категории", callback_data="category>" + str(cat)))
    bot.send_message(call.message.chat.id,text=u"Товар "+name+u" успешно удален",reply_markup=key)


@server.route("/bot", methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route("/up",methods=["POST"])
def login():
    if not request.json:
        abort(400)
    else:
        print request.json
        if request.json.get("api") == os.environ.get("API_TIKEN"):
            user = db.Users.get(db.Users.id==request.json.get("id"))
            user.is_admin =True
            user.save()
            return "!",200
        else:
            return jsonify(request.json),200


@server.route("/")
def webhook():
    bot.remove_webhook()

    bot.set_webhook(url=os.environ['SITE_URL'])

    return  "!",200


server.run(host="0.0.0.0",port=os.environ.get("PORT",5000))