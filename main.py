# coding=utf-8
import logging

import telebot

import config
from bots.db import *
from bots.utils import *

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
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
        keyboard.add(telebot.types.InlineKeyboardButton(text=cat.name, callback_data="category_" + str(cat.id)))
    return keyboard


def prod_list(category):
    keyboad = telebot.types.InlineKeyboardMarkup()
    for prod in Product.select().where(Product.category == Category.get(Category.id == int(category)),
                                       Product.count > 0):
        keyboad.add(telebot.types.InlineKeyboardButton(
            text=prod.title + u" " + config.currency + "{0:.2f}".format(prod.price / 100),
            callback_data="product_" + str(prod.id) + "_" + category))
    return keyboad


def get_price(product):
    return config.currency + "{0:.2f}".format(product.price / 100)


def paginarion(page, category):
    count = Product.select().where(Product.category == Category.get(id=category)).count()
    if count > (page * 20):
        return True
    else:
        return False


def get_orders_list(user):
    keyboard = telebot.types.InlineKeyboardMarkup()
    for ord in Order.select().where(Order.user == user):
        keyboard.add(telebot.types.InlineKeyboardButton(
            text=ord.product.title + u" Цена:" + str((ord.product.price / 100) * ord.count),
            callback_data="order_" + str(ord.id)))
    keyboard.add(telebot.types.InlineKeyboardButton(text=u"Оплатить всё", callback_data="check_all"))
    keyboard.add(telebot.types.InlineKeyboardButton(text="Назад", callback_data="start"))
    return keyboard


@bot.message_handler(commands=["start", "help"])
def start(message):
    get_user(message.chat)
    key = get_menu()
    bot.send_message(message.chat.id, "Выберете пункт меню:", reply_markup=key)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        user, created = get_user(call.message.chat)
        ers = call.data.split("_")
        # TODO показываем меню
        if call.data == "start":
            key = get_menu()
            bot.send_message(call.message.chat.id, "Выберете пункт меню:", reply_markup=key)
        # TODO показываем список категорий и кнопки редактирования категорий
        if call.data == "shop":
            key = cat_list()
            if user.is_admin:
                key.add(telebot.types.InlineKeyboardButton(text="Добавить категорию", callback_data="add_category"))
                key.add(telebot.types.InlineKeyboardButton(text="Удалить категорию", callback_data="del_category"))
            key.add(telebot.types.InlineKeyboardButton(text="Меню", callback_data="start"))
            bot.send_message(call.message.chat.id, "Выберете категорию товара:", reply_markup=key)
        if call.data == "basket":
            key = get_orders_list(user)
            bot.send_message(call.message.chat.id, "Ваша корзина", reply_markup=key)
        # TODO Показываем список товаров в конкретной категории
        if ers[0] == "category":
            if len(ers) > 1:
                key = prod_list(ers[1])
                save = get_user_date(user)
                save["category"] = ers[1]
                set_user_data(user, save)
                if user.is_admin:
                    key.add(telebot.types.InlineKeyboardButton(text="Добавить товар", callback_data="add_product"))
                key.add(telebot.types.InlineKeyboardButton(text="Категории", callback_data="shop"))
                bot.send_message(call.message.chat.id, "Выберете товар:", reply_markup=key)
        # TODO Показываем фото,описание,цену продукта и кнопки редактирования если пользователь админ
        if ers[0] == "product":
            if len(ers) > 1:
                product = Product.get(Product.id == int(ers[1]))
                key = telebot.types.InlineKeyboardMarkup()
                img = telebot.types.InlineKeyboardButton(text=u"\U0001F5BC",
                                                         callback_data="edit_prod_img_" + str(product.id))
                title = telebot.types.InlineKeyboardButton(text=u"\u270F\uFE0F",
                                                           callback_data="edit_prod_title_" + str(product.id))
                description = telebot.types.InlineKeyboardButton(text=u"\U0001F4DD",
                                                                 callback_data="edit_prod_desc_" + str(product.id))
                price = telebot.types.InlineKeyboardButton(text=u"\U0001F4B6",
                                                           callback_data="edit_prod_price_" + str(product.id))
                count = telebot.types.InlineKeyboardButton(text=u"\U0001F4E6",
                                                           callback_data="edit_prod_count_" + str(product.id))
                category = telebot.types.InlineKeyboardButton(text=u"\U0001F4C2",
                                                              callback_data="edit_prod_cat_" + str(product.id))

                key.row(img, title, description, category, price, count)
                key.add(telebot.types.InlineKeyboardButton(
                    text=u"Добавить в корзину " + get_price(product) + u" " + str(product.count),
                    callback_data="buy_" + str(product.id)))
                key.add(
                    telebot.types.InlineKeyboardButton(text="Назад", callback_data="category_" + ers[2]))
                bot.send_photo(call.message.chat.id, photo=product.img, caption=product.description, reply_markup=key)
        # TODO Обработка покупки
        if ers[0] == "buy":
            if len(ers) > 1:
                product = Product.get(Product.id == ers[1])
                order, created = Order.get_or_create(user=user, product=product)
                if order.count is None:
                    order.count = 1
                else:
                    order.count += 1
                order.save()
                bot.answer_callback_query(callback_query_id=call.id, show_alert=False, text=u"Товар "
                                                                                            u"добавлен в "
                                                                                            u"корзину")
        # TODO Обработка кнопок добавления
        if ers[0] == "add":
            # TODO запускаем шаги добавлениея котегории
            if ers[1] == "category":
                msg = bot.send_message(call.message.chat.id, "Введите название категории")
                bot.register_next_step_handler(msg, process_create_category)
            # TODO запускаем шаги добавления товара
            if ers[1] == "product":
                msg = bot.send_message(call.message.chat.id, "Пришлите фото товара")
                bot.register_next_step_handler(msg, process_create_product_photo)
        # TODO Удаление котегории и товаров
        if ers[0] == "del":
            if ers[1] == "category":
                key = telebot.types.InlineKeyboardMarkup()
                for cat in Category.select():
                    key.add(telebot.types.InlineKeyboardButton(text=cat.name, callback_data="del_cat_" + str(cat.id)))
                key.add(telebot.types.InlineKeyboardButton(text="Категории", callback_data="shop"))
                bot.send_message(call.message.chat.id, "Категория удалится вместе с товарами которые в ней",
                                 reply_markup=key)
            if ers[1] == "cat":
                cat = Category.get(Category.id == int(ers[2]))
                name = cat.name
                for prod in Product.select().where(Product.category == cat):
                    prod.delete_instance()
                cat.delete_instance()
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text="Удалить еще категорию", callback_data="del_category"))
                key.add(telebot.types.InlineKeyboardButton(text="Категории", callback_data="shop"))
                bot.send_message(call.message.chat.id, u"Категория " + name + u" и все товары в ней удалены")


bot.polling()
