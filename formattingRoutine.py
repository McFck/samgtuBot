def get_mark(mark):
    if mark == '10':
        return '✅'
    if mark == '0':
        return '❌'
    if mark == '1':
        return '1️⃣'
    if mark == '2':
        return '2️⃣'
    if mark == '3':
        return '3️⃣'
    if mark == '4':
        return '4️⃣'
    if mark == '5':
        return '5️⃣'
    return '🔍'


def check_for_unread_msgs(msgs):
    for msg in msgs:
        if '1' in msg['IsNew']:
            return True
    return False


def decl(number):
    titles = ['сообщение', 'сообщения',
              'сообщений']
    cases = [2, 0, 1, 1, 1, 2]
    if 4 < number % 100 < 20:
        idx = 2
    elif number % 10 < 5:
        idx = cases[number % 10]
    else:
        idx = cases[5]

    return titles[idx]


def format_msg(message):
    result = '<b>{sender}</b>:\n{text}\n<i>{time}</i>'.format(sender=message['Fio'], text=message['Text'],
                                                              time=message['Date'])
    return result


def get_week_day(day):
    if day == 0:
        return 'Понедельник'
    if day == 1:
        return 'Вторник'
    if day == 2:
        return 'Среда'
    if day == 3:
        return 'Четверг'
    if day == 4:
        return 'Пятница'
    if day == 5:
        return 'Суббота'
    if day == 6:
        return 'Воскресенье'
    return '???'


def get_week_day_short(day):
    if day == 0:
        return 'Понед.'
    if day == 1:
        return 'Вторник'
    if day == 2:
        return 'Среда'
    if day == 3:
        return 'Четверг'
    if day == 4:
        return 'Пятн.'
    if day == 5:
        return 'Суббота'
    if day == 6:
        return 'Вск'
    return '???'


ordered_attr = ['subject', 'type', 'time', 'teacher',  'place']


def get_string_by_attr(attr):
    if attr == 'teacher':
        return '🧑‍🏫 <b>Преподаватель:</b> '
    if attr == 'subject':
        return '✏ <b>Дисциплина:</b> '
    if attr == 'type':
        return '📖 <b>Вид занятия:</b> '
    if attr == 'time':
        return '⏳ <b>Время проведения занятия:</b> '
    if attr == 'place':
        return '📍 <b>Место проведения занятия:</b> '


def format_calendar(self, update, calendar, msgs=[], is_new='0'):
    result = ''
    for attr in ordered_attr:
        title = get_string_by_attr(str(attr))
        if title and getattr(calendar, attr):
            result += title + str(getattr(calendar, attr) or "Отсутствует") + '\n'

    if len(calendar.tasks) > 0:
        result += '📝 Результаты: '

    for task in calendar.tasks:
        result += task + ' '

    result += '\n'
    if calendar.newTask:
        result += '📣 <b>Есть невыполненное задание!</b>' + '\n'

    if msgs is None:
        messagesCounter = 0
    else:
        messagesCounter = len(msgs)

    if messagesCounter > 0:
        if is_new == '1':
            result += '📬 <b>Есть новые сообщения!</b>' + '\n'
        elif check_for_unread_msgs(msgs):
            result += '🗳 <b>Ваши сообщения не прочитаны преподавателем!</b>' + '\n'
        result += '✉ В чате {counter} {msg} \n'.format(counter=messagesCounter, msg=decl(messagesCounter))
    return result


def formatTasks(tasks, calendar):
    if len(tasks) == 0:
        calendar.newTask = True
        return calendar
    for task in tasks:
        calendar.tasks.append(get_mark(task['Result']))
    return calendar
