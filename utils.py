# coding=utf-8
import telebot

import config


class Util:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    def process_create_category(self, message):
        user, create = self.db.get_user(message.chat)
        if user.is_admin:
            if message.text is not None:
                cat_name = message.text
                self.db.Category.create(name=cat_name)
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text="Категории", callback_data="shop"))
                self.bot.send_message(message.chat.id, u"Категория " + message.text + u" добавлена", reply_markup=key)
            else:
                msg = self.bot.reply_to(message, "Не приемлемое название категории")
                self.bot.register_next_step_handler(msg, self.process_create_category)

    def process_create_product_photo(self, message):
        user, create = self.db.get_user(message.chat)
        if user.is_admin:
            if message.photo is not None:
                save = self.db.get_user_date(user)
                file_id = message.photo[-1].file_id
                cat = self.db.Category.get(self.db.Category.id == int(save["category"]))
                prod = self.db.Product.create(img=file_id, category=cat)
                save["prod_id"] = prod.id
                self.db.set_user_data(user, save)
                msg = self.bot.send_message(message.chat.id, "Введите имя товара: ")
                self.bot.register_next_step_handler(msg, self.process_create_product_title)
            else:
                msg = self.bot.send_message(message.chat.id, "Не могу найти фото")
                self.bot.register_next_step_handler(msg, self.process_create_product_photo)

    def process_create_product_title(self, message):
        user, create = self.db.get_user(message.chat)
        if user.is_admin:
            if message.text is not None > 0:
                save = self.db.get_user_date(user)
                prod = self.db.Product.get(self.db.Product.id == int(save["prod_id"]))
                prod.title = message.text
                prod.save()
                msg = self.bot.send_message(message.chat.id, "Введите описание товара 200 символов:")
                self.bot.register_next_step_handler(msg, self.process_create_product_description)
            else:
                msg = self.bot.send_message(message.chat.id, "Не могу найти имя товара:")
                self.bot.register_next_step_handler(msg, self.process_create_product_title)

    def process_create_product_description(self, message):
        user, create = self.db.get_user(message.chat)
        if user.is_admin:
            if message.text is not None:
                save = self.db.get_user_date(user)
                prod = self.db.Product.get(self.db.Product.id == int(save["prod_id"]))
                prod.description = message.text
                prod.save()
                msg = self.bot.send_message(message.chat.id, "Укажите цену товара пример: 3.22")
                self.bot.register_next_step_handler(msg, self.process_create_product_price)
            else:
                msg = self.bot.send_message(message.chat.id, "Укажите описание товара")
                self.bot.register_next_step_handler(msg, self.process_create_product_description)

    def process_create_product_price(self, message):
        user, create = self.db.get_user(message.chat)
        if user.is_admin:
            if message.text is not None:
                try:
                    save = self.db.get_user_date(user)
                    prod = self.db.Product.get(self.db.Product.id == int(save["prod_id"]))
                    prod.price = int(float(message.text.replace(",", ".").strip()) * 100)
                    prod.save()
                    msg = self.bot.send_message(message.chat.id, "Укажите количество товаров: 3")
                    self.bot.register_next_step_handler(msg, self.process_create_product_count)
                except:
                    msg = self.bot.send_message(message.chat.id, "Цена не является числом")
                    self.bot.register_next_step_handler(msg, self.process_create_product_price)
            else:
                msg = self.bot.send_message(message.chat.id, "Укажите цену товара")
                self.bot.register_next_step_handler(msg, self.process_create_product_price)

    def process_create_product_count(self, message):
        user, create = self.db.get_user(message.chat)
        if user.is_admin:
            if message.text is not None:
                if message.text.isdigit():
                    try:
                        save = self.db.get_user_date(user)
                        prod = self.db.Product.get(self.db.Product.id == int(save["prod_id"]))
                        prod.count = int(message.text.strip())
                        prod.save()
                        key = telebot.types.InlineKeyboardMarkup()
                        key.add(
                            telebot.types.InlineKeyboardButton(text=u"Добавить еще товар", callback_data="add_product"))
                        key.add(telebot.types.InlineKeyboardButton(
                            text=u"Посмотреть товары в категории " + self.db.Category.get(
                                self.db.Category.id == int(save["category"])).name,
                            callback_data="category_" + save["category"] + "_1"))
                        self.bot.send_message(message.chat.id, u"Товар " + prod.title + u" успешно добавлен",
                                              reply_markup=key)
                    except:
                        msg = self.bot.send_message(message.chat.id, "Количество не является числом")
                        self.bot.register_next_step_handler(msg, self.process_create_product_count)
                else:
                    msg = self.bot.send_message(message.chat.id, "Количество не является числом")
                    self.bot.register_next_step_handler(msg, self.process_create_product_count)
            else:
                msg = self.bot.send_message(message.chat.id, "Укажите количество товаров")
                self.bot.register_next_step_handler(msg, self.process_create_product_count)

    def get_price(self, product):
        if product.price is not None:
            return config.currency + "{0:.2f}".format(product.price / 100)
        else:
            return config.currency + u"0"

    def edit_prod_img(self, message):
        user, cre = self.db.get_user(message.chat)
        save = self.db.get_user_date(user)
        if user.is_admin:
            if message.text is not None:
                file_id = message.photo[-1].file_id
                prod = self.db.Product.get(self.db.Product.id == int(save["prod_id"]))
                prod.img = file_id
                prod.save()
                self.send_product(message.chat, prod.id)
            else:
                msg = self.bot.send_message(message.chat.id, "Не могу найти фото")
                self.bot.register_next_step_handler(msg, self.edit_prod_img)

    def edit_prod_title(self, message):
        user, cre = self.db.get_user(message.chat)
        save = self.db.get_user_date(user)
        if user.is_admin:
            if message.text is not None:
                prod = self.db.Product.get(self.db.Product.id == int(save["prod_id"]))
                prod.title = message.text
                prod.save()
                self.send_product(message.chat, prod.id)
            else:
                msg = self.bot.send_message(message.chat.id, "Некоректно указан текст")
                self.bot.register_next_step_handler(msg, self.edit_prod_title)

    def edit_prod_description(self, message):
        user, cre = self.db.get_user(message.chat)
        save = self.db.get_user_date(user)
        if user.is_admin:
            if message.text is not None:
                prod = self.db.Product.get(self.db.Product.id == int(save["prod_id"]))
                prod.description = message.text
                prod.save()
                self.send_product(message.chat, prod.id)
            else:
                msg = self.bot.send_message(message.chat.id, "Некоректно указан текст")
                self.bot.register_next_step_handler(msg, self.edit_prod_description)

    def edit_prod_price(self, message):
        user, cre = self.db.get_user(message.chat)
        save = self.db.get_user_date(user)
        if user.is_admin:
            if message.text is not None:
                try:
                    prod = self.db.Product.get(self.db.Product.id == int(save["prod_id"]))
                    prod.price = int(float(message.text.replace(",", ".").strip()) * 100)
                    prod.save()
                    self.send_product(message.chat, prod.id)
                except:
                    msg = self.bot.send_message(message.chat.id, "Цена не является числом")
                    self.bot.register_next_step_handler(msg, self.edit_prod_price)
            else:
                msg = self.bot.send_message(message.chat.id, "Некоректно указан текст")
                self.bot.register_next_step_handler(msg, self.edit_prod_price)

    def edit_prod_count(self, message):
        user, cre = self.db.get_user(message.chat)
        save = self.db.get_user_date(user)
        if user.is_admin:
            if message.text is not None:
                if message.text.isdigit():
                    prod = self.db.Product.get(self.db.Product.id == int(save["prod_id"]))
                    prod.count = int(message.text.strip())
                    prod.save()
                    self.send_product(message.chat, prod.id)
                else:
                    msg = self.bot.send_message(message.chat.id, "Количество не является числом")
                    self.bot.register_next_step_handler(msg, self.edit_prod_count)
            else:
                msg = self.bot.send_message(message.chat.id, "Укажите количество товаров")
                self.bot.register_next_step_handler(msg, self.edit_prod_count)

    def edit_cat_name(self, message):
        user, cre = self.db.get_user(message.chat)
        save = self.db.get_user_date(user)
        if user.is_admin:
            cat = self.db.Category.get(self.db.Category.id == int(save["category"]))
            oldname = cat.name
            cat.name = message.text
            cat.save()
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text="К категории", callback_data="category_" + str(cat.id)))
            self.bot.send_message(message.chat.id, u"Категория " + oldname + u" переименована в " + message.text,
                                  reply_markup=key)

    def send_product(self, chat, id):
        user, cre = self.db.get_user(chat)
        product = self.db.Product.get(self.db.Product.id == int(id))
        key = telebot.types.InlineKeyboardMarkup()
        if user.is_admin:
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
            text=u"Добавить в корзину " + self.get_price(product) + u" " + str(product.count),
            callback_data="buy_" + str(product.id)))
        key.add(
            telebot.types.InlineKeyboardButton(text="Назад", callback_data="category_" + str(product.category.id)))
        self.bot.send_photo(chat.id, photo=product.img, caption=product.description, reply_markup=key)
