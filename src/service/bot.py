import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, ConversationHandler, CallbackQueryHandler, CallbackContext
import config
from src.service import university
import datetime
from bs4 import BeautifulSoup
from datetime import date
from src.dto import calendarTable


class TelegramBot:
    def __init__(self):
        self.sessions = {}
        updater = Updater(token=config.token, use_context=True)
        dispatcher = updater.dispatcher
        help_handler = CommandHandler('help', self.help)
        dispatcher.add_handler(help_handler)
        login_handler = CommandHandler('login', self.login)
        dispatcher.add_handler(login_handler)
        calendar_handler = CommandHandler('calendar', self.calendar)
        dispatcher.add_handler(calendar_handler)
        dispatcher.add_handler(CallbackQueryHandler(self.calendar))
        updater.start_polling()

    def help(self, update, context):
        if update.effective_chat.id not in self.sessions:
            service = university.University()
            self.sessions[update.effective_chat.id] = service

        self.clearScreen(update, context)
        self.sessions[update.effective_chat.id].messages_to_delete.append(update.message)
        message = context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Привет\! Хочешь узнать расписание\? \n *Вот доступные команды:* \n 1\. /login Логин "
                                      "Пароль \- использется для авторизации в ЛК \n 2\. /calendar \- Узнать расписание "
                                      "на сегодня", parse_mode='MarkdownV2')
        self.sessions[update.effective_chat.id].messages_to_delete.append(message)

    def login(self, update, context):
        if update.effective_chat.id not in self.sessions:
            service = university.University()
            self.sessions[update.effective_chat.id] = service

        self.clearScreen(update, context)
        context.bot.delete_message(chat_id=update.effective_chat.id,
                                   message_id=update.message['message_id'])
        if len(context.args) != 2:
            message = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text='Неверный формат❗❗❗ \n Пример: "Логин Пароль"')
            self.sessions[update.effective_chat.id].messages_to_delete.append(message)
            return
        if self.sessions[update.effective_chat.id].login(context.args[0], context.args[1]):
            message = context.bot.send_message(chat_id=update.effective_chat.id, text='Авторизация успешна! 🔓')
        else:
            message = context.bot.send_message(chat_id=update.effective_chat.id, text='Ошибка авторизации 🔒')
        self.sessions[update.effective_chat.id].messages_to_delete.append(message)

    def clearScreen(self, update, context):
        for message in self.sessions[update.effective_chat.id].messages_to_delete:
            context.bot.delete_message(chat_id=update.effective_chat.id,
                                       message_id=message['message_id'])
        self.sessions[update.effective_chat.id].messages_to_delete = []

    def calendar(self, update, context):
        if update.effective_chat.id not in self.sessions:
            service = university.University()
            self.sessions[update.effective_chat.id] = service

        self.clearScreen(update, context)
        if update.message is not None:
            self.sessions[update.effective_chat.id].messages_to_delete.append(update.message)
        week_day = 0

        query = update.callback_query
        if query is not None:
            query.answer()
            choice = query.data
            week_day = int(choice)
            self.process_calendar(update, context, week_day, query.message)
        else:
            self.process_calendar(update, context, week_day)

    def process_calendar(self, update: Update, context: CallbackContext, week_day, message=None):
        today = date.today()
        check_day = today + datetime.timedelta(days=week_day)
        next_day = today + datetime.timedelta(days=week_day + 1)
        response = self.sessions[update.effective_chat.id].getCalendarData(check_day.strftime("%Y-%m-%d"),
                                                                           next_day.strftime("%Y-%m-%d"))
        if response is None:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Нужно авторизоваться! 🔑🔑🔑, используйте команду /login')
            return
        self.parseDate(context, update, response, check_day.strftime("%Y-%m-%d"))
        keyboard = [
            [
                InlineKeyboardButton("< 1", callback_data=str(week_day - 1)),
                InlineKeyboardButton("> 1", callback_data=str(week_day + 1)),
            ],
            [
                InlineKeyboardButton("<< 7", callback_data=str(week_day - 7)),
                InlineKeyboardButton(">> 7", callback_data=str(week_day + 7)),
            ],
            [InlineKeyboardButton("Сегодня", callback_data='0')],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        if message is None:
            message = update.message.reply_text('Навигация:', reply_markup=reply_markup)
            self.sessions[update.effective_chat.id].messages_to_delete.append(message)
        else:
            message = message.reply_text('Навигация:', reply_markup=reply_markup)
            self.sessions[update.effective_chat.id].messages_to_delete.append(message)

    def parseDate(self, context, update, dateInfo, current_date):
        message = context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='<b>📆 Дата:' + current_date + '</b>', parse_mode='html')
        self.sessions[update.effective_chat.id].messages_to_delete.append(message)
        if len(dateInfo) == 0:
            message = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text='В этот день занятий нет!')
            self.sessions[update.effective_chat.id].messages_to_delete.append(message)
            return

        for item in dateInfo:
            html_to_parse = self.sessions[update.effective_chat.id].getPageToParse(item['url'])
            table = self.parseTable(html_to_parse)
            result = self.formatCalendar(table)
            message = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text=result, parse_mode='html')
            self.sessions[update.effective_chat.id].messages_to_delete.append(message)

    def parseTable(self, html):
        soup = BeautifulSoup(html)
        table = soup.find("table", {"id": "w0"})
        rows = table.find_all('tr')
        calendar = calendarTable.CalendarTable()
        for row in rows:
            header = row.find('th')
            value = row.find('td')
            if header.contents[0] == 'Преподаватель':
                calendar.teacher = value.text.strip()
            if header.contents[0] == 'Дисциплина':
                calendar.subject = value.text.strip()
            if header.contents[0] == 'Вид занятия':
                calendar.type = value.text.strip()
            if header.contents[0] == 'Время проведения занятия':
                calendar.time = value.text.strip()
            if header.contents[0] == 'Место проведения занятия':
                calendar.place = value.text.strip()

        return calendar

    def formatCalendar(self, calendar):
        result = ''
        result += '🧑‍🏫 <b>Преподаватель:</b> ' + calendar.teacher + '\n'
        result += '✏ <b>Дисциплина:</b> ' + calendar.subject + '\n'
        result += '📖 Вид занятия: ' + calendar.type + '\n'
        result += '⏳ Время проведения занятия: ' + calendar.time + '\n'
        result += '📍 <i>Место проведения занятия:</i> ' + calendar.place + '\n'
        return result
