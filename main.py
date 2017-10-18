#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot to reply to Telegram messages
# This program is dedicated to the public domain under the CC0 license.

import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import os

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

class TeleBot(object):
    def __init__(self, api_token):
        self.api_token = api_token
        self.users_states = {}
        self.admins_names = ["Fogizz"]
        self.admins = {}
        self.picup = u"איסוף עצמי"
        self.delivery = u"משלוח"
        self.cancel_text = u"בטל הזמנה"
        self.orders = {1: ["3", 300],
                       2: ["5", 500],
                       3: ["10", 900],
                       4: ["15", 1300],
                       5: ["20", 1700]}
        self.cmd_channel = None

        self.updater = Updater(api_token)
        # Get the dispatcher to register handlers
        self.dp = self.updater.dispatcher

        # on different commands - answer in Telegram
        self.dp.add_handler(CommandHandler("start", self.start))
        self.dp.add_handler(CommandHandler("exit", self.bot_exit))

        # on noncommand i.e message - echo the message on Telegram
        self.dp.add_handler(MessageHandler(Filters.text, self.echo))
        self.dp.add_handler(MessageHandler(Filters.photo, self.recv_photos))

        # log all errors
        self.dp.add_error_handler(self.error)

    def run(self):
        # Start the Bot
        print("Start Server")
        self.updater.start_polling(poll_interval=1.0, timeout=30, read_latency=1.0)

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        self.updater.idle()

    def check_admin(self, update):
        username = update.message.from_user.username
        if username in self.admins_names:
            self.admins[username] = update

    def start(self, bot, update):
        username = update.message.from_user.username
        self.check_admin(update)
        self.users_states[username] = {}
        self.users_states[username]["state"] = 1
        text = u"שלום " + username + "\n"
        text += u"הגעת לבוט ההזמנות האוטומטי של פוגיזז" + "\n"
        text += u"האם תרצה איסוף עצמי או משלוח?" + "\n"
        text += u"עלות משלוח היא 50 שח"

        kb = [[telegram.KeyboardButton(self.picup)],
              [telegram.KeyboardButton(self.delivery)]]
        kb_markup = telegram.ReplyKeyboardMarkup(kb, resize_keyboard=True)
        bot.send_message(chat_id=update.message.chat_id,
                         text=text,
                         reply_markup=kb_markup)

    def send_message(self, update, text):
        update.message.reply_text(text)

    def bot_exit(self, bot, update):
        update.message.reply_text('Server closed')
        print("Server closed, please exit by Ctrl + C")
        self.updater.stop()
        exit()

    def error(self, bot, update, error):
        logger.warn('Update "%s" caused error "%s"' % (update, error))

    def echo(self, bot, update):
        if update.message is not None:
            if update.message.chat.type != "private":
                return
            username = update.message.from_user.username
            self.check_admin(update)
            if username not in self.users_states:
                self.start(bot, update)
                return
            if self.users_states[username]["state"] == 1:
                msg = update.message.text
                if msg == self.picup:
                    self.users_states[username]["service"] = "pickup"
                    self.users_states[username]["state"] = 2
                    text = u"בחרת איסוף עצמי." + "\n"
                    text += u"לביטול שלח הודעה עם Cancel"
                    kb_markup = telegram.ReplyKeyboardRemove(True)
                    bot.send_message(chat_id=update.message.chat_id,
                                     text=text,
                                     reply_markup=kb_markup)
                    self.start_order(bot, update)
                elif msg == self.delivery:
                    self.users_states[username]["service"] = "delivery"
                    self.users_states[username]["state"] = 2
                    text = u"בחרת משלוח." + "\n"
                    text += u"לביטול שלח הודעה עם " + self.cancel_text
                    kb_markup = telegram.ReplyKeyboardRemove(True)
                    bot.send_message(chat_id=update.message.chat_id,
                                     text=text,
                                     reply_markup=kb_markup)
                    self.start_order(bot, update)
                else:
                    text = u"תבחר אחת מהאפשרויות מהתפריט."
                    kb = [[telegram.KeyboardButton(self.picup)],
                          [telegram.KeyboardButton(self.delivery)]]
                    kb_markup = telegram.ReplyKeyboardMarkup(kb, resize_keyboard=True)
                    bot.send_message(chat_id=update.message.chat_id,
                                     text=text,
                                     reply_markup=kb_markup)
            elif self.users_states[username]["state"] == 2:
                msg = update.message.text
                if msg == self.cancel_text:
                    self.users_states[username] = {}
                    text = u"ההזמנה בוטלה."
                    kb_markup = telegram.ReplyKeyboardRemove(True)
                    bot.send_message(chat_id=update.message.chat_id,
                                     text=text,
                                     reply_markup=kb_markup)
                    self.start(bot, update)
                    return
                for key, val in sorted(self.orders.items()):
                    if msg == val[0]:
                        text = u"בחרת לקנות " + val[0] + u" גרם" +"\n"
                        text += u"לאישור ההזמנה נצטרך לאשר את זהותך. " + "\n"
                        text += u"שלח תמונה של תעודה מזהה או רישיון נהיגה עם כל הפרטים גלויים." + "\n"
                        self.users_states[username]["grams"] = key
                        self.users_states[username]["state"] = 3
                        kb_markup = telegram.ReplyKeyboardRemove(True)
                        bot.send_message(chat_id=update.message.chat_id,
                                         text=text,
                                         reply_markup=kb_markup)
                        return
                text = u"ההודעה שהוכנסה לא מוכרת למערכת, נסה שנית." + "\n"
                text += u"על מנת להתחיל את ההזמנה אנא בחר כמות להזמנה: " + "\n"
                kb = [[telegram.KeyboardButton(self.cancel_text)]]
                for key, val in sorted(self.orders.items()):
                    if self.users_states[username]["service"] == "delivery":
                        text += val[0] + " gram: " + str(val[1] + 50) + "\n"
                    else:
                        text += val[0] + " gram: " + str(val[1]) + "\n"
                    kb.append([telegram.KeyboardButton(val[0])])
                kb_markup = telegram.ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)
                bot.send_message(chat_id=update.message.chat_id,
                                 text=text,
                                 reply_markup=kb_markup)
            elif self.users_states[username]["state"] == 3:
                text = u"הגעת לשלב האימות, שלח תמונה של תעודה מזהה או רישיון נהיגה עם כל הפרטים גלויים"
                kb_markup = telegram.ReplyKeyboardRemove(True)
                bot.send_message(chat_id=update.message.chat_id,
                                 text=text,
                                 reply_markup=kb_markup)
            elif self.users_states[username]["state"] == 4:
                text = u"שלח בבקשה תצלום מסך של הפרופיל שלך בפייסבוק, לינק לא יתקבל."
                kb_markup = telegram.ReplyKeyboardRemove(True)
                bot.send_message(chat_id=update.message.chat_id,
                                 text=text,
                                 reply_markup=kb_markup)
            elif self.users_states[username]["state"] == 5:
                text = u"שלח בבקשה סלפי מחזיק פתק עם תאריך ושעה בזמן ההזמנה."
                kb_markup = telegram.ReplyKeyboardRemove(True)
                bot.send_message(chat_id=update.message.chat_id,
                                 text=text,
                                 reply_markup=kb_markup)
            elif self.users_states[username]["state"] == 6:
                msg = update.message.text
                text = u"כמעט סיימת לבצע את ההזמנה, נשאר רק לאמת פעם אחרונה את הפרטים וההזמנה בדרך אליכם!" + "\n"
                if self.users_states[username]["service"] == "pickup":
                    text += u"ברצונכם לאסוף "
                else:
                    text += u"ברצונכם לבצע משלוח של "
                grams_key = self.users_states[username]["grams"]
                text += self.orders[grams_key][0]
                text += u" גרם במחיר "
                if self.users_states[username]["service"] == "delivery":
                    text += str(self.orders[grams_key][1] + 50) + "\n"
                else:
                    text += str(self.orders[grams_key][1]) + "\n"

                self.users_states[username]["addr"] = msg
                text += u"הכתובת והמספר טלפון הם: " + "\n"
                text += self.users_states[username]["addr"] + "\n"
                text += u"התמונות שקיבלנו ממך הן:"
                kb_markup = telegram.ReplyKeyboardRemove(True)
                bot.send_message(chat_id=update.message.chat_id,
                                 text=text,
                                 reply_markup=kb_markup)
                bot.send_photo(update.message.chat_id, photo=open(str(username+"_1.jpg"), 'rb'))
                bot.send_photo(update.message.chat_id, photo=open(str(username+"_2.jpg"), 'rb'))
                bot.send_photo(update.message.chat_id, photo=open(str(username+"_3.jpg"), 'rb'))
                text = u"האם אתה מאשר את הזמנתך?"
                kb = [[telegram.KeyboardButton(u"מאשר")],
                      [telegram.KeyboardButton(u"ביטול")]]
                kb_markup = telegram.ReplyKeyboardMarkup(kb, resize_keyboard=True)
                bot.send_message(chat_id=update.message.chat_id,
                                 text=text,
                                 reply_markup=kb_markup)
                self.users_states[username]["state"] = 7
            elif self.users_states[username]["state"] == 7:
                msg = update.message.text
                confirm = False
                if msg == u"מאשר":
                    text = u"הזמנתך התקבלה, תודה רבה שפנית אלינו!"
                    confirm = True
                elif msg == u"ביטול":
                    text = u"הזמנתך התבטלה"
                else:
                    text = u"הטקסט שהוכנס לא תקין, הזמנתך התבטלה"
                kb_markup = telegram.ReplyKeyboardRemove(True)
                bot.send_message(chat_id=update.message.chat_id,
                                 text=text,
                                 reply_markup=kb_markup)
                if confirm:
                    if self.cmd_channel is not None:
                        text = u"התקבלה הזמנה חדשה מהמשתמש " + username + "\n"
                        text += u"סוג ההזמנה: "
                        if self.users_states[username]["service"] == "pickup":
                            text += u"איסוף עצמי "
                        else:
                            text += u"משלוח "
                        text += "\n"
                        grams_key = self.users_states[username]["grams"]
                        text += u"כמות לרכישה: " + self.orders[grams_key][0]
                        text += u" גרם במחיר "
                        if self.users_states[username]["service"] == "delivery":
                            text += str(self.orders[grams_key][1]+50) + "\n"
                        else:
                            text += str(self.orders[grams_key][1]) + "\n"
                        text += u"הכתובת והמספר טלפון הם: " + "\n"
                        text += self.users_states[username]["addr"] + "\n"
                        text += u"התמונות שקיבלנו ממך הן:"
                        bot.send_message(chat_id="-1001133757984",
                                         text=text)
                        bot.send_photo("-1001133757984", photo=open(str(username + "_1.jpg"), 'rb'))
                        bot.send_photo("-1001133757984", photo=open(str(username + "_2.jpg"), 'rb'))
                        bot.send_photo("-1001133757984", photo=open(str(username + "_3.jpg"), 'rb'))
                    else:
                        text = u"תקלה במערכת, נסה שוב מאוחר יותר."
                        kb_markup = telegram.ReplyKeyboardRemove(True)
                        bot.send_message(chat_id=update.message.chat_id,
                                         text=text,
                                         reply_markup=kb_markup)
                self.start(bot, update)
                os.remove(str(username + "_1.jpg"))
                os.remove(str(username + "_2.jpg"))
                os.remove(str(username + "_3.jpg"))
        elif update.channel_post.chat.type == "channel":
            if update.channel_post.chat.title == "FogizzControlCenter":
                self.cmd_channel = update.channel_post


    def recv_photos(self, bot, update):
        username = update.message.from_user.username
        self.check_admin(update)
        # for key, val in self.admins.items():
        # bot.send_photo(val.message.chat_id, photo=newFile)
        if username not in self.users_states:
            self.start(bot, update)
            return
        if self.users_states[username]["state"] == 3:
            if "pic_counter" not in self.users_states[username]:
                self.users_states[username]["pic_counter"] = 0
            self.users_states[username]["pic_counter"] += 1
            self.users_states[username]["state"] = 4
            file_id = update.message.photo[-1].file_id
            newFile = bot.getFile(file_id)
            newFile.download(username + "_" + str(self.users_states[username]["pic_counter"]) + ".jpg")
            text = u"שלח בבקשה תצלום מסך של הפרופיל שלך בפייסבוק, לינק לא יתקבל."
            update.message.reply_text(text)
        elif self.users_states[username]["state"] == 4:
            if "pic_counter" not in self.users_states[username]:
                self.users_states[username]["pic_counter"] = 0
            self.users_states[username]["pic_counter"] += 1
            self.users_states[username]["state"] = 5
            file_id = update.message.photo[-1].file_id
            newFile = bot.getFile(file_id)
            newFile.download(username + "_" + str(self.users_states[username]["pic_counter"]) + ".jpg")
            text = u"שלח בבקשה סלפי מחזיק פתק עם תאריך ושעה בזמן ההזמנה."
            update.message.reply_text(text)
        elif self.users_states[username]["state"] == 5:
            if "pic_counter" not in self.users_states[username]:
                self.users_states[username]["pic_counter"] = 0
            self.users_states[username]["pic_counter"] += 1
            self.users_states[username]["state"] = 6
            file_id = update.message.photo[-1].file_id
            newFile = bot.getFile(file_id)
            newFile.download(username + "_" + str(self.users_states[username]["pic_counter"]) + ".jpg")
            text = u"תרשום בהודעה כתובת מדוייקת ומספר פלאפון."
            update.message.reply_text(text)
        else:
            text = u"באפשרותך לשלוח תמונה רק בזמן אימות הפרטים."
            update.message.reply_text(text)
            self.start(bot, update)
            return

    def start_order(self, bot, update):
        username = update.message.from_user.username
        text = u"בסיום אימות הפרטים עם הבוט יש לחכות להודעת אישור בדיקת הפרטים ושליחת ההזמנה מנציג שירות אנושי, תהליך זה עשוי לקחת מספר דקות בשעות הפעילות." + "\n"
        #text += u"על מנת להתחיל את ההזמנה אנא שלח/י תמונת סלפי כשאת/ה מחזיק/ה תעודת זהות/רישיון נהיגה/דרכון. נא לשים לב שהתמונה ברורה."
        text += u"על מנת להתחיל את ההזמנה אנא בחר כמות להזמנה: " + "\n"
        kb = [[telegram.KeyboardButton(self.cancel_text)]]
        for key, val in sorted(self.orders.items()):
            if self.users_states[username]["service"] == "delivery":
                text += val[0] + " gram: " + str(val[1] +50) +"\n"
            else:
                text += val[0] + " gram: " + str(val[1]) +"\n"
            kb.append([telegram.KeyboardButton(val[0])])
        kb_markup = telegram.ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)
        bot.send_message(chat_id=update.message.chat_id,
                         text=text,
                         reply_markup=kb_markup)

if __name__ == '__main__':
    telebot = TeleBot("360267122:AAHmCyriJwzBpt5IsUIquGAxdkMtyor8xSk")
    telebot.run()
