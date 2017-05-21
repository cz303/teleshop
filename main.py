# coding=utf-8
import telebot
import config
from db import *

bot = telebot.TeleBot(config.API_TOKEN)

menu = {
    "shop": "Магазин",
    "basket": "Корзина"
}


def get_menu():
    keyboard = telebot.types.InlineKeyboardMarkup()
    for key in menu.keys():
        keyboard.add(telebot.types.InlineKeyboardButton(text=menu[key], callback_data=key))
    return keyboard


def cat_list():
    keyboard = telebot.types.InlineKeyboardMarkup()
    for cat in Category.select():
        keyboard.add(telebot.types.InlineKeyboardButton(text=cat.name, callback_data="category_" + str(cat.id) + "_1"))
    return keyboard


def prod_list(offset, category):
    keyboad = telebot.types.InlineKeyboardMarkup()
    for prod in Product.select().where(Product.category == Category.get(Category.id == int(category)),
                                       Product.count > 0).paginate(int(offset), 20):
        keyboad.add(telebot.types.InlineKeyboardButton(
            text=prod.name + u" " + config.currency + "{0:.2f}".format(prod.price / 100),
            callback_data="product_" + str(prod.id) + "_" + category + "_" + offset))
    return keyboad


def paginarion(page, category):
    count = Product.select().where(Product.category == Category.get(id=category)).count()
    if count > (page * 20):
        return True
    else:
        return False


def get_orders_list(id):
    keyboard = telebot.types.InlineKeyboardMarkup()
    for ord in Users.get(Users.id == id).orders:
        keyboard.add(telebot.types.InlineKeyboardButton(text=ord.name + " Цена:" + str(ord.price / 100),
                                                        callback_data="order_" + str(ord.id)))

def process_create_category(message):
    user,create = get_user(message.chat)
    if user.is_admin:
        cat_name = message.text
        Category.create(name=cat_name)



@bot.message_handler(commands=["start", "help"])
def start(message):
    get_user(message.chat)
    key = get_menu()
    bot.send_message(message.chat.id, "Выберете пункт меню:", reply_markup=key)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        user,created = get_user(call.message.chat)
        ers = call.data.split("_")
        if call.data == "start":
            key = get_menu()
            bot.send_message(call.message.chat.id, "Выберете пункт меню:", reply_markup=key)
        if call.data == "shop":
            key = cat_list()
            if user.is_admin:
                key.add(telebot.types.InlineKeyboardButton(text="Добавить категорию",callback_data="add_category"))
                key.add(telebot.types.InlineKeyboardButton(text="Удалить категорию",callback_data="del_category"))
            key.add(telebot.types.InlineKeyboardButton(text="Меню", callback_data="start"))
            bot.send_message(call.message.chat.id, "Выберете категорию товара:", reply_markup=key)
        if call.data == "basket":
            pass
        if ers[0] == "category":
            if len(ers) > 1:
                key = prod_list(ers[2], ers[1])
                if paginarion(ers[2], ers[1]):
                    back = telebot.types.InlineKeyboardButton(text="Назад",
                                                              callback_data="category_" + str(ers[1]) + "_" + str(
                                                                  ers[2]))
                    next = telebot.types.InlineKeyboardButton(text="Вперед",
                                                              callback_data="category_" + str(ers[1]) + "_" + str(
                                                                  ers[2] + 1))
                    key.row(back, next)
                key.add(telebot.types.InlineKeyboardButton(text="Категории", callback_data="shop"))
                bot.send_message(call.message.chat.id, "Выберете товар:", reply_markup=key)
        if ers[0] == "product":
            if len(ers) > 1:
                product = Product.get(Product.id == int(ers[1]))
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text="Добавить в корзину",
                                                           callback_data="buy_" + str(product.id)))
                key.add(telebot.types.InlineKeyboardButton(text="Назад", callback_data=""))
                bot.send_photo(call.message.chat.id, photo=product.img, caption=product.description, reply_markup=key)
        if ers[0] == "buy":
            if len(ers) > 1:
                product = Product.get(Product.id == ers[1])
                order, created = Order.get_or_create(user_id=user.id, product=product)
                if created:
                    user.orders.add(order)
                else:
                    order.count += 1
                    order.save()
                bot.answer_callback_query(callback_query_id=call.message.chat.id,show_alert=True,text=u"Товар "
                                                                                                      u"добавлен в "
                                                                                                      u"корзину")



bot.polling()
