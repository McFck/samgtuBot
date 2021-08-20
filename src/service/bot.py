from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters

import config
from src.service import university
import datetime
from bs4 import BeautifulSoup
from datetime import date
from src.dto import calendarTable
from formattingRoutine import format_msg, get_week_day, format_calendar, formatTasks
import time
import json


class TelegramBot:

    def __init__(self):
        self.super = {174740505}
        self.sessions = {}
        updater = Updater(token=config.token, use_context=True)
        dispatcher = updater.dispatcher

        stat_handler = CommandHandler('stat', self.statistics)
        dispatcher.add_handler(stat_handler)

        help_handler = CommandHandler('help', self.help)
        dispatcher.add_handler(help_handler)

        start_handler = CommandHandler('start', self.help)
        dispatcher.add_handler(start_handler)

        login_handler = CommandHandler('login', self.login)
        dispatcher.add_handler(login_handler)

        logout_handler = CommandHandler('logout', self.logout)
        dispatcher.add_handler(logout_handler)

        calendar_handler = CommandHandler('calendar', self.calendar)
        dispatcher.add_handler(calendar_handler)

        jump_to_handler = CommandHandler('to', self.jump_to)
        dispatcher.add_handler(jump_to_handler)

        dispatcher.add_handler(CallbackQueryHandler(self.calendar))
        while True:
            updater.start_polling()
            time.sleep(1800)
            self.session_loop(updater.bot)

    def session_loop(self, bot):
        for chat_id in self.sessions.keys():
            if self.is_Authorized(chat_id):
                data = self.request_year_data(chat_id)
                self.check_for_date_updates(data, bot, chat_id)

    def check_for_date_updates(self, data, bot, chat_id):
        for entry in data:
            is_new = False
            cur_date = datetime.datetime.strptime(entry['start'], '%Y-%m-%dT%H:%M:%S').date()
            message = '<b>🔥 Есть обновления на дате: ' + cur_date.strftime(
                "%d.%m.%Y") + ' ' + get_week_day(cur_date.weekday()) + '</b>' + '\n' + '✏ Дисциплина: ' + entry[
                          'title'] + '\n'
            if entry['IsNew'] == '1':
                message += '📬 Новые сообщения' + '\n'
                is_new = True
            if entry['NewResult'] != '0':
                message += '📝 Новый результат? (В процессе разработки, сообщите об этом тексте сюда: contact@babunov.dev)' + '\n'
                is_new = True
            if is_new:
                offset = (cur_date - date.today()).days
                keyboard = [
                    [
                        InlineKeyboardButton("Перейти к дате 👀", callback_data=str(offset)),
                    ],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                bot.send_message(chat_id=chat_id,
                                 text=message,
                                 parse_mode='html', reply_markup=reply_markup)

    def request_year_data(self, chat_id):
        summer = date(date.today().year, 9, 22)
        monitor_start = date(date.today().year, 1, 1) if date.today() < summer else summer
        monitor_end = date(date.today().year, 12, 31)
        return self.sessions[chat_id].get_calendar_data(monitor_start.strftime("%Y-%m-%d"),
                                                        monitor_end.strftime("%Y-%m-%d"))

    def write_json(self, new_data, filename='stats.json'):
        with open(filename, 'r+') as file:
            file_data = json.load(file)
            for entry in file_data["user_stats"]:
                if new_data["ID"] == entry["ID"]:
                    return
            file_data["user_stats"].append(new_data)
            file.seek(0)
            json.dump(file_data, file, indent=4)

    def stat_count(self, filename='stats.json'):
        with open(filename, 'r+') as file:
            file_data = json.load(file)
            return len(file_data["user_stats"])

    def statistics(self, update, context):
        if update.effective_user['id'] not in self.super:
            return
        message = context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='<b>📈 Статистика:</b> \n'
                                                'Онлайн сейчас: ' + str(len(self.sessions)) + '\n'
                                                                                              'Всего пользователей: ' + str(
                                               self.stat_count()) + '\n',
                                           parse_mode='html')

    def help(self, update, context):
        if update.effective_chat.id not in self.sessions:
            service = university.University()
            self.sessions[update.effective_chat.id] = service

        self.clear_screen(update, context)
        self.sessions[update.effective_chat.id].messages_to_delete.append(update.message)
        message = context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="<b>Привет! Хочешь узнать как работает бот?</b>\n"
                                                "Доступные команды: \n"
                                                "1. <b>/login</b> [Логин] [Пароль] - Использется для авторизации в ЛК \n"
                                                "2. <b>/calendar</b> - Основное меню бота\n"
                                                "3. <b>/logout</b> - Завершить сессию и выйти из аккаунта\n"
                                                "4. <b>/to</b> [день].[месяц].[год] - Посмотреть дату\n"
                                                "5. <b>/help</b> - Помогите, я потерялся...(Ты уже здесь)\n"
                                                "<b>Что умеет бот?</b>\n"
                                                "Бот переодически проверяет расписание на наличие <i>новых "
                                                "сообщений</i> от преподавателей⚡️\n"
                                                "С помощью бота, на конкретную дату, ты можешь <i>прочитать "
                                                "сообщения и проверить оценки</i>👀\n"
                                                "По всем вопросам обращайся на почту: <i>contact@babunov.dev</i>",
                                           parse_mode='html')
        self.sessions[update.effective_chat.id].messages_to_delete.append(message)
        if update.effective_user['id'] in self.super:
            message = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text="<b>🛠Дополнительные команды бота🛠</b> \n"
                                                    "1. <b>/stat</b> - Узнать статистику бота \n",
                                               parse_mode='html')
            self.sessions[update.effective_chat.id].messages_to_delete.append(message)

    def jump_to(self, update, context):
        if update.effective_chat.id not in self.sessions:
            service = university.University()
            self.sessions[update.effective_chat.id] = service

        if not self.is_Authorized(update.effective_chat.id):
            message = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text='<b>🔑Ошибка!</b>\nВы не авторизованы для использования этой команды.',
                                               parse_mode='html')
            self.sessions[update.effective_chat.id].messages_to_delete.append(message)
            return

        if len(context.args) == 0:
            message = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text='<b>🖍Использование команды</b>\n'
                                                    'Пожалуйста, внимательно соблюдайте формат команды! /to [день].[месяц].[год]\n'
                                                    'Пример: /to 20.08.2021\n'
                                                    '<i>Месяц и год опциональны, по умолчанию используются параметры <b>относительно сегодняшней даты</b>.</i>',
                                               parse_mode='html')
            self.sessions[update.effective_chat.id].messages_to_delete.append(message)
            return
        args = context.args[0].split('.')
        next_day = date.today()
        month = date.today().month
        year = date.today().year
        try:
            if len(args) == 1:
                next_day = datetime.datetime.strptime('{d}.{m}.{y}'.format(d=int(args[0]), m=month, y=year),
                                                      '%d.%m.%Y').date()
            if len(args) == 2:
                next_day = datetime.datetime.strptime('{d}.{m}.{y}'.format(d=int(args[0]), m=int(args[1]), y=year),
                                                      '%d.%m.%Y').date()
            if len(args) == 3:
                next_day = datetime.datetime.strptime(
                    '{d}.{m}.{y}'.format(d=int(args[0]), m=int(args[1]), y=int(args[2])),
                    '%d.%m.%Y').date()
        except Exception as e:
            message = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text='<b>Ошибка!</b>\nНеправильный формат даты.',
                                               parse_mode='html')
            self.sessions[update.effective_chat.id].messages_to_delete.append(message)
            return
        self.calendar(update, context, (next_day - date.today()).days)

    def is_Authorized(self, id):
        today = date.today()
        loginCheck = self.sessions[id].get_calendar_data(today.strftime("%Y-%m-%d"),
                                                         today.strftime("%Y-%m-%d"))
        return loginCheck is not None

    def logout(self, update, context):
        if update.effective_chat.id in self.sessions and self.is_Authorized(update.effective_chat.id):
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='🔒<b>Сессия завершена</b>\nХорошего дня.', parse_mode='html')
            self.sessions.pop(update.effective_chat.id)
            return
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='<b>🔑Ошибка!</b>\nВы не авторизованы для использования этой команды.',
                                 parse_mode='html')

    def login(self, update, context):
        if update.effective_chat.id not in self.sessions:
            service = university.University()
            self.sessions[update.effective_chat.id] = service

        self.clear_screen(update, context)
        context.bot.delete_message(chat_id=update.effective_chat.id,
                                   message_id=update.message['message_id'])
        if len(context.args) != 2:
            message = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text='<b>🖍Использование команды</b>\n'
                                                    'Пример: /login [Логин] [Пароль]', parse_mode='html')
            self.sessions[update.effective_chat.id].messages_to_delete.append(message)
            return

        if self.is_Authorized(update.effective_chat.id):
            message = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text='Вы уже авторизованы! 🔓')
            self.sessions[update.effective_chat.id].messages_to_delete.append(message)
            return

        if self.sessions[update.effective_chat.id].login(context.args[0], context.args[1]):
            user = update.message.from_user
            new_user = {
                "Telegram": "@" + user['username'],
                "ID": user['id']
            }
            self.write_json(new_user)
            message = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text='Авторизация успешна! 🔓 \n'
                                                    'Теперь вы можете использовать команду /calendar')
        else:
            message = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text='Ошибка авторизации 🔒 \n'
                                                    'Проверьте логин и пароль.')
        self.sessions[update.effective_chat.id].messages_to_delete.append(message)

    def clear_screen(self, update, context):
        if len(self.sessions) == 0:
            return
        for message in self.sessions[update.effective_chat.id].messages_to_delete:
            try:
                context.bot.delete_message(chat_id=update.effective_chat.id,
                                           message_id=message['message_id'])
            except Exception as e:
                print("too old")
        self.sessions[update.effective_chat.id].messages_to_delete = []

    def calendar(self, update, context, week_day=0):
        if update.effective_chat.id not in self.sessions:
            service = university.University()
            self.sessions[update.effective_chat.id] = service

        self.clear_screen(update, context)
        if update.message is not None:
            self.sessions[update.effective_chat.id].messages_to_delete.append(update.message)

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
        response = self.sessions[update.effective_chat.id].get_calendar_data(check_day.strftime("%Y-%m-%d"),
                                                                             next_day.strftime("%Y-%m-%d"))
        if response is None:
            message = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text='Нужно авторизоваться! 🔑🔑🔑, используйте команду \n'
                                                    '/login [Логин] [Пароль]')
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
            html_to_parse = self.sessions[update.effective_chat.id].get_page_to_parse(item['url'])
            table = self.parse_table(html_to_parse)
            taskId = self.get_task_id(html_to_parse)
            msgs_ids = self.get_msg_id(html_to_parse)
            messages = self.sessions[update.effective_chat.id].get_messages_to_parse(msgs_ids, False)
            table.msg_ids = ' '.join(msgs_ids)
            self.sessions[update.effective_chat.id].messages_to_show[' '.join(msgs_ids)] = messages
            if taskId is not None:
                tasksToFormat = self.sessions[update.effective_chat.id].get_tasks_to_parse(taskId)
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
        self.sessions[update.effective_chat.id].get_messages_to_parse(ids, True)
        self.sessions[update.effective_chat.id].messages_to_delete.append(message)

    # def return_cache(self, id):
    #    id = int(id)
    #    for msg in self.sessions[id].short_cache:
    #        to_delete = self.sessions[id].context.bot.send_message(chat_id=id,
    #                                                               text=msg, parse_mode='html')
    #        self.sessions[id].messages_to_delete.append(to_delete)
    #    reply_markup = self.create_navigation_keyboard(self.sessions[id].offset)
    #    message = to_delete.reply_text('Навигация:', reply_markup=reply_markup)
    #    self.sessions[id].messages_to_delete.append(message)
