from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import config
from src.service import university
import datetime
from bs4 import BeautifulSoup
from datetime import date
from src.dto import calendarTable
from formattingRoutine import format_msg, get_week_day, format_calendar, formatTasks


class TelegramBot:
    def __init__(self):
        self.sessions = {}
        updater = Updater(token=config.token, use_context=True)
        dispatcher = updater.dispatcher

        help_handler = CommandHandler('help', self.help)
        dispatcher.add_handler(help_handler)

        start_handler = CommandHandler('start', self.help)
        dispatcher.add_handler(start_handler)

        login_handler = CommandHandler('login', self.login)
        dispatcher.add_handler(login_handler)

        calendar_handler = CommandHandler('calendar', self.calendar)
        dispatcher.add_handler(calendar_handler)

        dispatcher.add_handler(CallbackQueryHandler(self.calendar))
        while True:
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
                                                "на сегодня \n По всем вопросам обращайтесь на почту: contact@babunov.dev",
                                           parse_mode='MarkdownV2')
        self.sessions[update.effective_chat.id].messages_to_delete.append(message)

    def is_Authorized(self, id):
        today = date.today()
        loginCheck = self.sessions[id].getCalendarData(today.strftime("%Y-%m-%d"),
                                                       today.strftime("%Y-%m-%d"))
        return loginCheck is not None

    def login(self, update, context):
        if update.effective_chat.id not in self.sessions:
            service = university.University()
            self.sessions[update.effective_chat.id] = service

        self.clearScreen(update, context)
        context.bot.delete_message(chat_id=update.effective_chat.id,
                                   message_id=update.message['message_id'])
        if len(context.args) != 2:
            message = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text='Неверный формат❗❗❗ \n Пример: /login [Логин] [Пароль]')
            self.sessions[update.effective_chat.id].messages_to_delete.append(message)
            return

        if self.is_Authorized(update.effective_chat.id):
            message = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text='Вы уже авторизованы! 🔓')
            self.sessions[update.effective_chat.id].messages_to_delete.append(message)
            return

        if self.sessions[update.effective_chat.id].login(context.args[0], context.args[1]):
            message = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text='Авторизация успешна! 🔓 \n Теперь вы можете использовать команду /calendar')
        else:
            message = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text='Ошибка авторизации 🔒 \n Проверьте логин и пароль.')
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

            if choice.split()[0] == 'msg':
                split = choice.split()
                ids = [split[2], split[3], split[4]]
                self.process_msgs(update, context, split[1], ids)
            else:
                week_day = int(choice)
                self.process_calendar(update, context, week_day, query.message)
        else:
            self.process_calendar(update, context, week_day)

    def create_navigation_keyboard(self, week_day):
        keyboard = [
            [
                InlineKeyboardButton("◀", callback_data=str(week_day - 1)),
                InlineKeyboardButton("▶", callback_data=str(week_day + 1)),
            ],
            [
                InlineKeyboardButton("⏮", callback_data=str(week_day - 7)),
                InlineKeyboardButton("⏭", callback_data=str(week_day + 7)),
            ],
            [InlineKeyboardButton("Сегодня ↩", callback_data='0')],
        ]

        return InlineKeyboardMarkup(keyboard)

    def process_calendar(self, update: Update, context: CallbackContext, week_day, message=None):
        self.sessions[update.effective_chat.id].offset = week_day
        today = date.today()
        check_day = today + datetime.timedelta(days=week_day)
        next_day = today + datetime.timedelta(days=week_day + 1)
        response = self.sessions[update.effective_chat.id].getCalendarData(check_day.strftime("%Y-%m-%d"),
                                                                           next_day.strftime("%Y-%m-%d"))
        if response is None:
            message = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text='Нужно авторизоваться! 🔑🔑🔑, используйте команду \n /login [Логин] [Пароль]')
            self.sessions[update.effective_chat.id].messages_to_delete.append(message)
            return
        self.parse_date(context, update, response, check_day)

        reply_markup = self.create_navigation_keyboard(week_day)

        if message is None:
            message = update.message.reply_text('Навигация:', reply_markup=reply_markup)
            self.sessions[update.effective_chat.id].messages_to_delete.append(message)
        else:
            message = message.reply_text('Навигация:', reply_markup=reply_markup)
            self.sessions[update.effective_chat.id].messages_to_delete.append(message)

    def parse_date(self, context, update, dateInfo, current_date):
        self.sessions[update.effective_chat.id].messages_to_show = {}
        # self.sessions[update.effective_chat.id].short_cache = []
        message = context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='<b>📆 Дата:' + current_date.strftime(
                                               "%d.%m.%Y") + ' ' + get_week_day(current_date.weekday()) + '</b>',
                                           parse_mode='html')
        self.sessions[update.effective_chat.id].messages_to_delete.append(message)
        # self.sessions[update.effective_chat.id].short_cache.append(message.text_html)
        if len(dateInfo) == 0:
            message = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text='<b>В этот день занятий нет!</b> 😎',
                                               parse_mode='html')
            self.sessions[update.effective_chat.id].messages_to_delete.append(message)
            return

        for item in dateInfo:
            html_to_parse = self.sessions[update.effective_chat.id].getPageToParse(item['url'])
            table = self.parse_table(html_to_parse)
            taskId = self.get_task_id(html_to_parse)
            msgs_ids = self.get_msg_id(html_to_parse)
            messages = self.sessions[update.effective_chat.id].getMessagesToParse(msgs_ids)
            table.msg_ids = ' '.join(msgs_ids)
            self.sessions[update.effective_chat.id].messages_to_show[' '.join(msgs_ids)] = messages
            if taskId is not None:
                tasksToFormat = self.sessions[update.effective_chat.id].getTasksToParse(taskId)
                table = formatTasks(tasksToFormat, table)
            result = format_calendar(self, update, table, messages)
            if len(messages) > 0:
                delta = current_date - datetime.date.today()
                keyboard = [
                    [InlineKeyboardButton("Сообщения",
                                          callback_data='msg {days} {id0} {id1} {id2}'.format(days=delta.days,
                                                                                              id0=msgs_ids[0],
                                                                                              id1=msgs_ids[1],
                                                                                              id2=msgs_ids[2]))],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                message = context.bot.send_message(chat_id=update.effective_chat.id,
                                                   text=result, parse_mode='html', reply_markup=reply_markup)
            else:
                message = context.bot.send_message(chat_id=update.effective_chat.id,
                                                   text=result, parse_mode='html')
            self.sessions[update.effective_chat.id].messages_to_delete.append(message)
            # self.sessions[update.effective_chat.id].short_cache.append(result)
            # self.sessions[update.effective_chat.id].context = context

    def get_task_id(self, html):
        soup = BeautifulSoup(html)
        taskGrid = soup.find('div', {'ng-modules': 'DistanceLearning'}).find('div', {'class': 'grid-view'})
        if taskGrid is not None:
            taskIdToParse = taskGrid.attrs['ng-init']
            return taskIdToParse[taskIdToParse.find("(") + 1:taskIdToParse.find(")")]
        return None

    def get_msg_id(self, html):
        soup = BeautifulSoup(html)
        distanceLearningGrid = soup.find('div', {'ng-modules': 'DistanceLearning'})
        if distanceLearningGrid is not None:
            IdBlockToParse = distanceLearningGrid.attrs['ng-init']
            return IdBlockToParse[IdBlockToParse.find("(") + 1:IdBlockToParse.find(")")].split(', ')
        return None

    def parse_table(self, html):
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

    def process_msgs(self, update, context, offset, ids):
        key = ' '.join(ids)
        lst = self.sessions[update.effective_chat.id].messages_to_show.get(key)
        for message in lst:
            to_delete = context.bot.send_message(chat_id=update.effective_chat.id,
                                                 text=format_msg(message), parse_mode='html')
            self.sessions[update.effective_chat.id].messages_to_delete.append(to_delete)

        keyboard = [
            [InlineKeyboardButton("Вернуться", callback_data=offset)],
            # was offset
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        message = to_delete.reply_text('Навигация:', reply_markup=reply_markup)
        self.sessions[update.effective_chat.id].messages_to_delete.append(message)

    #def return_cache(self, id):
    #    id = int(id)
    #    for msg in self.sessions[id].short_cache:
    #        to_delete = self.sessions[id].context.bot.send_message(chat_id=id,
    #                                                               text=msg, parse_mode='html')
    #        self.sessions[id].messages_to_delete.append(to_delete)
    #    reply_markup = self.create_navigation_keyboard(self.sessions[id].offset)
    #    message = to_delete.reply_text('Навигация:', reply_markup=reply_markup)
    #    self.sessions[id].messages_to_delete.append(message)
