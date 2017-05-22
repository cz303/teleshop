# coding=utf-8
import telebot
import config
from db import *
import logging

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
        keyboard.add(telebot.types.InlineKeyboardButton(text=cat.name, callback_data="category_" + str(cat.id) + "_1"))
    return keyboard


def prod_list(offset, category):
    keyboad = telebot.types.InlineKeyboardMarkup()
    for prod in Product.select().where(Product.category == Category.get(Category.id == int(category)),
                                       Product.count > 0).paginate(int(offset), 20):
        keyboad.add(telebot.types.InlineKeyboardButton(
            text=prod.title + u" " + config.currency + "{0:.2f}".format(prod.price / 100),
            callback_data="product_" + str(prod.id) + "_" + category + "_" + str(offset)))
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
        if call.data == "start":
            key = get_menu()
            bot.send_message(call.message.chat.id, "Выберете пункт меню:", reply_markup=key)
        if call.data == "shop":
            key = cat_list()
            if user.is_admin:
                key.add(telebot.types.InlineKeyboardButton(text="Добавить категорию", callback_data="add_category"))
                key.add(telebot.types.InlineKeyboardButton(text="Удалить категорию", callback_data="del_category"))
            key.add(telebot.types.InlineKeyboardButton(text="Меню", callback_data="start"))
            bot.send_message(call.message.chat.id, "Выберете категорию товара:", reply_markup=key)
        if call.data == "basket":
            key = get_orders_list(user)
            bot.send_message(call.message.chat.id, "Ваша корзина")
        if ers[0] == "category":
            if len(ers) > 1:
                if len(ers) < 3:
                    ers.append(1)
                key = prod_list(ers[2], ers[1])
                save = get_user_date(user)
                save["category"] = ers[1]
                set_user_data(user, save)
                if user.is_admin:
                    key.add(telebot.types.InlineKeyboardButton(text="Добавить товар", callback_data="add_product"))

                if paginarion(ers[2], ers[1]):
                    back = telebot.types.InlineKeyboardButton(text="Назад",
                                                              callback_data="category_" + str(ers[1]) + "_" + str(
                                                                  ers[2]))
                    next = telebot.types.InlineKeyboardButton(text="Вперед",
                                                              callback_data="category_" + str(ers[1]) + "_" + str(
                                                                  int(ers[2]) + 1))
                    key.row(back, next)
                key.add(telebot.types.InlineKeyboardButton(text="Категории", callback_data="shop"))
                bot.send_message(call.message.chat.id, "Выберете товар:", reply_markup=key)
        if ers[0] == "product":
            if len(ers) > 1:
                product = Product.get(Product.id == int(ers[1]))
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text=u"Добавить в корзину " + get_price(product),
                                                           callback_data="buy_" + str(product.id)))
                key.add(
                    telebot.types.InlineKeyboardButton(text="Назад", callback_data="category_" + ers[2] + "_" + ers[3]))
                bot.send_photo(call.message.chat.id, photo=product.img, caption=product.description, reply_markup=key)
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
        if ers[0] == "add":
            if ers[1] == "category":
                msg = bot.send_message(call.message.chat.id, "Введите название категории")
                bot.register_next_step_handler(msg, process_create_category)
            if ers[1] == "product":
                msg = bot.send_message(call.message.chat.id, "Пришлите фото товара")
                bot.register_next_step_handler(msg, process_create_product_photo)


bot.polling()
