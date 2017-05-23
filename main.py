# coding=utf-8
import logging
import telebot
import config
import db
import utils

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
bot = telebot.TeleBot(config.API_TOKEN)

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


def cat_list(tag):
    keyboard = telebot.types.InlineKeyboardMarkup()
    for cat in db.Category.select():
        keyboard.add(telebot.types.InlineKeyboardButton(text=cat.name, callback_data=tag + str(cat.id)))
    return keyboard


def prod_list(category):
    keyboad = telebot.types.InlineKeyboardMarkup()
    for prod in db.Product.select().where(db.Product.category == db.Category.get(db.Category.id == int(category)),
                                          db.Product.count > 0):
        keyboad.add(telebot.types.InlineKeyboardButton(
            text=prod.title + u" " + config.currency + "{0:.2f}".format(prod.price / 100),
            callback_data="product_" + str(prod.id) + "_" + category))
    return keyboad


def get_price(product):
    return config.currency + "{0:.2f}".format(product.price / 100)


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


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        user, created = db.get_user(call.message.chat)
        save = db.get_user_date(user)
        ers = call.data.split("_")
        # TODO показываем меню
        if call.data == "start":
            key = get_menu()
            bot.send_message(call.message.chat.id, "Выберете пункт меню:", reply_markup=key)
        # TODO показываем список категорий и кнопки редактирования категорий
        if call.data == "shop":
            key = cat_list("category_")
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
                save = db.get_user_date(user)
                save["category"] = ers[1]
                db.set_user_data(user, save)
                if user.is_admin:
                    key.add(telebot.types.InlineKeyboardButton(text="Добавить товар", callback_data="add_product"))
                    key.add(telebot.types.InlineKeyboardButton(text="Переименовать категорию",callback_data="edit_category_rename"))
                key.add(telebot.types.InlineKeyboardButton(text="Категории", callback_data="shop"))
                bot.send_message(call.message.chat.id, "Выберете товар:", reply_markup=key)
        # TODO Показываем фото,описание,цену продукта и кнопки редактирования если пользователь админ
        if ers[0] == "product":
            if len(ers) > 1:
                ut.send_product(call.message.chat,ers[1])

        # TODO Обработка покупки
        if ers[0] == "buy":
            if len(ers) > 1:
                product = db.Product.get(db.Product.id == ers[1])
                order, created = db.Order.get_or_create(user=user, product=product)
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
                bot.register_next_step_handler(msg, ut.process_create_category)
            # TODO запускаем шаги добавления товара
            if ers[1] == "product":
                msg = bot.send_message(call.message.chat.id, "Пришлите фото товара")
                bot.register_next_step_handler(msg, ut.process_create_product_photo)
        # TODO Удаление котегории и товаров
        if ers[0] == "del":
            if ers[1] == "category_":
                key = telebot.types.InlineKeyboardMarkup()
                for cat in db.Category.select():
                    key.add(telebot.types.InlineKeyboardButton(text=cat.name, callback_data="del_cat_" + str(cat.id)))
                key.add(telebot.types.InlineKeyboardButton(text="Категории", callback_data="shop"))
                bot.send_message(call.message.chat.id, "Категория удалится вместе с товарами которые в ней",
                                 reply_markup=key)
            if ers[1] == "cat":
                cat = db.Category.get(db.Category.id == int(ers[2]))
                name = cat.name
                for prod in db.Product.select().where(db.Product.category == cat):
                    prod.delete_instance()
                cat.delete_instance()
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text="Удалить еще категорию", callback_data="del_category"))
                key.add(telebot.types.InlineKeyboardButton(text="Категории", callback_data="shop"))
                bot.send_message(call.message.chat.id, u"Категория " + name + u" и все товары в ней удалены")
        if ers[0] == "edit":
            if ers[1] == "prod":
                save['prod_id'] = ers[3]
                if ers[2] == "img":
                    msg = bot.send_message(call.message.chat.id,"Пришлите новое фото товара:")
                    bot.register_next_step_handler(msg,ut.edit_prod_img)
                if ers[2] == "title":
                    msg = bot.send_message(call.message.chat.id, "Пришлите новое название")
                    bot.register_next_step_handler(msg, ut.edit_prod_title)
                if ers[2] == "desc":
                    msg = bot.send_message(call.message.chat.id, "Пришлите новое описание")
                    bot.register_next_step_handler(msg, ut.edit_prod_description)
                if ers[2] == "price":
                    msg = bot.send_message(call.message.chat.id, "Пришлите новую цену")
                    bot.register_next_step_handler(msg, ut.edit_prod_price)
                if ers[2] == "count":
                    msg = bot.send_message(call.message.chat.id, "Пришлите количество товара")
                    bot.register_next_step_handler(msg, ut.edit_prod_count)
                if ers[2] == "cat":
                    key = cat_list("category_setcat_")
                    bot.send_message(call.message.chat.id, "Выбирите категорию",reply_markup=key)
                if ers[2]=="setcat":
                    prod = db.Product.get(db.Product.id == int(save["prod_id"]))
                    cat = db.Category.get(db.Category.id==int(ers[3]))
                    prod.category=cat
                    prod.save()
                    ut.send_product(call.message.chat,save["prod_id"])
            if ers[1]=="category":
                if ers[2]=="rename":
                    cat = db.Category.get(db.Category.id == int(save["category"]))
                    msg = bot.send_message(call.message.chat.id,u"Пришлите новое имя категории "+cat.name)
                    bot.register_next_step_handler(msg,ut.edit_cat_name)





bot.polling()
