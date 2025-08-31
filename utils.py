from calendar import monthrange
from datetime import date, datetime
from json import loads
from random import choice, randint
from secrets import token_urlsafe
from time import gmtime, strftime

from hammett.core.exceptions import PayloadIsEmpty

from constants import GREET_DAY, GREET_EVENING, GREET_MORNING, GREET_NIGHT, WEEK_DAYS


def get_week_day(task_year, task_month_int: int, task_day: int):
    week_day = date(int(task_year), task_month_int, task_day)
    week_day_new = WEEK_DAYS[week_day.weekday()]
    return str(week_day_new)


def get_greet(name):
    greet = '<strong>'
    if datetime.now().hour < 4:
        greet += choice(['🌕', '🌙'])
        greet += 'Доброй ночи, '
        attach = GREET_NIGHT[randint(0, 2)]
    elif 4 <= datetime.now().hour < 12:
        greet += choice(['🌅', '🌄'])
        greet += 'Доброе утро, '
        attach = GREET_MORNING[randint(0, 2)]
    elif 12 <= datetime.now().hour < 17:
        greet += choice(['🌞', '☀️'])
        greet += 'Добрый день, '
        attach = GREET_DAY[randint(0, 2)]
    elif 17 <= datetime.now().hour < 23:
        greet += choice(['🌅', '🌄'])
        greet += 'Добрый вечер, '
        attach = GREET_EVENING[randint(0, 2)]
    else:
        greet += choice(['🌕', '🌙'])
        greet += 'Доброй ночи, '
        attach = GREET_NIGHT[randint(0, 2)]
    greet += name + '!👋' + attach + '</strong>'
    return greet


def get_clean_var(var, new_var_type: str, index: int, need_clear: bool):
    var = str(var[index])
    if new_var_type == 'to_string':
        if need_clear:
            if var[0] == '(':
                var = var[1: -1]
            if var[-1] == ',':
                var = var[0: -1]
            if var[0] == "'":
                var = var[1: -1]
        return str(var)
    elif new_var_type == 'to_int':
        if var[0] == '(':
            var = var[1: -1]
        if var[-1] == ',':
            var = var[0: -1]
        return int(var)


def recognise_month(month):
    month_dict = {'1': 'января',
                  '2': 'февраля',
                  '3': 'марта',
                  '4': 'апреля',
                  '5': 'мая',
                  '6': 'июня',
                  '7': 'июля',
                  '8': 'августа',
                  '9': 'сентября',
                  '10': 'октября',
                  '11': 'ноября',
                  '12': 'декабря',
                  }
    month = month_dict[str(month)]
    return month


def recognise_n_tag(text: str):
    if r'\n' in text:
        text = text.replace(r'\n', '\n')
    return text


def check_task_validity(day, month, year):
    if int(year) > int(datetime.now().year):
        return True
    elif int(year) == int(datetime.now().year):
        if int(month) > int(datetime.now().month):
            return True
        elif int(month) == int(datetime.now().month):
            if int(day) > int(datetime.now().day):
                return True
            else:
                return False
        else:
            return False
    else:
        return False


def update_day(check_month, task_day):
    if task_day <= int(monthrange(int(strftime('%Y', gmtime())), int(check_month))[1]):
        return task_day
    return False


def get_user_month(month):
    months_dict = {
        1: ['Январь', 'Января', 'январь', 'января'],
        2: ['Февраль', 'Февраля', 'февраль', 'февраля'],
        3: ['Март', 'Марта', 'март', 'марта'],
        4: ['Апрель', 'Апреля', 'апрель', 'апреля'],
        5: ['Май', 'Мая', 'май', 'мая'],
        6: ['Июнь', 'Июня', 'июнь', 'июня'],
        7: ['Июль', 'Июля', 'июль', 'июля'],
        8: ['Август', 'Августа', 'август', 'августа'],
        9: ['Сентябрь', 'Сентября', 'сентябрь', 'сентября'],
        10: ['Октябрь', 'Октября', 'октябрь', 'октября'],
        11: ['Ноябрь', 'Ноября', 'ноябрь', 'ноября'],
        12: ['Декабрь', 'Декабря', 'декабрь', 'декабря'],
    }
    for i in months_dict:
        month_list = months_dict[i]
        for a in month_list:
            if a == month:
                return i


def update_month(check_day, task_month):
    check_month = get_user_month(task_month)
    if check_day <= int(monthrange(int(strftime('%Y', gmtime())), check_month)[1]):
        return check_month
    return False


def get_hypertime(month: int, day: int, year: int):
    if int(month) < 10:
        hypertime = str(year) + '0' + str(month)
    else:
        hypertime = str(year) + str(month)
    if day < 10:
        hypertime += '0'
    hypertime += str(day)
    return str(hypertime)


async def get_payload_safe(self, update, context, key_id: str, value: str):
    try:
        payload = loads(await self.get_payload(update, context))
    except PayloadIsEmpty:
        payload = context.user_data.get(key_id)
    else:
        context.user_data[key_id] = payload
    context.user_data[value] = payload[value]


def find_informative_username(username):
    username = username.strip()
    if not username or len(set(username)) == 1 or all(c in ' .-_/*!@#$%^:&()+=`~' for c in username):
        return False

    return True


def get_username(first_name, last_name, username):
    data = [first_name, last_name, username]
    for check in data:
        if check and find_informative_username(check):
            return check.strip()
    return 'Дорогой пользователь School Tasker'


def generate_id():
    return token_urlsafe(randint(5, 25))


def save_html_markers(caption):
    return caption.replace('\n', '<!-- NEWLINE -->')


def load_html_markers(caption):
    return caption.replace('<!-- NEWLINE -->', '\n')
