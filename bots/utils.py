# coding=utf-8
import telebot

from db import *
from main import bot


def process_create_category(message):
    user, create = get_user(message.chat)
    if user.is_admin:
        if len(message.text) > 0:
            cat_name = message.text
            Category.create(name=cat_name)
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text="Категории", callback_data="shop"))
            bot.send_message(message.chat.id, u"Категория " + message.text + u" добавлена", reply_markup=key)
        else:
            bot.reply_to(message, "Не приемлемое название категории")


def process_create_product_photo(message):
    user, create = get_user(message.chat)
    if user.is_admin:
        if len(message.photo) > 0:
            save = get_user_date(user)
            file_id = message.photo[-1].file_id
            cat = Category.get(Category.id == int(save["category"]))
            prod = Product.create(img=file_id, category=cat)
            save["prod_id"] = prod.id
            set_user_data(user, save)
            msg = bot.send_message(message.chat.id, "Введите имя товара: ")
            bot.register_next_step_handler(msg, process_create_product_title)
        else:
            bot.send_message(message.chat.id, "Не могу найти фото")


def process_create_product_title(message):
    user, create = get_user(message.chat)
    if user.is_admin:
        if len(message.text) > 0:
            save = get_user_date(user)
            prod = Product.get(Product.id == int(save["prod_id"]))
            prod.title = message.text
            prod.save()
            msg = bot.send_message(message.chat.id, "Введите описание товара 200 символов:")
            bot.register_next_step_handler(msg, process_create_product_description)
        else:
            bot.send_message(message.chat.id, "Не могу найти имя товара:")


def process_create_product_description(message):
    user, create = get_user(message.chat)
    if user.is_admin:
        if 0 < len(message.text):
            save = get_user_date(user)
            prod = Product.get(Product.id == int(save["prod_id"]))
            prod.description = message.text
            prod.save()
            msg = bot.send_message(message.chat.id, "Укажите цену товара пример: 3.22")
            bot.register_next_step_handler(msg, process_create_product_price)
        else:
            bot.send_message(message.chat.id, "Укажите описание товара")


def process_create_product_price(message):
    user, create = get_user(message.chat)
    if user.is_admin:
        if len(message.text) > 0:
            try:
                save = get_user_date(user)
                prod = Product.get(Product.id == int(save["prod_id"]))
                prod.price = int(float(message.text.replace(",", ".").strip()) * 100)
                prod.save()
                msg = bot.send_message(message.chat.id, "Укажите количество товаров: 3")
                bot.register_next_step_handler(msg, process_create_product_count)
            except:
                bot.send_message(message.chat.id, "Цена не является числом")
        else:
            bot.send_message(message.chat.id, "Укажите цену товара")


def process_create_product_count(message):
    user, create = get_user(message.chat)
    if user.is_admin:
        if len(message.text) > 0:
            if message.text.isdigit():
                save = get_user_date(user)
                prod = Product.get(Product.id == int(save["prod_id"]))
                prod.count = int(message.text.strip())
                prod.save()
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text=u"Добавить еще товар", callback_data="add_product"))
                key.add(telebot.types.InlineKeyboardButton(
                    text=u"Посмотреть товары в категории " + Category.get(Category.id == int(save["category"])).name,
                    callback_data="category_" + save["category"] + "_1"))
                bot.send_message(message.chat.id, u"Товар " + prod.title + u" успешно добавлен", reply_markup=key)
            else:
                bot.send_message(message.chat.id, "Количество не является числом")
        else:
            bot.send_message(message.chat.id, "Укажите количество товаров")