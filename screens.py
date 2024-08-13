import contextlib
import json
import logging
import telegram.error
from hammett.core import Button, Screen
from hammett.core.constants import RenderConfig, SourcesTypes
from hammett.core.handlers import register_button_handler, register_typing_handler
from hammett.core.hiders import ONLY_FOR_ADMIN, Hider
from hammett.core.mixins import StartMixin
import settings
import sqlite3
from constants import *
from datetime import datetime
import calendar
from time import gmtime, strftime
from random import randint

connection = sqlite3.connect('school_tasker_database.db')
cursor = connection.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS SchoolTasker (
item_name TEXT,
item_index INTEGER,
group_number INTEGER,
task_description TEXT,
task_day INT,
task_month INT,
hypertime INT
)
''')
users_connection = sqlite3.connect('users_database.db')
users_cursor = users_connection.cursor()
users_cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
user_permission TEXT,
user_id INT PRIMARY KEY,
user_name TEXT
)
''')
LOGGER = logging.getLogger('hammett')


class Global:
    last_day = int()
    last_month = int()
    index_store = int(0)
    open_date = True
    is_changing_task_description = False
    is_changing_day = False
    is_changing_month = False
    is_changing_group_number = False


def update_day(check_month, task_day):
    if task_day <= int(calendar.monthrange(int(strftime("%Y", gmtime())), int(check_month))[1]):
        return task_day
    else:
        return False


def logger_alert(user: list, status: str, formattered_index):
    global cursor
    cursor.execute("SELECT task_day FROM SchoolTasker ORDER BY hypertime ASC")
    task_day = cursor.fetchall()
    print(formattered_index)
    task_day = str(task_day[formattered_index])
    for symbol in REMOVE_SYMBOLS_ITEM:
        task_day = task_day.replace(symbol, "")
    cursor.execute("SELECT task_month FROM SchoolTasker ORDER BY hypertime ASC")
    task_month = cursor.fetchall()
    task_month = str(task_month[formattered_index])
    for symbol in REMOVE_SYMBOLS_ITEM:
        task_month = task_month.replace(symbol, "")
    cursor.execute("SELECT item_name FROM SchoolTasker ORDER BY hypertime ASC")
    item_name = cursor.fetchall()
    item_name = str(item_name[formattered_index])
    for symbol in REMOVE_SYMBOLS_ITEM:
        item_name = item_name.replace(symbol, "")
    cursor.execute("SELECT group_number FROM SchoolTasker ORDER BY hypertime ASC")
    group_number = cursor.fetchall()
    group_number = str(group_number[formattered_index])
    for symbol in REMOVE_SYMBOLS_ITEM:
        group_number = group_number.replace(symbol, "")
    cursor.execute("SELECT task_description FROM SchoolTasker ORDER BY hypertime ASC")
    task_description = cursor.fetchall()
    task_description = str(task_description[formattered_index])
    for symbol in REMOVE_SYMBOLS_ITEM:
        task_description = task_description.replace(symbol, "")
    title = "The "
    if len(user) < 2:
        title += "SchoolTasker has "
        if status == "add":
            title += "added task"
        if status == "delete":
            title += "deleted task"
        if status == "change":
            title += "changed task"
        title += ": На " + str(task_day) + "." + str(task_month) + " по " + item_name
        if item_name == "Английский язык" or item_name == "Информатика":
            title += "(" + str(group_number) + "ая группа)"
        title += ": " + str(task_description)
        LOGGER.info(title)
    else:
        title += "user " + str(user[0]) + " (" + str(user[1]) + ")" + " has "
        if status == "add":
            title += "added task"
        if status == "delete":
            title += "deleted task"
        if status == "change":
            title += "changed task"
        title += ": На " + str(task_day) + "." + str(task_month) + " по " + item_name
        if item_name == "Английский язык" or item_name == "Информатика":
            title += "(" + str(group_number) + "ая группа)"
        title += ": " + str(task_description)
        LOGGER.info(title)


def update_month(check_day, task_month):
    months_dict = {
        1: ["Январь", "Января", "январь", "января"],
        2: ["Февраль", "Февраля", "февраль", "февраля"],
        3: ["Март", "Марта", "март", "марта"],
        4: ["Апрель", "Апреля", "апрель", "апреля"],
        5: ["Май", "Мая", "май", "мая"],
        6: ["Июнь", "Июня", "июнь", "июня"],
        7: ["Июль", "Июля", "июль", "июля"],
        8: ["Август", "Августа", "август", "августа"],
        9: ["Сентябрь", "Сентября", "сентябрь", "сентября"],
        10: ["Октябрь", "Октября", "октябрь", "октября"],
        11: ["Ноябрь", "Ноября", "ноябрь", "ноября"],
        12: ["Декабрь", "Декабря", "декабрь", "декабря"],
    }
    for i in months_dict:
        month_list = months_dict[i]
        for a in month_list:
            if a == task_month:
                check_month = i
                if check_day <= int(calendar.monthrange(int(strftime("%Y", gmtime())), check_month)[1]):
                    return check_month
                else:
                    return False
            else:
                pass


def get_var_from_database(index, need_variable):
    global cursor
    if need_variable == "item_name":
        cursor.execute("SELECT item_name FROM SchoolTasker ORDER BY hypertime ASC")
        variable = cursor.fetchall()
        variable = str(variable[index])
        for symbol in REMOVE_SYMBOLS_ITEM:
            variable = variable.replace(symbol, "")
        return variable
    if need_variable == "group_number":
        cursor.execute("SELECT group_number FROM SchoolTasker ORDER BY hypertime ASC")
        variable = cursor.fetchall()
        variable = str(variable[index])
        for symbol in REMOVE_SYMBOLS_ITEM:
            variable = variable.replace(symbol, "")
        return variable
    if need_variable == "task_description":
        cursor.execute("SELECT task_description FROM SchoolTasker ORDER BY hypertime ASC")
        variable = cursor.fetchall()
        variable = str(variable[index])
        for symbol in REMOVE_SYMBOLS_ITEM:
            variable = variable.replace(symbol, "")
        if need_variable == "task_day":
            cursor.execute("SELECT task_day FROM SchoolTasker ORDER BY hypertime ASC")
            variable = cursor.fetchall()
            variable = str(variable[index])
            for symbol in REMOVE_SYMBOLS_ITEM:
                variable = variable.replace(symbol, "")
        if need_variable == "task_month":
            cursor.execute("SELECT task_month FROM SchoolTasker ORDER BY hypertime ASC")
            variable = cursor.fetchall()
            variable = str(variable[index])
            for symbol in REMOVE_SYMBOLS_ITEM:
                variable = variable.replace(symbol, "")
        return variable


def get_button_title(index):
    item_name = get_var_from_database(index, "item_name")
    if item_name == "Английский язык" or item_name == "Информатика":
        group_number = get_var_from_database(index, "group_number")
        item_name += " (" + group_number + "ая группа) "
    task_description = get_var_from_database(index, "task_description")
    title = item_name
    title += " : "
    title += task_description
    return title


def update_task_index(index, index_new):
    global cursor
    cursor.execute('UPDATE SchoolTasker set item_index = ? WHERE item_index = ?',
                   (index_new, index))
    connection.commit()


def get_multipy_async(index, title, return_value):
    cursor.execute("select count(*) from SchoolTasker")
    out_of_data = False
    Global.index_store = cursor.fetchone()
    database_length = Global.index_store
    Global.index_store = str(Global.index_store)
    database_length = str(database_length)
    for symbol in REMOVE_SYMBOLS_INDEX:
        Global.index_store = Global.index_store.replace(symbol, "")
        database_length = database_length.replace(symbol, "")
    Global.index_store = int(Global.index_store)
    cursor.execute('SELECT task_day FROM SchoolTasker ORDER BY hypertime ASC')
    task_day = cursor.fetchall()
    task_day = list(task_day)
    task_day = str(task_day[index])
    for symbol in REMOVE_SYMBOLS_ITEM:
        task_day = task_day.replace(symbol, "")
    check_day = int(task_day)
    cursor.execute('SELECT task_month FROM SchoolTasker ORDER BY hypertime ASC')
    task_month = cursor.fetchall()
    task_month = str(task_month[index])
    for symbol in REMOVE_SYMBOLS_ITEM:
        task_month = task_month.replace(symbol, "")
    check_month = int(task_month)
    if not out_of_data:
        task_month = str(task_month)
        if task_month == "1":
            task_month = "января"
        if task_month == "2":
            task_month = "февраля"
        if task_month == "3":
            task_month = "марта"
        if task_month == "4":
            task_month = "апреля"
        if task_month == "5":
            task_month = "мая"
        if task_month == "6":
            task_month = "июня"
        if task_month == "7":
            task_month = "июля"
        if task_month == "8":
            task_month = "августа"
        if task_month == "9":
            task_month = "сентября"
        if task_month == "10":
            task_month = "октября"
        if task_month == "11":
            task_month = "ноября"
        if task_month == "12":
            task_month = "декабря"
        if Global.last_day == task_day and Global.last_month == task_month:
            if Global.open_date:
                task_time = "<strong>На " + str(task_day) + " " + str(task_month) + " :</strong>" + "\n"
            else:
                task_time = ""
        else:
            task_time = "<strong>На " + str(task_day) + " " + str(task_month) + " :</strong>" + "\n"
        Global.last_day = task_day
        Global.last_month = task_month
        cursor.execute('SELECT item_name FROM SchoolTasker ORDER BY hypertime ASC')
        item_name = cursor.fetchall()
        item_name = "<strong>" + str(item_name[index])
        for symbol in REMOVE_SYMBOLS_ITEM:
            item_name = item_name.replace(symbol, "")
        if item_name == "<strong>Английский язык" or item_name == "<strong>Информатика":
            item_name += " ("
            cursor.execute('SELECT group_number FROM SchoolTasker ORDER BY hypertime ASC')
            group_number = cursor.fetchall()
            group_number = str(group_number[index])
            for symbol in REMOVE_SYMBOLS_ITEM:
                group_number = group_number.replace(symbol, "")
            item_name += group_number
            item_name += "ая группа)"
        else:
            pass
        item_name += " : </strong>"
        cursor.execute('SELECT task_description FROM SchoolTasker ORDER BY hypertime ASC')
        task_description = cursor.fetchall()
        task_description = "<strong>" + str(task_description[index])
        for symbol in REMOVE_SYMBOLS_ITEM:
            task_description = task_description.replace(symbol, "")
        task_description += "</strong>\n"
        title += task_time + item_name + task_description
        if return_value == 0:
            return title
        elif return_value == 1:
            return check_day
        else:
            return check_month
    else:
        title += ""
        if return_value == 0:
            return title
        elif return_value == 1:
            return check_day
        else:
            return check_month


async def check_tasks(update, context):
    global cursor
    out_of_data = False
    cursor.execute("select count(*) from SchoolTasker")
    Global.index_store = cursor.fetchone()
    database_length = Global.index_store
    Global.index_store = str(Global.index_store)
    database_length = str(database_length)
    title = str()
    for symbol in REMOVE_SYMBOLS_INDEX:
        Global.index_store = Global.index_store.replace(symbol, "")
        database_length = database_length.replace(symbol, "")
    database_length = int(database_length)
    Global.index_store = int(Global.index_store)
    if database_length == 0:
        SchoolTasks.description = "<strong>На данный момент список заданий пуст!</strong>"
    if database_length == 1:
        cursor.execute("select count(*) from SchoolTasker")
        Global.index_store = cursor.fetchone()
        database_length = Global.index_store
        Global.index_store = str(Global.index_store)
        database_length = str(database_length)
        for symbol in REMOVE_SYMBOLS_INDEX:
            Global.index_store = Global.index_store.replace(symbol, "")
            database_length = database_length.replace(symbol, "")
        Global.index_store = int(Global.index_store)
        cursor.execute('SELECT task_day FROM SchoolTasker')
        task_day = cursor.fetchall()[0]
        task_day = str(task_day)
        for symbol in REMOVE_SYMBOLS_ITEM:
            task_day = task_day.replace(symbol, "")
        cursor.execute('SELECT task_month FROM SchoolTasker')
        task_month = cursor.fetchall()[0]
        task_month = str(task_month)
        for symbol in REMOVE_SYMBOLS_ITEM:
            task_month = task_month.replace(symbol, "")
        check_month = task_month
        check_day = task_day
        # if int(check_month) <= datetime.now().month and int(check_day) <= datetime.now().day:
        if int(check_month) == datetime.now().month:
            if int(check_day) <= datetime.now().day:
                cursor.execute("DELETE FROM SchoolTasker WHERE item_index = ?", (0,))
                connection.commit()
                SchoolTasks.description = "<strong>На данный момент список заданий пуст!</strong>"
                out_of_data = True
        if int(check_month) < datetime.now().month:
            cursor.execute("DELETE FROM SchoolTasker WHERE item_index = ?", (0,))
            connection.commit()
            SchoolTasks.description = "<strong>На данный момент список заданий пуст!</strong>"
            out_of_data = True
        if not out_of_data:
            task_day = str(task_day)
            task_month = str(task_month)
            if task_month == "1":
                task_month = "января"
            if task_month == "2":
                task_month = "февраля"
            if task_month == "3":
                task_month = "марта"
            if task_month == "4":
                task_month = "апреля"
            if task_month == "5":
                task_month = "мая"
            if task_month == "6":
                task_month = "июня"
            if task_month == "7":
                task_month = "июля"
            if task_month == "8":
                task_month = "августа"
            if task_month == "9":
                task_month = "сентября"
            if task_month == "10":
                task_month = "октября"
            if task_month == "11":
                task_month = "ноября"
            if task_month == "12":
                task_month = "декабря"
            task_time = "<strong>На " + str(task_day) + " " + str(task_month) + " :</strong>" + "\n"
            Global.last_day = task_day
            Global.last_month = task_month
            cursor.execute('SELECT item_name FROM SchoolTasker')
            item_name = cursor.fetchall()[0]
            item_name = "<strong>" + str(item_name)
            for symbol in REMOVE_SYMBOLS_ITEM:
                item_name = item_name.replace(symbol, "")
            if item_name == "<strong>Английский язык" or item_name == "<strong>Информатика":
                item_name += " ("
                cursor.execute('SELECT group_number FROM SchoolTasker')
                group_number = cursor.fetchall()[0]
                group_number = str(group_number)
                for symbol in REMOVE_SYMBOLS_ITEM:
                    group_number = group_number.replace(symbol, "")
                item_name += group_number
                item_name += "ая группа)"
            else:
                pass
            item_name += " : </strong>"
            cursor.execute('SELECT task_description FROM SchoolTasker')
            task_description = cursor.fetchall()[0]
            task_description = "<strong>" + str(task_description)
            for symbol in REMOVE_SYMBOLS_ITEM:
                task_description = task_description.replace(symbol, "")
            task_description += "</strong>\n"
            title += task_time + item_name + task_description
            SchoolTasks.description = title
            # return SchoolTasks().goto(update, context)
        else:
            SchoolTasks.description = "<strong>На данный момент список заданий пуст!</strong>"
    elif database_length > 1:
        Global.open_date = True
        new_title = str()
        for i in range(database_length):
            got_error = False
            check_day = int()
            check_month = int()
            try:
                title, check_day, check_month = (get_multipy_async(i, title, 0),
                                                 get_multipy_async(i, title, 1),
                                                 get_multipy_async(i, title, 2))
            except IndexError:
                await check_tasks(update, context)
            # if check_month <= datetime.now().month or check_day <= datetime.now().day:
            if check_month == datetime.now().month:
                if check_day <= datetime.now().day:
                    title = ""
                    cursor.execute("SELECT item_index FROM SchoolTasker WHERE task_month < ?", (datetime.now().month,))
                    formatted_index = cursor.fetchall()
                    cursor.execute("SELECT count(*) FROM SchoolTasker WHERE task_month < ?", (datetime.now().month,))
                    n = cursor.fetchall()
                    n = str(n)
                    for symbol in REMOVE_SYMBOLS_ITEM:
                        n = n.replace(symbol, "")
                    n = int(n)
                    try:
                        formatted_index = str(formatted_index[n - 1])
                    except IndexError:
                        got_error = True
                    if not got_error:
                        for symbol in REMOVE_SYMBOLS_ITEM:
                            formatted_index = formatted_index.replace(symbol, "")
                        formatted_index = int(formatted_index)
                        cursor.execute("DELETE FROM SchoolTasker WHERE item_index = ?", (formatted_index,))
                        connection.commit()
                        await check_tasks(update, context)
                    else:
                        pass
            if check_month < datetime.now().month:
                title = ""
                cursor.execute("SELECT item_index FROM SchoolTasker WHERE task_month < ?", (datetime.now().month,))
                formatted_index = cursor.fetchall()
                cursor.execute("SELECT count(*) FROM SchoolTasker WHERE task_month < ?", (datetime.now().month,))
                n = cursor.fetchall()
                n = str(n)
                for symbol in REMOVE_SYMBOLS_ITEM:
                    n = n.replace(symbol, "")
                n = int(n)
                try:
                    formatted_index = str(formatted_index[n - 1])
                except IndexError:
                    got_error = True
                if not got_error:
                    for symbol in REMOVE_SYMBOLS_ITEM:
                        formatted_index = formatted_index.replace(symbol, "")
                    formatted_index = int(formatted_index)
                    cursor.execute("DELETE FROM SchoolTasker WHERE item_index = ?", (formatted_index,))
                    connection.commit()
                    await check_tasks(update, context)
                else:
                    pass
            else:
                new_title = title
                Global.open_date = False
            if not new_title:
                SchoolTasks.description = "<strong>На данный момент список заданий пуст!</strong>"
            else:
                SchoolTasks.description = new_title
        if database_length < 1:
            SchoolTasks.description = "<strong>На данный момент список заданий пуст!</strong>"
        # return await SchoolTasks().jump(update, context)


def get_notification_title(task_item, task_description, group_number, task_day, task_month):
    is_group_item = False
    title = "На " + str(task_day)
    add_month_txt = " " + str(task_month)
    title += str(add_month_txt)
    title += " было добавлено задание по "
    add_task_txt = str()
    if task_item == "Алгебра":
        add_task_txt = "Алгебре"
    if task_item == "Алгебра":
        add_task_txt = "Алгебре"
    if task_item == "Английский язык":
        add_task_txt = "Английскому языку"
        is_group_item = True
    if task_item == "Биология":
        add_task_txt = "Биологии"
    if task_item == "География":
        add_task_txt = "Географии"
    if task_item == "Геометрия":
        add_task_txt = "Геометрии"
    if task_item == "Информатика":
        add_task_txt = "Информатике"
        is_group_item = True
    if task_item == "История":
        add_task_txt = "Истории"
    if task_item == "Литература":
        add_task_txt = "Литературе"
    if task_item == "Музыка":
        add_task_txt = "Музыке"
    if task_item == "Обществознание":
        add_task_txt = "Обществознанию"
    if task_item == "ОБЖ":
        add_task_txt = "ОБЖ"
    if task_item == "Решение задач повышенного уровня по алгебре":
        add_task_txt = "Решению задач повышенного уровня по алгебре"
    if task_item == "Русский язык":
        add_task_txt = "Русскому языку"
    if task_item == "Технология":
        add_task_txt = "Технологии"
    if task_item == "Физика":
        add_task_txt = "Физике"
    if task_item == "Химия":
        add_task_txt = "Химии"
    title += add_task_txt
    if is_group_item:
        group_txt = " (" + str(group_number) + "ая " + "группа) "
        title += group_txt
    title += ": " + task_description
    return title


class Reference(Screen):
    description = ("В данной справке приведены ответы на все вопросы, которые могут возникнуть при работе с "
                   "ботом.")

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button("⬅Вернуться в главное меню", MainMenu, source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]


class NotificationScreen(Screen):
    description = "ERROR 451!"

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button("⬅В главное меню", MainMenu, source_type=SourcesTypes.JUMP_SOURCE_TYPE)
            ]
        ]


class NewsNotificationScreen(Screen):
    description = "_"


class MainMenu(StartMixin, Screen):
    admin_status = 'Администратор'
    anonymous_status = 'Обычный пользователь'
    text_map = {
        admin_status: (
        ),
        anonymous_status: (
        ),
    }

    #
    # Private methods
    #

    async def _get_user_status(self, user):
        if str(user.id) in settings.ADMIN_GROUP:
            # LOGGER.info('The user %s (%s) was added to the admin group.', user.username, user.id)
            return self.admin_status
        else:
            # LOGGER.info('%s (%s) joined', user.username, user.id)
            return self.anonymous_status

    #
    # Public methods
    #

    async def get_config(self, update, _context, **_kwargs):
        global users_cursor
        config = RenderConfig()
        config.description = ""
        return config

    async def add_default_keyboard(self, _update, _context):
        user = _update.effective_user
        if user.id == settings.DIRECTOR_ID:
            return [
                [
                    Button('Зайти в задачник📓', self.school_tasks,
                           source_type=SourcesTypes.HANDLER_SOURCE_TYPE),
                ],
                [
                    Button('Внести изменения в задачник🔧', ManageSchoolTasksMain,
                           hiders=Hider(ONLY_FOR_ADMIN),
                           source_type=SourcesTypes.GOTO_SOURCE_TYPE),
                ],
                # [
                #     Button('Внести изменения в список администраторов👥', ManageAdminUsersMain,
                #            source_type=SourcesTypes.GOTO_SOURCE_TYPE),
                # ],
                [
                    Button('Настройки⚙', Options,
                           source_type=SourcesTypes.GOTO_SOURCE_TYPE),
                ],
                # [
                #     Button('Справка для пользователей📄', Reference,
                #            source_type=SourcesTypes.GOTO_SOURCE_TYPE),
                # ],
                [
                    Button('Что нового сегодня?✨', WhatsNew,
                           source_type=SourcesTypes.GOTO_SOURCE_TYPE),
                ],
                [
                    Button('Связаться с разработчиком📞', 'https://t.me/TheDanskiSon09',
                           source_type=SourcesTypes.URL_SOURCE_TYPE),
                ],
                [
                    Button('Наш новостной журнал📰', 'https://t.me/SchoolTaskerNews',
                           source_type=SourcesTypes.URL_SOURCE_TYPE),
                ]
            ]
            # [
            # Button('🎸 Hammett Home Page', 'https://github.com/cusdeb-com/hammett',
            # source_type=SourcesTypes.URL_SOURCE_TYPE),
            # ],
        else:
            return [
                [
                    Button('Зайти в задачник📓', self.school_tasks,
                           source_type=SourcesTypes.HANDLER_SOURCE_TYPE),
                ],
                [
                    Button('Внести изменения в задачник🔧', ManageSchoolTasksMain,
                           hiders=Hider(ONLY_FOR_ADMIN),
                           source_type=SourcesTypes.GOTO_SOURCE_TYPE),
                ],
                # [
                #     Button('Внести изменения в список администраторов👥', ManageAdminUsersMain,
                #            source_type=SourcesTypes.GOTO_SOURCE_TYPE),
                # ],
                [
                    Button('Настройки⚙', Options,
                           source_type=SourcesTypes.GOTO_SOURCE_TYPE),
                ],
                # [
                #     Button('Справка для пользователей📄', Reference,
                #            source_type=SourcesTypes.GOTO_SOURCE_TYPE),
                # ],
                [
                    Button('Что нового сегодня?✨', WhatsNew,
                           source_type=SourcesTypes.GOTO_SOURCE_TYPE),
                ],
                [
                    Button('Связаться с разработчиком📞', 'https://t.me/TheDanskiSon09',
                           source_type=SourcesTypes.URL_SOURCE_TYPE),
                ],
                [
                    Button('Наш новостной журнал📰', 'https://t.me/SchoolTaskerNews',
                           source_type=SourcesTypes.URL_SOURCE_TYPE),
                ],
                # [
                # Button('🎸 Hammett Home Page', 'https://github.com/cusdeb-com/hammett',
                # source_type=SourcesTypes.URL_SOURCE_TYPE),
                # ],
            ]

    @register_button_handler
    async def school_tasks(self, update, context):
        await check_tasks(update, context)
        return await SchoolTasks().goto(update, context)

    async def start(self, update, context):
        """Replies to the /start command. """
        try:
            user = update.message.from_user
            # LOGGER.info('The user %s (%s) was added to the admin group.', user.username, user.id)
        except AttributeError:
            # When the start handler is invoked through editing
            # the message with the /start command.
            user = update.edited_message.from_user
        if str(user.id) in settings.ADMIN_GROUP:
            LOGGER.info('The user %s (%s) was added to the admin group.', user.username, user.id)
        else:
            LOGGER.info('The user %s (%s) was added to the anonim group.', user.username, user.id)
        try:
            users_cursor.execute(
                'INSERT INTO Users (user_permission, user_id, user_name) '
                'VALUES'
                '(?,?,?)',
                (1, user.id, update.message.chat.first_name))
            users_connection.commit()
            if str(user.id) in settings.ADMIN_GROUP:
                MainMenu.description = GREET_ADMIN_FIRST[randint(0, 2)]
            else:
                MainMenu.description = GREET_ANONIM_FIRST[randint(0, 2)]
        except sqlite3.IntegrityError:
            if str(user.id) in settings.ADMIN_GROUP:
                MainMenu.description = GREET_ADMIN_LATEST[randint(0, 2)]
            else:
                MainMenu.description = GREET_ANONIM_LATEST[randint(0, 2)]
        except AttributeError:
            if str(user.id) in settings.ADMIN_GROUP:
                MainMenu.description = GREET_ADMIN_LATEST[randint(0, 2)]
            else:
                MainMenu.description = GREET_ANONIM_LATEST[randint(0, 2)]
        return await super().start(update, context)


class ManageAdminUsersMain(Screen):
    description = "<strong>Какие изменения Вы хотите внести в список администраторов?</strong>"

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button("Добавить администратора➕", ManageAdminUsersAdd,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ],
            [
                Button("Убрать администратора➖", ManageAdminUsersRemove,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ],
            [
                Button("⬅Назад", MainMenu,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]

        ]


class ManageAdminUsersAdd(Screen):
    description = "<strong>Кого из данных пользователей Вы хотите назначить администратором?</strong>"

    async def add_default_keyboard(self, _update, _context):
        users_cursor.execute("SELECT count(*) FROM Users")
        database_length = users_cursor.fetchone()
        database_length = str(database_length)
        for symbol in REMOVE_SYMBOLS_ITEM:
            database_length = database_length.replace(symbol, "")
        database_length = int(database_length)
        keyboard = []
        for n in range(database_length):
            users_cursor.execute("SELECT user_id FROM Users")
            user_id = users_cursor.fetchall()
            user_id = str(user_id[n])
            for symbol in REMOVE_SYMBOLS_ITEM:
                user_id = user_id.replace(symbol, "")
            if str(user_id) not in settings.ADMIN_GROUP:
                users_cursor.execute("SELECT user_name FROM Users")
                user_name = users_cursor.fetchall()
                user_name = str(user_name[n])
                for symbol in REMOVE_SYMBOLS_ITEM:
                    user_name = user_name.replace(symbol, "")
                button_title = user_name + "(" + str(user_id) + ")"
                button = [
                    Button(button_title, self.got_to_confirm,
                           source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                           payload=json.dumps({"button_title": button_title, "user_id": user_id}))
                ]
                keyboard.append(button)
            else:
                pass
        button = [
            Button("⬅Назад", ManageAdminUsersMain,
                   source_type=SourcesTypes.GOTO_SOURCE_TYPE)
        ]
        keyboard.append(button)
        return keyboard

    @register_button_handler
    async def got_to_confirm(self, _update, _context):
        payload = json.loads(await self.get_payload(_update, _context))
        _context.user_data["button_title"], _context.user_data["user_id"] = (payload["button_title"],
                                                                             payload["user_id"])
        return await ManageAdminUsersAddConfirm().goto(_update, _context)


class ManageAdminUsersAddConfirm(Screen):

    async def get_description(self, _update, _context):
        title = ("<strong>Вы уверены, что хотите назначить данного пользователя " +
                 str(_context.user_data["button_title"] + " администратором?</strong>"))
        return title

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button("Да➕", self.confirm_add,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button("⬅Назад", ManageAdminUsersAdd,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def confirm_add(self, _update, _context):
        settings.ADMIN_GROUP.append(_context.user_data["user_id"])
        return await UserWasMarkedAsAdmin().goto(_update, _context)


class UserWasMarkedAsAdmin(Screen):
    description = "✅<strong>Пользователь был успешно добавлен в число администраторов!</strong>"

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button('⬅️ В меню редактора', ManageAdminUsersMain,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
            [
                Button('⬅️ Добавить ещё администратора', ManageAdminUsersAdd,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
            [
                Button('⬅️ В главное меню', MainMenu,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ],
        ]


class ManageAdminUsersRemove(Screen):
    description = "<strong>Кого из данных пользователей Вы хотите исключить из числа администраторов?</strong>"

    async def add_default_keyboard(self, _update, _context):
        user = _update.effective_user
        users_cursor.execute("SELECT count(*) FROM Users ")
        database_length = users_cursor.fetchone()
        database_length = str(database_length)
        for symbol in REMOVE_SYMBOLS_ITEM:
            database_length = database_length.replace(symbol, "")
        database_length = int(database_length)
        keyboard = []
        for n in range(database_length):
            users_cursor.execute("SELECT user_id FROM Users")
            user_id = users_cursor.fetchall()
            user_id = str(user_id[n])
            for symbol in REMOVE_SYMBOLS_ITEM:
                user_id = user_id.replace(symbol, "")
            if (str(user_id) in settings.ADMIN_GROUP and user_id != user.id
                    and user_id != settings.DIRECTOR_ID):
                users_cursor.execute("SELECT user_name FROM Users")
                user_name = users_cursor.fetchall()
                user_name = str(user_name[n])
                for symbol in REMOVE_SYMBOLS_ITEM:
                    user_name = user_name.replace(symbol, "")
                button_title = user_name + "(" + str(user_id) + ")"
                button = [
                    Button(button_title, self.got_to_confirm,
                           source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                           payload=json.dumps({"button_title": button_title, "user_id": user_id}))
                ]
                keyboard.append(button)
            else:
                pass
        button = [
            Button("⬅Назад", ManageAdminUsersMain,
                   source_type=SourcesTypes.GOTO_SOURCE_TYPE)
        ]
        keyboard.append(button)
        return keyboard

    @register_button_handler
    async def got_to_confirm(self, _update, _context):
        payload = json.loads(await self.get_payload(_update, _context))
        _context.user_data["button_title"], _context.user_data["user_id"] = (payload["button_title"],
                                                                             payload["user_id"])
        return await ManageAdminUsersRemoveConfirm().goto(_update, _context)


class ManageAdminUsersRemoveConfirm(Screen):

    async def get_description(self, _update, _context):
        title = ("<strong>Вы уверены, что хотите исключить данного пользователя " +
                 str(_context.user_data["button_title"] + " из числа администраторов?</strong>"))
        return title

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button("Да➖", self.confirm_remove,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button("⬅Назад", ManageAdminUsersRemove,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def confirm_remove(self, _update, _context):
        settings.ADMIN_GROUP.remove(_context.user_data["user_id"])
        return await UserWasMarkedAsAnonim().goto(_update, _context)


class UserWasMarkedAsAnonim(Screen):
    description = "✅<strong>Пользователь был успешно исключен из числа администраторов!</strong>"

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button('⬅️ В меню редактора', ManageAdminUsersMain,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
            [
                Button('⬅️ Убрать ещё администратора', ManageAdminUsersRemove,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
            [
                Button('⬅️ В главное меню', MainMenu,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ],
        ]


class WhatsNew(Screen):
    description = "ERROR 451"

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button("⬅Вернуться в главное меню", MainMenu, source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]

    async def get_description(self, _update, _context):
        current_day = datetime.now().day
        current_month = datetime.now().month
        # current_day = 4
        # current_month = 1
        try:
            title = str()
            title += "<strong>"
            if current_month == 1:
                title += str(MONTH_JAN[current_day])
                title += "</strong>"
                return title
            if current_month == 2:
                title += str(MONTH_FEB[current_day])
                title += "</strong>"
                return title
            if current_month == 3:
                title += str(MONTH_MARCH[current_day])
                title += "</strong>"
                return title
            if current_month == 4:
                title += str(MONTH_APRIL[current_day])
                title += "</strong>"
                return title
            if current_month == 5:
                title += str(MONTH_MAY[current_day])
                title += "</strong>"
                return title
            if current_month == 6:
                title += str(MONTH_JUNE[current_day])
                title += "</strong>"
                return title
            if current_month == 7:
                title += str(MONTH_JULY[current_day])
                title += "</strong>"
                return title
            if current_month == 8:
                title += str(MONTH_AUG[current_day])
                title += "</strong>"
                return title
            if current_month == 9:
                title += MONTH_SEP[current_day]
                title += "</strong>"
                return title
            if current_month == 10:
                title += str(MONTH_OCT[current_day])
                title += '</strong>'
                return title
            if current_month == 11:
                title += str(MONTH_NOV[current_day])
                title += "</strong>"
                return title
            if current_month == 12:
                title += str(MONTH_DEC[current_day])
                title += "</strong>"
                return title
            else:
                return "<strong>Сегодня никаких праздников и мероприятий</strong>"
        except KeyError:
            return "<strong>Сегодня никаких праздников и мероприятий</strong>"


class Options(Screen):
    description = '<strong>Выберите подходящие для Вас параметры</strong>'

    async def add_default_keyboard(self, _update, _context):
        global users_cursor
        user = _update.effective_user
        notification_button_title = str()
        users_cursor.execute("SELECT user_permission FROM Users WHERE user_id = ?", (user.id,))
        notification_permission = users_cursor.fetchone()
        notification_permission = str(notification_permission)
        for symbol in REMOVE_SYMBOLS_ITEM:
            notification_permission = notification_permission.replace(symbol, "")
        notification_permission = int(notification_permission)
        if notification_permission == 0:
            notification_button_title = "Включить "
        if notification_permission == 1:
            notification_button_title = "Выключить "
        notification_button_title += "рассылки от бота"
        return [
            [
                Button(notification_button_title, self.edit_notification_permission,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({"index": notification_permission}))
            ],
            [
                Button('⬅️ Вернуться в главный экран', MainMenu,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def edit_notification_permission(self, _update, _context):
        global users_cursor
        payload = json.loads(await self.get_payload(_update, _context))
        notification_permission = payload["index"]
        if notification_permission == 1:
            notification_permission = 0
        else:
            notification_permission = 1
        user = _update.effective_user
        users_cursor.execute(
            'UPDATE Users set user_permission = ? WHERE user_id = ?', (notification_permission, user.id))
        users_connection.commit()
        return await self.goto(_update, _context)


class SchoolTasks(Screen):
    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button('⬅️ Вернуться в главный экран', MainMenu,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
        ]


class ManageSchoolTasksMain(Screen):
    description = '<strong>Какие изменения Вы хотите внести в задачник?</strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button('Добавить задание➕', ManageSchoolTasksAdd,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
            [
                Button('Изменить задание✖', self.go_to_change_tasks_screen,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE),
            ],
            [
                Button('Удалить задание➖', self.go_to_remove_tasks_screen,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE),
            ],
            [
                Button('⬅️ Вернуться в главный экран', MainMenu,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def go_to_remove_tasks_screen(self, _update, _context):
        global cursor
        cursor.execute("select count(*) from SchoolTasker")
        database_length = cursor.fetchone()
        database_length = str(database_length)
        for symbol in REMOVE_SYMBOLS_INDEX:
            database_length = database_length.replace(symbol, "")
        database_length = int(database_length)
        if database_length > 0:
            ManageSchoolTasksRemove.description = "<strong>Какое из этих заданий Вы хотите удалить?</strong>"
            return await ManageSchoolTasksRemove().goto(_update, _context)
        if database_length < 1:
            ManageSchoolTasksRemove.description = "<strong>На данный момент список заданий пуст!</strong>"
            return await ManageSchoolTasksRemove().goto(_update, _context)

    @register_button_handler
    async def go_to_change_tasks_screen(self, _update, _context):
        global cursor
        cursor.execute("select count(*) from SchoolTasker")
        database_length = cursor.fetchone()
        database_length = str(database_length)
        for symbol in REMOVE_SYMBOLS_INDEX:
            database_length = database_length.replace(symbol, "")
        database_length = int(database_length)
        if database_length > 0:
            ManageSchoolTasksChangeMain.description = "<strong>Какое из этих заданий Вы хотите изменить?</strong>"
            return await ManageSchoolTasksChangeMain().goto(_update, _context)
        if database_length < 1:
            ManageSchoolTasksChangeMain.description = "<strong>На данный момент список заданий пуст!</strong>"
            return await ManageSchoolTasksChangeMain().goto(_update, _context)


class ManageSchoolTasksAdd(Screen):
    description = '<strong>По какому предмету будет задание?</strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button("Алгебра", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({'task_item': "Алгебра"})),
                Button("Английский язык", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({'task_item': "Английский язык"})),
                Button("Биология", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({'task_item': "Биология"})),
                Button("География", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({'task_item': "География"})),
                Button("Музыка", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({'task_item': "Музыка"})),
            ],
            [
                Button("Геометрия", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({'task_item': "Геометрия"})),
                Button("Информатика", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({'task_item': "Информатика"})),
                Button("История", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({'task_item': "История"})),
                Button("Литература", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({'task_item': "Литература"})),
                Button("Обществознание", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({'task_item': "Обществознание"})),
            ],
            [

                # Button("Решение задач повышенного уровня по алгебре",
                #        self.get_school_item,
                #        source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                #        payload=json.dumps({'task_item': "Решение задач повышенного уровня по алгебре"})),
            ],
            [Button("ОБЖ", self.get_school_item,
                    source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                    payload=json.dumps({'task_item': "ОБЖ"})),
             Button("Русский язык", self.get_school_item,
                    source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                    payload=json.dumps({'task_item': "Русский язык"})),
             Button("Технология", self.get_school_item,
                    source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                    payload=json.dumps({'task_item': "Технология"})),
             Button("Физика", self.get_school_item,
                    source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                    payload=json.dumps({'task_item': "Физика"})),
             Button("Химия", self.get_school_item,
                    source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                    payload=json.dumps({'task_item': "Химия"})),
             ],
            [
                Button('⬅️ Назад', ManageSchoolTasksMain,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),

            ]
        ]

    @register_button_handler
    async def get_school_item(self, update, context):
        payload = json.loads(await self.get_payload(update, context))
        context.user_data['task_item'] = payload['task_item']
        if context.user_data["task_item"] == "Английский язык" or context.user_data["task_item"] == "Информатика":
            return await ManageSchoolTasksAddGroupNumber().goto(update, context)
        else:
            return await ManageSchoolTasksAddDetails().goto(update, context)


class ManageSchoolTasksAddGroupNumber(Screen):
    description = '<strong>Какой группе дано задание?</strong>'

    async def add_default_keyboard(self, _update, _context):
        keyboard = []
        buttons = []
        if _context.user_data["task_item"] == "Английский язык":
            buttons.append(
                Button('Группа 1️⃣(Мартиросян Астхик Нориковна)', self.get_group_number,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({"group_number": 1})))
            buttons.append(
                Button('Группа 2️⃣(Кравцова Анна Сергеевна)', self.get_group_number,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({"group_number": 2})))

        if _context.user_data['task_item'] == "Информатика":
            buttons.append(
                Button('Группа 1️⃣(Мамедова Наталья Николаевна)', self.get_group_number,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({"group_number": 1})))
            buttons.append(
                Button('Группа 2️⃣(Фокин Алексей Юрьевич)', self.get_group_number,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({"group_number": 2})))
        keyboard.append(buttons)
        keyboard.append(
            [
                Button('⬅️ Назад', self.return_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ])
        return keyboard

    @register_button_handler
    async def get_group_number(self, _update, _context):
        payload = json.loads(await self.get_payload(_update, _context))
        _context.user_data["group_number"] = payload["group_number"]
        return await ManageSchoolTasksAddDetails().goto(_update, _context)

    @register_button_handler
    async def return_back(self, _update, _context):
        return await ManageSchoolTasksAdd().goto(_update, _context)


async def add_task_school(_update, _context, task_item, task_description, group_number, task_day, task_month):
    global cursor
    cursor.execute("select count(*) from SchoolTasker")
    Global.index_store = cursor.fetchone()
    database_length = Global.index_store
    Global.index_store = str(Global.index_store)
    database_length = str(database_length)
    for symbol in REMOVE_SYMBOLS_INDEX:
        Global.index_store = Global.index_store.replace(symbol, "")
        database_length = database_length.replace(symbol, "")
    database_length = int(database_length)
    Global.index_store = int(Global.index_store)
    hypertime = str()
    # hypertime = str(0) + str(task_month) + str(0) + str(task_day)
    if int(task_month) < 10:
        hypertime = str(0)
    hypertime += str(task_month)
    if task_day < 10:
        hypertime += str(0)
    hypertime += str(task_day)
    if database_length == 0:
        # index_store = 0
        cursor.execute(
            'INSERT INTO SchoolTasker (item_name, item_index, group_number, task_description, task_day, task_month, '
            'hypertime)'
            'VALUES'
            '(?,?,?,?,?,?,?)',
            (task_item, Global.index_store, group_number, task_description, task_day,
             task_month, hypertime,))
        connection.commit()
        cursor.execute("select count(*) from SchoolTasker")
        Global.index_store = cursor.fetchone()
        database_length = Global.index_store
        Global.index_store = str(Global.index_store)
        database_length = str(database_length)
        for symbol in REMOVE_SYMBOLS_INDEX:
            Global.index_store = Global.index_store.replace(symbol, "")
            database_length = database_length.replace(symbol, "")

        database_length = int(database_length)
        Global.index_store = int(Global.index_store)
        if database_length == 1:
            Global.index_store = 0
        if database_length > 1:
            Global.index_store = database_length
            Global.index_store -= 1
        cursor.execute('SELECT task_day FROM SchoolTasker')
        task_day = cursor.fetchall()[0]
        task_day = str(task_day)
        for symbol in REMOVE_SYMBOLS_ITEM:
            task_day = task_day.replace(symbol, "")
        cursor.execute('SELECT task_month FROM SchoolTasker')
        task_month = cursor.fetchall()[0]
        task_month = str(task_month)
        for symbol in REMOVE_SYMBOLS_ITEM:
            task_month = task_month.replace(symbol, "")
        if task_month == "1":
            task_month = "января"
        if task_month == "2":
            task_month = "февраля"
        if task_month == "3":
            task_month = "марта"
        if task_month == "4":
            task_month = "апреля"
        if task_month == "5":
            task_month = "мая"
        if task_month == "6":
            task_month = "июня"
        if task_month == "7":
            task_month = "июля"
        if task_month == "8":
            task_month = "августа"
        if task_month == "9":
            task_month = "сентября"
        if task_month == "10":
            task_month = "октября"
        if task_month == "11":
            task_month = "ноября"
        if task_month == "12":
            task_month = "декабря"
        task_time = "<strong>На " + str(task_day) + " " + str(task_month) + " :</strong>" + "\n"
        Global.last_day = task_day
        Global.last_month = task_month
        cursor.execute('SELECT item_name FROM SchoolTasker')
        item_name = cursor.fetchall()[0]
        item_name = str(item_name)
        for symbol in REMOVE_SYMBOLS_ITEM:
            item_name = item_name.replace(symbol, "")
        if item_name == "Английский язык" or item_name == "Информатика":
            item_name += " ("
            cursor.execute('SELECT group_number FROM SchoolTasker')
            group_number = cursor.fetchall()[0]
            group_number = str(group_number)
            for symbol in REMOVE_SYMBOLS_ITEM:
                group_number = group_number.replace(symbol, "")
            item_name += group_number
            item_name += "ая группа)"

        item_name += " : "
        cursor.execute('SELECT task_description FROM SchoolTasker')
        task_description = cursor.fetchall()[0]
        task_description = str(task_description)
        for symbol in REMOVE_SYMBOLS_ITEM:
            task_description = task_description.replace(symbol, "")
        task_description += "\n"
        SchoolTasks.description = task_time + item_name + task_description
        ManageSchoolTasksRemoveConfirm.description = "<strong>Какое из этих заданий Вы хотите удалить?</strong>"
        TaskWasAdded.task_description, TaskWasAdded.group_number, TaskWasAdded.task_day, TaskWasAdded.task_month = (
            task_description, group_number, task_day, task_month)
        return await TaskWasAdded().jump(_update, _context)
    elif database_length > 0:
        cursor.execute(
            'INSERT INTO SchoolTasker (item_name, item_index, group_number, task_description, task_day, task_month, '
            'hypertime)'
            'VALUES'
            '(?,?,?,?,?,?,?)',
            (task_item, Global.index_store, group_number, task_description, task_day,
             task_month, hypertime,))
        connection.commit()
        cursor.execute("select count(*) from SchoolTasker")
        Global.index_store = cursor.fetchone()
        database_length = Global.index_store
        Global.index_store = str(Global.index_store)
        database_length = str(database_length)
        for symbol in REMOVE_SYMBOLS_INDEX:
            Global.index_store = Global.index_store.replace(symbol, "")
            database_length = database_length.replace(symbol, "")
        database_length = int(database_length)
        Global.index_store = int(Global.index_store)
        if database_length == 1:
            Global.index_store = 0
        if database_length > 1:
            Global.index_store = database_length
            Global.index_store -= 1
        cursor.execute('SELECT task_day FROM SchoolTasker WHERE item_index = ?',
                       (Global.index_store,))
        connection.commit()
        task_day = cursor.fetchone()
        task_day = str(task_day)
        for symbol in REMOVE_SYMBOLS_ITEM:
            task_day = task_day.replace(symbol, "")
        cursor.execute('SELECT task_month FROM SchoolTasker WHERE item_index = ?',
                       (Global.index_store,))
        connection.commit()
        task_month = cursor.fetchone()
        task_month = str(task_month)
        for symbol in REMOVE_SYMBOLS_ITEM:
            task_month = task_month.replace(symbol, "")
        if task_month == "1":
            task_month = "января"
        if task_month == "2":
            task_month = "февраля"
        if task_month == "3":
            task_month = "марта"
        if task_month == "4":
            task_month = "апреля"
        if task_month == "5":
            task_month = "мая"
        if task_month == "6":
            task_month = "июня"
        if task_month == "7":
            task_month = "июля"
        if task_month == "8":
            task_month = "августа"
        if task_month == "9":
            task_month = "сентября"
        if task_month == "10":
            task_month = "октября"
        if task_month == "11":
            task_month = "ноября"
        if task_month == "12":
            task_month = "декабря"
        if Global.last_day == task_day and Global.last_month == task_month:
            task_time = ""
        else:
            task_time = "На " + str(task_day) + " " + str(task_month) + " :" + "\n"
        Global.last_day = task_day
        Global.last_month = task_month
        cursor.execute('SELECT item_name FROM SchoolTasker WHERE item_index = ?',
                       (Global.index_store,))
        connection.commit()
        item_name = cursor.fetchone()
        item_name = str(item_name)
        for symbol in REMOVE_SYMBOLS_ITEM:
            item_name = item_name.replace(symbol, "")
        if item_name == "Английский язык" or item_name == "Информатика":
            item_name += " ("
            cursor.execute('SELECT group_number FROM SchoolTasker WHERE item_index = ?',
                           (Global.index_store,))
            connection.commit()
            group_number = cursor.fetchone()
            group_number = str(group_number)
            for symbol in REMOVE_SYMBOLS_ITEM:
                group_number = group_number.replace(symbol, "")
            item_name += group_number
            item_name += "ая группа)"
        else:
            pass
        item_name += " : "
        cursor.execute('SELECT task_description FROM SchoolTasker WHERE item_index = ?',
                       (Global.index_store,))
        connection.commit()
        task_description = cursor.fetchone()
        task_description = str(task_description)
        for symbol in REMOVE_SYMBOLS_ITEM:
            task_description = task_description.replace(symbol, "")
        task_description += "\n"
        SchoolTasks.description += task_time + item_name + task_description
        ManageSchoolTasksRemoveConfirm.description = "<strong>Какое из этих заданий Вы хотите удалить?</strong>"
    ManageSchoolTasksAddDetails.group_number = 1
    TaskWasAdded.task_description, TaskWasAdded.group_number, TaskWasAdded.task_day, TaskWasAdded.task_month = (
        task_description, group_number, task_day, task_month)
    return await TaskWasAdded().jump(_update, _context)


class ReplaceOrAddTask(Screen):
    description = ("Задание по данному предмету уже есть.\n"
                   "Вы действительно хотите добавить новое задание по данному предмету или хотите заменить "
                   "существующее задание на новое?")


class TaskWasChanged(Screen):
    description = "✅<strong>Задание успешно изменено!</strong>"

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button('⬅️ В меню редактора', ManageSchoolTasksMain,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
            [
                Button("⬅ Изменить ещё задания", ManageSchoolTasksChangeMain,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ],
            [
                Button('⬅️ В главное меню', MainMenu,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ],
        ]


class ManageSchoolTasksAddDetails(Screen):
    description = '<strong>Введите текст задания:</strong>'
    staged_once = False
    staged_twice = False
    is_adding_task = False
    task_item = str()
    task_description = str()
    group_number = int(1)
    task_day = str()
    task_month = str()

    async def add_default_keyboard(self, _update, _context):
        if not Global.is_changing_day and not Global.is_changing_month:
            self.is_adding_task = True
        return [
            [
                Button('⬅️ Назад', self.return_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def return_back(self, _update, _context):
        # global
        # = None
        self.staged_once = False
        self.staged_twice = False
        self.is_adding_task = False
        if (Global.is_changing_day or Global.is_changing_month or Global.is_changing_task_description
                or Global.is_changing_group_number):
            Global.is_changing_day = False
            Global.is_changing_month = False
            Global.is_changing_task_description = False
            Global.is_changing_group_number = False
            return await ManageSchoolTasksChangeBase().goto(_update, _context)
        else:
            return await ManageSchoolTasksAdd().goto(_update, _context)

    @register_typing_handler
    async def set_details(self, update, context):
        success_add = False
        user = update.effective_user
        try:
            self.group_number = context.user_data['group_number']
        except KeyError:
            self.group_number = 1
        try:
            deletion_index = context.user_data['deletion_index']
        except KeyError:
            deletion_index = int()
        if str(user.id) in settings.ADMIN_GROUP:
            if self.is_adding_task:
                self.task_item = context.user_data['task_item']
                if not self.staged_once and not self.staged_twice:
                    self.task_description = update.message.text
                    self.description = "<strong>На какое число задано задание?</strong>"
                    self.staged_once = True
                    return await ManageSchoolTasksAddDetails().jump(update, context)
                if self.staged_once and not self.staged_twice:
                    self.task_day = update.message.text
                    try:
                        self.task_day = int(self.task_day)
                        if self.task_day > 31 or self.task_day < 1:
                            return await ManageSchoolTasksAddDetails().jump(update, context)
                        else:
                            pass
                        self.staged_twice = True
                        self.description = "<strong>На какой месяц задано задание?</strong>"
                        return await ManageSchoolTasksAddDetails().jump(update, context)
                    except ValueError:
                        self.description = "<strong>Пожалуйста, введите число!</strong>"
                        return await ManageSchoolTasksAddDetails().jump(update, context)
                if self.staged_once and self.staged_twice:
                    self.task_month = update.message.text
                    if (self.task_month == "Январь" or self.task_month == "Января"
                            or self.task_month == "январь" or self.task_month == "января"):
                        self.task_month = int(1)
                        self.staged_once = False
                        self.staged_twice = False
                        self.description = "<strong>Введите текст задания:</strong>"
                        success_add = True
                        await add_task_school(update, context, self.task_item, self.task_description,
                                              self.group_number, self.task_day, self.task_month)
                    if (self.task_month == "Февраль" or self.task_month == "Февраля"
                            or self.task_month == "февраль" or self.task_month == "февраля"):
                        if int(self.task_day) > 29:
                            self.description = ("<strong>Извините, но в данном месяце не может быть такое количество "
                                                "дней!\nНа какое число дано задание?</strong>")
                            self.staged_twice = False
                            return await ManageSchoolTasksAddDetails().jump(update, context)
                        else:
                            self.task_month = int(2)
                            self.staged_once = False
                            self.staged_twice = False
                            self.description = "<strong>Введите текст задания:</strong>"
                            success_add = True
                            await add_task_school(update, context, self.task_item, self.task_description,
                                                  self.group_number, self.task_day, self.task_month)
                    if (self.task_month == "Март" or self.task_month == "Марта"
                            or self.task_month == "март" or self.task_month == "марта"):
                        self.task_month = int(3)
                        self.staged_once = False
                        self.staged_twice = False
                        self.description = "<strong>Введите текст задания:</strong>"
                        success_add = True
                        await add_task_school(update, context, ManageSchoolTasksAddDetails.task_item,
                                              self.task_description, self.group_number, self.task_day, self.task_month)
                    if (self.task_month == "Апрель" or self.task_month == "Апреля"
                            or self.task_month == "апрель" or self.task_month == "апреля"):
                        if int(self.task_day) > 30:
                            self.description = ("<strong>Извините, но в данном месяце не может быть такое количество "
                                                "дней!\nНа какое число дано задание?</strong>")
                            self.staged_twice = False
                            return await ManageSchoolTasksAddDetails().jump(update, context)
                        else:
                            self.task_month = int(4)
                            self.staged_once = False
                            self.staged_twice = False
                            self.description = "<strong>Введите текст задания:</strong>"
                            success_add = True
                            await add_task_school(update, context, self.task_item, self.task_description,
                                                  self.group_number, self.task_day, self.task_month)
                    if (self.task_month == "Май" or self.task_month == "Мая"
                            or self.task_month == "май" or self.task_month == "мая"):
                        self.task_month = int(5)
                        self.staged_once = False
                        self.staged_twice = False
                        self.description = "<strong>Введите текст задания:</strong>"
                        success_add = True
                        await add_task_school(update, context, self.task_item, self.task_description,
                                              self.group_number, self.task_day, self.task_month)
                    if (self.task_month == "Июнь" or self.task_month == "Июня"
                            or self.task_month == "июнь" or self.task_month == "июня"):
                        if int(self.task_day) > 30:
                            self.description = ("<strong>Извините, но в данном месяце не может быть такое количество "
                                                "дней!\nНа какое число дано задание?</strong>")
                            self.staged_twice = False
                            return await ManageSchoolTasksAddDetails().jump(update, context)
                        else:
                            self.task_month = int(6)
                            self.staged_once = False
                            self.staged_twice = False
                            self.description = "<strong>Введите текст задания:</strong>"
                            success_add = True
                            await add_task_school(update, context, self.task_item, self.task_description,
                                                  self.group_number, self.task_day, self.task_month)
                    if (self.task_month == "Июль" or self.task_month == "Июля"
                            or self.task_month == "июль" or self.task_month == "июля"):
                        if int(self.task_day) > 30:
                            self.description = ("<strong>Извините, но в данном месяце не может быть такое количество "
                                                "дней!\nНа какое число дано задание?</strong>")
                            self.staged_twice = False
                            return await ManageSchoolTasksAddDetails().jump(update, context)
                        else:
                            self.task_month = int(7)
                            self.staged_once = False
                            self.staged_twice = False
                            self.description = "<strong>Введите текст задания:</strong>"
                            success_add = True
                            await add_task_school(update, context, self.task_item, self.task_description,
                                                  self.group_number, self.task_day, self.task_month)
                    if (self.task_month == "Август" or self.task_month == "Августа"
                            or self.task_month == "август" or self.task_month == "августа"):
                        if int(self.task_day) > 30:
                            self.description = ("<strong>Извините, но в данном месяце не может быть такое количество "
                                                "дней!\nНа какое число дано задание?</strong>")
                            self.staged_twice = False
                            return await ManageSchoolTasksAddDetails().jump(update, context)
                        else:
                            self.task_month = int(8)
                            self.staged_once = False
                            self.staged_twice = False
                            self.description = "<strong>Введите текст задания:</strong>"
                            success_add = True
                            await add_task_school(update, context, self.task_item, self.task_description,
                                                  self.group_number, self.task_day, self.task_month)
                    if (self.task_month == "Сентябрь" or self.task_month == "Сентября"
                            or self.task_month == "сентябрь" or self.task_month == "сентября"):
                        if int(self.task_day) > 30:
                            self.description = ("<strong>Извините, но в данном месяце не может быть такое количество "
                                                "дней!\nНа какое число дано задание?</strong>")
                            self.staged_twice = False
                            return await ManageSchoolTasksAddDetails().jump(update, context)
                        else:
                            self.task_month = int(9)
                            self.staged_once = False
                            self.staged_twice = False
                            self.description = "<strong>Введите текст задания:</strong>"
                            success_add = True
                            await add_task_school(update, context, self.task_item, self.task_description,
                                                  self.group_number, self.task_day, self.task_month)
                    if (self.task_month == "Октябрь" or self.task_month == "Октября"
                            or self.task_month == "октябрь" or self.task_month == "октября"):
                        self.task_month = int(10)
                        self.staged_once = False
                        self.staged_twice = False
                        self.description = "<strong>Введите текст задания:</strong>"
                        success_add = True
                        await add_task_school(update, context, self.task_item, self.task_description,
                                              self.group_number, self.task_day, self.task_month)
                    if (self.task_month == "Ноябрь" or self.task_month == "Ноября"
                            or self.task_month == "ноябрь" or self.task_month == "ноября"):
                        if int(self.task_day) > 30:
                            self.description = ("<strong>Извините, но в данном месяце не может быть такое количество "
                                                "дней!\nНа какое число дано задание?</strong>")
                            self.staged_twice = False
                            return await ManageSchoolTasksAddDetails().jump(update, context)
                        else:
                            self.task_month = int(11)
                            self.staged_once = False
                            self.staged_twice = False
                            self.description = "<strong>Введите текст задания:</strong>"
                            success_add = True
                            await add_task_school(update, context, self.task_item, self.task_description,
                                                  self.group_number, self.task_day, self.task_month)
                    if (self.task_month == "Декабрь" or self.task_month == "Декабря"
                            or self.task_month == "декабрь" or self.task_month == "декабря"):
                        self.task_month = int(12)
                        self.staged_once = False
                        self.staged_twice = False
                        self.description = "<strong>Введите текст задания:</strong>"
                        success_add = True
                        await add_task_school(update, context, self.task_item, self.task_description,
                                              self.group_number, self.task_day, self.task_month)
                    if not success_add:
                        return await ManageSchoolTasksAddDetails().jump(update, context)
                    self.is_adding_task = False
            else:
                pass
            if Global.is_changing_task_description:
                self.task_description = update.message.text
                Global.is_changing_task_description = False
                cursor.execute("SELECT item_index FROM SchoolTasker ORDER BY hypertime ASC")
                formattered_index = cursor.fetchall()
                formattered_index = str(formattered_index[deletion_index])
                for symbol in REMOVE_SYMBOLS_ITEM:
                    formattered_index = formattered_index.replace(symbol, "")
                cursor.execute("SELECT item_name FROM SchoolTasker")
                item_name = cursor.fetchall()
                item_name = str(item_name[int(formattered_index)])
                for symbol in REMOVE_SYMBOLS_ITEM:
                    item_name = item_name.replace(symbol, "")
                cursor.execute("SELECT task_description FROM SchoolTasker")
                task_description = cursor.fetchall()
                task_description = str(task_description[int(formattered_index)])
                for symbol in REMOVE_SYMBOLS_ITEM:
                    task_description = task_description.replace(symbol, "")
                cursor.execute("SELECT group_number FROM SchoolTasker")
                group_number = cursor.fetchall()
                group_number = str(group_number[int(formattered_index)])
                for symbol in REMOVE_SYMBOLS_ITEM:
                    group_number = group_number.replace(symbol, "")
                cursor.execute("SELECT task_day FROM SchoolTasker")
                task_day = cursor.fetchall()
                task_day = str(task_day[int(formattered_index)])
                for symbol in REMOVE_SYMBOLS_ITEM:
                    task_day = task_day.replace(symbol, "")
                cursor.execute("SELECT task_month FROM SchoolTasker")
                task_month = cursor.fetchall()
                task_month = str(task_month[int(formattered_index)])
                for symbol in REMOVE_SYMBOLS_ITEM:
                    task_month = task_month.replace(symbol, "")
                if item_name == "Английский язык" or item_name == "Информатика":
                    LOGGER.info("The user %s (%s) has changed task: На%s.%s по %s(%sая группа): %s",
                                user.username, user.id, task_day, task_month,
                                item_name, group_number, task_description)
                else:
                    LOGGER.info("The user %s (%s) has changed task: На %s.%s по %s: %s", user.username, user.id,
                                task_day, task_month, item_name, task_description)
                cursor.execute("UPDATE SchoolTasker set task_description = ? WHERE item_index = ?",
                               (self.task_description, formattered_index,))
                connection.commit()
                return await TaskWasChanged().jump(update, context)
            if Global.is_changing_day:
                self.task_day = update.message.text
                try:
                    self.task_day = int(self.task_day)
                except ValueError:
                    self.description = "На какой день дано задание?"
                    return await ManageSchoolTasksAddDetails().jump(update, context)
                if not self.task_day < 1 and not self.task_day >= 32:
                    cursor.execute("SELECT task_month FROM SchoolTasker ORDER BY hypertime ASC")
                    check_month = cursor.fetchall()
                    check_month = str(check_month[deletion_index])
                    for symbol in REMOVE_SYMBOLS_ITEM:
                        check_month = check_month.replace(symbol, "")
                    check_task_day = update_day(check_month, self.task_day)
                    if check_task_day:
                        cursor.execute("SELECT item_index FROM SchoolTasker ORDER BY hypertime ASC")
                        formattered_index = cursor.fetchall()
                        formattered_index = str(formattered_index[deletion_index])
                        for symbol in REMOVE_SYMBOLS_ITEM:
                            formattered_index = formattered_index.replace(symbol, "")
                        Global.is_changing_month = False
                        Global.is_changing_day = False
                        cursor.execute("SELECT item_name FROM SchoolTasker")
                        item_name = cursor.fetchall()
                        item_name = str(item_name[int(formattered_index)])
                        for symbol in REMOVE_SYMBOLS_ITEM:
                            item_name = item_name.replace(symbol, "")
                        cursor.execute("SELECT task_description FROM SchoolTasker")
                        task_description = cursor.fetchall()
                        task_description = str(task_description[int(formattered_index)])
                        for symbol in REMOVE_SYMBOLS_ITEM:
                            task_description = task_description.replace(symbol, "")
                        cursor.execute("SELECT group_number FROM SchoolTasker")
                        group_number = cursor.fetchall()
                        group_number = str(group_number[int(formattered_index)])
                        for symbol in REMOVE_SYMBOLS_ITEM:
                            group_number = group_number.replace(symbol, "")
                        cursor.execute("SELECT task_day FROM SchoolTasker")
                        task_day = cursor.fetchall()
                        task_day = str(task_day[int(formattered_index)])
                        for symbol in REMOVE_SYMBOLS_ITEM:
                            task_day = task_day.replace(symbol, "")
                        cursor.execute("SELECT task_month FROM SchoolTasker")
                        task_month = cursor.fetchall()
                        task_month = str(task_month[int(formattered_index)])
                        for symbol in REMOVE_SYMBOLS_ITEM:
                            task_month = task_month.replace(symbol, "")
                        if item_name == "Английский язык" or item_name == "Информатика":
                            LOGGER.info("The user %s (%s) has changed task: На %s.%s по %s(%sая группа): %s",
                                        user.username, user.id, task_day, task_month, item_name, group_number,
                                        task_description)
                        else:
                            LOGGER.info("The user %s (%s) has changed task: На %s.%s по %s: %s",
                                        user.username, user.id, task_day, task_month, item_name, task_description)
                        cursor.execute("UPDATE SchoolTasker set task_day = ? WHERE item_index = ?",
                                       (self.task_day, formattered_index,))
                        connection.commit()
                        cursor.execute("SELECT task_month FROM SchoolTasker ORDER BY hypertime ASC")
                        task_month = cursor.fetchall()
                        task_month = str(task_month[deletion_index])
                        for symbol in REMOVE_SYMBOLS_ITEM:
                            task_month = task_month.replace(symbol, "")
                        task_month = int(task_month)
                        hypertime = str()
                        if task_month < 10:
                            hypertime += str(0)
                        hypertime += str(task_month)
                        if int(self.task_day) < 10:
                            hypertime += str(0)
                        hypertime += str(self.task_day)
                        cursor.execute("UPDATE SchoolTasker set hypertime = ? WHERE item_index = ?",
                                       (hypertime, formattered_index,))
                        connection.commit()
                        return await TaskWasChanged().jump(update, context)
                    else:
                        self.description = "На какой день дано задание?"
                        return await ManageSchoolTasksAddDetails().jump(update, context)
                else:
                    self.description = "На какой день дано задание?"
                    return await ManageSchoolTasksAddDetails().jump(update, context)
            if Global.is_changing_month:
                self.task_month = update.message.text
                cursor.execute("SELECT task_day FROM SchoolTasker ORDER BY hypertime ASC")
                check_day = cursor.fetchall()
                check_day = str(check_day[deletion_index])
                for symbol in REMOVE_SYMBOLS_ITEM:
                    check_day = check_day.replace(symbol, "")
                check_day = int(check_day)
                check_month = update_month(check_day, self.task_month)
                if check_month:
                    self.staged_once = False
                    self.staged_twice = False
                    self.description = "Введите текст задания:"
                    Global.is_changing_month = False
                    Global.is_changing_day = False
                    cursor.execute("SELECT item_index FROM SchoolTasker ORDER BY hypertime ASC")
                    formattered_index = cursor.fetchall()
                    formattered_index = str(formattered_index[deletion_index])
                    for symbol in REMOVE_SYMBOLS_ITEM:
                        formattered_index = formattered_index.replace(symbol, "")
                    cursor.execute("SELECT item_name FROM SchoolTasker")
                    item_name = cursor.fetchall()
                    item_name = str(item_name[int(formattered_index)])
                    for symbol in REMOVE_SYMBOLS_ITEM:
                        item_name = item_name.replace(symbol, "")
                    cursor.execute("SELECT task_description FROM SchoolTasker")
                    task_description = cursor.fetchall()
                    task_description = str(task_description[int(formattered_index)])
                    for symbol in REMOVE_SYMBOLS_ITEM:
                        task_description = task_description.replace(symbol, "")
                    cursor.execute("SELECT group_number FROM SchoolTasker")
                    group_number = cursor.fetchall()
                    group_number = str(group_number[int(formattered_index)])
                    for symbol in REMOVE_SYMBOLS_ITEM:
                        group_number = group_number.replace(symbol, "")
                    cursor.execute("SELECT task_day FROM SchoolTasker")
                    task_day = cursor.fetchall()
                    task_day = str(task_day[int(formattered_index)])
                    for symbol in REMOVE_SYMBOLS_ITEM:
                        task_day = task_day.replace(symbol, "")
                    cursor.execute("SELECT task_month FROM SchoolTasker")
                    task_month = cursor.fetchall()
                    task_month = str(task_month[int(formattered_index)])
                    for symbol in REMOVE_SYMBOLS_ITEM:
                        task_month = task_month.replace(symbol, "")
                    if item_name == "Английский язык" or item_name == "Информатика":
                        LOGGER.info("The user %s (%s) has changed task: На %s.%s по %s(%sая группа): %s",
                                    user.username, user.id, task_day, task_month, item_name, group_number,
                                    task_description)
                    else:
                        LOGGER.info("The user %s (%s) has changed task: На %s.%s по %s: %s",
                                    user.username, user.id, task_day, task_month, item_name, task_description)
                    cursor.execute("UPDATE SchoolTasker set task_month = ? WHERE item_index = ?",
                                   (check_month, formattered_index,))
                    connection.commit()
                    hypertime = str()
                    if int(check_month) < 10:
                        hypertime += str(0)
                    hypertime += str(check_month)
                    if int(check_day) < 10:
                        hypertime += str(0)
                    hypertime += str(check_day)
                    cursor.execute("UPDATE SchoolTasker set hypertime = ? WHERE item_index = ?",
                                   (hypertime, formattered_index,))
                    connection.commit()
                    return await TaskWasChanged().jump(update, context)
                else:
                    self.description = "<strong>На какой месяц дано задание?</strong>"
                    return await ManageSchoolTasksAddDetails().jump(update, context)


async def send_update_notification(update, context, task_item, task_description, group_number, task_day, task_month):
    global users_cursor
    user = update.effective_user
    task_description01 = task_description[:-1]
    if task_item == "Английский язык" or task_item == "Информатика":
        LOGGER.info("The user %s (%s) has added new task: На %s %s по %s(%sая группа): %s",
                    user.username, user.id, task_day, task_month, task_item, group_number, task_description01)
    else:
        LOGGER.info("The user %s (%s) has added new task: На %s %s по %s: %s",
                    user.username, user.id, task_day, task_month, task_item, task_description01)
    id_result = []
    user = update.effective_user
    notification_image = ""
    for id_row in users_cursor.execute('SELECT user_id FROM Users WHERE user_permission = 1 AND user_id != ?',
                                       (user.id,)):
        id_row = list(id_row)
        id_row = int(id_row[0])
        id_result.append(id_row)
    for user_id in id_result:
        users_cursor.execute('SELECT user_name FROM Users WHERE user_id = ?', (user_id,))
        send_name = users_cursor.fetchone()
        send_name = str(send_name)
        for symbol in REMOVE_SYMBOLS_ITEM:
            send_name = send_name.replace(symbol, "")
        notification_title = "Здравствуйте, " + str(send_name) + "!" + "\n"
        notification_title += get_notification_title(task_item, task_description,
                                                     group_number, task_day, task_month)
        config = RenderConfig(
            cover=notification_image,
            chat_id=user_id,
            description=notification_title,
        )
        extra_data = None
        with contextlib.suppress(telegram.error.Forbidden):
            await NotificationScreen().send(context, config=config, extra_data=extra_data)


class TaskWasAdded(Screen):
    description = "✅<strong>Задание успешно добавлено!</strong>"
    task_description = str()
    group_number = str()
    task_day = str()
    task_month = str()

    async def add_default_keyboard(self, _update, _context):
        await send_update_notification(_update, _context, _context.user_data['task_item'], self.task_description,
                                       self.group_number, self.task_day,
                                       self.task_month)
        return [
            [
                Button('⬅️ В меню редактора', ManageSchoolTasksMain,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
            [
                Button('⬅️ Добавить ещё задание', ManageSchoolTasksAdd,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
            [
                Button('⬅️ В главное меню', MainMenu,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ],
        ]


class ManageSchoolTasksRemove(Screen):
    global cursor
    tasks_numbers = []

    # description = 'На данный момент список заданий пуст!'

    async def add_default_keyboard(self, _update, _context):
        global cursor
        cursor.execute("select count(*) from SchoolTasker")
        database_length = cursor.fetchone()
        database_length = str(database_length)

        for symbol in REMOVE_SYMBOLS_ITEM:
            database_length = database_length.replace(symbol, "")
        database_length = int(database_length)
        keyboard = []
        if not database_length > 99:
            for task_index in range(database_length):
                try:
                    button_name = get_button_title(task_index)
                    button_list = [
                        Button(
                            button_name, self.remove_task,
                            source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                            payload=json.dumps({'task_index': task_index}),
                        )
                    ]
                    keyboard.append(button_list)
                except KeyError:
                    pass
            exit_button = [Button('⬅️ Назад', ManageSchoolTasksMain,
                                  source_type=SourcesTypes.GOTO_SOURCE_TYPE)]
            keyboard.append(exit_button)
            return keyboard
        else:
            contact_button = [Button('Связаться с разработчиком📞', 'https://t.me/TheDanskiSon09',
                                     source_type=SourcesTypes.URL_SOURCE_TYPE)]
            exit_button = [Button('⬅️ Назад', ManageSchoolTasksMain,
                                  source_type=SourcesTypes.GOTO_SOURCE_TYPE)]
            keyboard.append(contact_button)
            keyboard.append(exit_button)
            return keyboard

    async def get_description(self, _update, _context):
        global cursor
        cursor.execute("select count(*) from SchoolTasker")
        database_length = cursor.fetchone()
        database_length = str(database_length)
        for symbol in REMOVE_SYMBOLS_ITEM:
            database_length = database_length.replace(symbol, "")
        database_length = int(database_length)
        if database_length > 0 and not database_length > 99:
            return "<strong>Какое из этих заданий Вы хотите удалить?</strong>"
        if database_length < 1:
            return "<strong>На данный момент список заданий пуст!</strong>"
        if database_length > 99:
            return ("<strong>Прошу прощения, Я не могу вывести задачи из задачника - возможно превышен лимит возможных "
                    "заданий!😢\n"
                    "Предлагаю Вам связаться с разработчиком, чтобы доложить о случившейся проблеме!📞</strong>")

    @register_button_handler
    async def remove_task(self, update, context):
        payload = json.loads(await self.get_payload(update, context))

        context.user_data['task_index'] = payload['task_index']
        return await ManageSchoolTasksRemoveConfirm().goto(update, context)


class ManageSchoolTasksRemoveConfirm(Screen):
    description = "<strong>Вы действительно хотите удалить данное задание?</strong>"
    deletion_index = 0

    async def add_default_keyboard(self, _update, _context):

        return [
            [
                Button("Удалить🗑️", self.delete_school_task, source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button("⬅Назад", ManageSchoolTasksRemove, source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def delete_school_task(self, _update, _context):
        global cursor
        Global.index_store -= 1

        task_index = _context.user_data['task_index']
        user = _update.effective_user
        cursor.execute("SELECT item_index FROM SchoolTasker ORDER BY hypertime ASC")
        formatted_index = cursor.fetchall()
        formatted_index = str(formatted_index[task_index])
        for symbol in REMOVE_SYMBOLS_ITEM:
            formatted_index = formatted_index.replace(symbol, "")
        formatted_index = int(formatted_index)
        cursor.execute("SELECT item_name FROM SchoolTasker")
        item_name = cursor.fetchall()
        item_name = str(item_name[formatted_index])
        for symbol in REMOVE_SYMBOLS_ITEM:
            item_name = item_name.replace(symbol, "")
        cursor.execute("SELECT task_description FROM SchoolTasker")
        task_description = cursor.fetchall()
        task_description = str(task_description[formatted_index])
        for symbol in REMOVE_SYMBOLS_ITEM:
            task_description = task_description.replace(symbol, "")
        cursor.execute("SELECT group_number FROM SchoolTasker")
        group_number = cursor.fetchall()
        group_number = str(group_number[formatted_index])
        cursor.execute("SELECT task_day FROM SchoolTasker")
        task_day = cursor.fetchall()
        task_day = str(task_day[int(formatted_index)])
        for symbol in REMOVE_SYMBOLS_ITEM:
            task_day = task_day.replace(symbol, "")
        cursor.execute("SELECT task_month FROM SchoolTasker")
        task_month = cursor.fetchall()
        task_month = str(task_month[int(formatted_index)])
        for symbol in REMOVE_SYMBOLS_ITEM:
            task_month = task_month.replace(symbol, "")
        for symbol in REMOVE_SYMBOLS_ITEM:
            group_number = group_number.replace(symbol, "")
        if item_name == "Английский язык" or item_name == "Информатика":
            LOGGER.info("The user %s (%s) has deleted task: На %s.%s по %s(%sая группа): %s",
                        user.username, user.id, task_day, task_month, item_name, group_number, task_description)
        else:
            LOGGER.info("The user %s (%s) has deleted task: На %s.%s по %s: %s",
                        user.username, user.id, task_day, task_month, item_name, task_description)
        cursor.execute('''DELETE FROM SchoolTasker WHERE item_index = ?''', (formatted_index,))
        connection.commit()
        cursor.execute('UPDATE SchoolTasker set item_index = item_index-1 where item_index>?',
                       (formatted_index,))
        connection.commit()
        cursor.execute("select count(*) from SchoolTasker")
        Global.index_store = cursor.fetchone()
        database_length = Global.index_store
        Global.index_store = str(Global.index_store)
        database_length = str(database_length)
        title = str()

        for symbol in REMOVE_SYMBOLS_INDEX:
            Global.index_store = Global.index_store.replace(symbol, "")
            database_length = database_length.replace(symbol, "")

        database_length = int(database_length)
        Global.index_store = int(Global.index_store)

        if database_length == 1:
            cursor.execute("select count(*) from SchoolTasker")
            Global.index_store = cursor.fetchone()
            database_length = Global.index_store
            Global.index_store = str(Global.index_store)
            database_length = str(database_length)

            for symbol in REMOVE_SYMBOLS_INDEX:
                Global.index_store = Global.index_store.replace(symbol, "")
                database_length = database_length.replace(symbol, "")

            Global.index_store = int(Global.index_store)
            cursor.execute('SELECT task_day FROM SchoolTasker')
            task_day = cursor.fetchall()[0]
            task_day = str(task_day)

            for symbol in REMOVE_SYMBOLS_ITEM:
                task_day = task_day.replace(symbol, "")

            cursor.execute('SELECT task_month FROM SchoolTasker')
            task_month = cursor.fetchall()[0]
            task_month = str(task_month)

            for symbol in REMOVE_SYMBOLS_ITEM:
                task_month = task_month.replace(symbol, "")

            if task_month == "1":
                task_month = "января"
            if task_month == "2":
                task_month = "февраля"
            if task_month == "3":
                task_month = "марта"
            if task_month == "4":
                task_month = "апреля"
            if task_month == "5":
                task_month = "мая"
            if task_month == "6":
                task_month = "июня"
            if task_month == "9":
                task_month = "сентября"
            if task_month == "10":
                task_month = "октября"
            if task_month == "11":
                task_month = "ноября"
            if task_month == "12":
                task_month = "декабря"

            task_time = "<strong>На " + str(task_day) + " " + str(task_month) + " :</strong>" + "\n"
            Global.last_day = task_day
            Global.last_month = task_month
            cursor.execute('SELECT item_name FROM SchoolTasker')
            item_name = cursor.fetchall()[0]
            item_name = str(item_name)

            for symbol in REMOVE_SYMBOLS_ITEM:
                item_name = item_name.replace(symbol, "")

            if item_name == "Английский язык" or item_name == "Информатика":
                item_name += " ("
                cursor.execute('SELECT group_number FROM SchoolTasker')
                group_number = cursor.fetchall()[0]
                group_number = str(group_number)
                for symbol in REMOVE_SYMBOLS_ITEM:
                    group_number = group_number.replace(symbol, "")
                item_name += group_number
                item_name += "ая группа)"

            item_name += " : "
            cursor.execute('SELECT task_description FROM SchoolTasker')
            task_description = cursor.fetchall()[0]
            task_description = str(task_description)
            for symbol in REMOVE_SYMBOLS_ITEM:
                task_description = task_description.replace(symbol, "")
            task_description += "\n"
            title = task_time + item_name + task_description
        elif database_length > 1:
            n = int(0)
            Global.open_date = True
            for i in range(database_length):
                title = get_multipy_async(n, title, 0)
                Global.open_date = False
                n += 1
        if not title:
            SchoolTasks.description = "<strong>На данный момент список заданий пуст!</strong>"
        else:
            SchoolTasks.description = title
        return await TaskWasRemoved().goto(_update, _context)

    async def get_description(self, _update, _context):
        return "<strong>Вы действительно хотите удалить данное задание?</strong>"


class TaskWasRemoved(Screen):
    description = "✅<strong>Задание успешно удалено!</strong>"

    async def add_default_keyboard(self, _update, _context):
        cursor.execute("select count(*) from SchoolTasker")
        database_length = cursor.fetchone()
        database_length = str(database_length)
        for symbol in REMOVE_SYMBOLS_ITEM:
            database_length = database_length.replace(symbol, "")
        database_length = int(database_length)
        if database_length > 0:
            return [
                [
                    Button('⬅️ В меню редактора', ManageSchoolTasksMain,
                           source_type=SourcesTypes.GOTO_SOURCE_TYPE),
                ],
                [
                    Button('⬅️ Удалить  ещё задание', ManageSchoolTasksRemove,
                           source_type=SourcesTypes.GOTO_SOURCE_TYPE),
                ],
                [
                    Button('⬅️ В главное меню', MainMenu,
                           source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                ],
            ]
        elif database_length < 1:
            return [
                [
                    Button('⬅️ В меню редактора', ManageSchoolTasksMain,
                           source_type=SourcesTypes.GOTO_SOURCE_TYPE),
                ],
                [
                    Button('⬅️ В главное меню', MainMenu,
                           source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                ],
            ]


class ManageSchoolTasksChangeBase(Screen):
    description = "<strong>Что Вы хотите изменить в данном задании?</strong>"

    async def add_default_keyboard(self, _update, _context):
        global cursor
        cursor.execute("SELECT item_name FROM SchoolTasker ORDER BY hypertime ASC")
        check_item = cursor.fetchall()
        check_item = str(check_item[_context.user_data['task_index']])
        keyboard = [
            [
                Button("Предмет", self.change_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({"task_index": _context.user_data['task_index']}))
            ],
            [
                Button("Задание", self.change_school_task,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({"deletion_index": _context.user_data['task_index']}))
            ],
            [
                Button("День", self.change_task_day,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({"deletion_index": _context.user_data['task_index']}))
            ],
            [
                Button("Месяц", self.change_task_month,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({"deletion_index": _context.user_data['task_index']}))
            ],
            [
                Button("⬅Назад", ManageSchoolTasksChangeMain,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]
        for symbol in REMOVE_SYMBOLS_ITEM:
            check_item = check_item.replace(symbol, "")
        if check_item == "Английский язык" or check_item == "Информатика":
            keyboard.insert(2, [
                Button("Группу", ManageSchoolTasksChangeGroupNumber,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ], )
        return keyboard

    @register_button_handler
    async def change_task_month(self, update, context):
        return await ManageSchoolTasksChangeMonth().goto(update, context)

    @register_button_handler
    async def change_task_day(self, update, context):
        return await ManageSchoolTasksChangeDay().goto(update, context)

    @register_button_handler
    async def change_school_task(self, update, context):
        return await ManageSchoolTasksChangeTask().goto(update, context)

    @register_button_handler
    async def change_school_item(self, update, context):
        payload = json.loads(await self.get_payload(update, context))

        context.user_data['task_index'] = payload['task_index']
        return await ManageSchoolTasksChangeItem().goto(update, context)


class ManageSchoolTasksChangeMain(Screen):
    global cursor

    async def add_default_keyboard(self, _update, _context):
        global cursor
        cursor.execute("select count(*) from SchoolTasker")
        database_length = cursor.fetchone()
        database_length = str(database_length)
        for symbol in REMOVE_SYMBOLS_ITEM:
            database_length = database_length.replace(symbol, "")
        database_length = int(database_length)
        keyboard = []
        if not database_length > 99:
            for task_index in range(database_length):
                cursor.execute("SELECT item_index FROM SchoolTasker ORDER BY hypertime")
                button_name = get_button_title(task_index)
                new_button = [Button(button_name, self.change_task,
                                     source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                                     payload=json.dumps({'task_index': task_index}))]
                keyboard.append(new_button)
            exit_button = [Button('⬅️ Назад', ManageSchoolTasksMain,
                                  source_type=SourcesTypes.GOTO_SOURCE_TYPE)]
            keyboard.append(exit_button)
            return keyboard
        else:
            contact_button = [Button('Связаться с разработчиком📞', 'https://t.me/TheDanskiSon09',
                                     source_type=SourcesTypes.URL_SOURCE_TYPE)]
            exit_button = [Button('⬅️ Назад', ManageSchoolTasksMain,
                                  source_type=SourcesTypes.GOTO_SOURCE_TYPE)]
            keyboard.append(contact_button)
            keyboard.append(exit_button)
            return keyboard

    async def get_description(self, _update, _context):
        global cursor
        cursor.execute("select count(*) from SchoolTasker")
        database_length = cursor.fetchone()
        database_length = str(database_length)
        for symbol in REMOVE_SYMBOLS_ITEM:
            database_length = database_length.replace(symbol, "")
        database_length = int(database_length)
        # database_length = 120
        if database_length > 0 and not database_length > 99:
            return "<strong>Какое из этих заданий Вы хотите изменить?</strong>"
        if database_length < 1:
            return "<strong>На данный момент список заданий пуст!</strong>"
        if database_length > 99:
            return ("<strong>Прошу прощения, Я не могу вывести задачи из задачника - возможно превышен лимит возможных "
                    "заданий!😢\n"
                    "Предлагаю Вам связаться с разработчиком, чтобы доложить о случившейся проблеме!📞</strong>")

    @register_button_handler
    async def change_task(self, update, context):
        payload = json.loads(await self.get_payload(update, context))

        context.user_data['task_index'] = payload['task_index']
        return await ManageSchoolTasksChangeBase().goto(update, context)


class ManageSchoolTasksChangeItem(Screen):
    description = "<strong>По какому предмету будет задание?</strong>"

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button("Алгебра", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({"task_item": "Алгебра", "task_index": _context.user_data['task_index']})),
                Button("Английский язык", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps(
                           {"task_item": "Английский язык", "task_index": _context.user_data['task_index']})),
                Button("Биология", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({"task_item": "Биология", "task_index": _context.user_data['task_index']})),
                Button("География", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({"task_item": "География", "task_index": _context.user_data['task_index']})),
                Button("Музыка", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({"task_item": "Музыка", "task_index": _context.user_data['task_index']})),
            ],
            [
                Button("Геометрия", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({"task_item": "Геометрия", "task_index": _context.user_data['task_index']})),
                Button("Информатика", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps(
                           {"task_item": "Информатика", "task_index": _context.user_data['task_index']})),
                Button("История", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({"task_item": "История", "task_index": _context.user_data['task_index']})),
                Button("Литература", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps({"task_item": "Литература", "task_index": _context.user_data['task_index']})),
                Button("Обществознание", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=json.dumps(
                           {"task_item": "Обществознание", "task_index": _context.user_data['task_index']})),
            ],
            [

                # Button("Решение задач повышенного уровня по алгебре",
                #        self.change_item,
                #        source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                #        payload=json.dumps({"task_item": "Решение задач повышенного уровня по алгебре",
                #                            "task_index": _context.user_data['task_index']})),
            ],
            [Button("ОБЖ", self.change_item,
                    source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                    payload=json.dumps({"task_item": "ОБЖ", "task_index": _context.user_data['task_index']})),
             Button("Русский язык", self.change_item,
                    source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                    payload=json.dumps(
                        {"task_item": "Русский язык", "task_index": _context.user_data['task_index']})),
             Button("Технология", self.change_item,
                    source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                    payload=json.dumps({"task_item": "Технология", "task_index": _context.user_data['task_index']})),
             Button("Физика", self.change_item,
                    source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                    payload=json.dumps({"task_item": "Физика", "task_index": _context.user_data['task_index']})),
             Button("Химия", self.change_item,
                    source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                    payload=json.dumps({"task_item": "Химия", "task_index": _context.user_data['task_index']}))
             ],
            [
                Button('⬅️ Назад', ManageSchoolTasksChangeBase,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),

            ]
        ]

    @register_button_handler
    async def change_item(self, update, context):
        global cursor
        user = update.effective_user
        payload = json.loads(await self.get_payload(update, context))
        context.user_data['task_item'], context.user_data['task_index'] = payload['task_item'], payload['task_index']
        cursor.execute("SELECT item_index from SchoolTasker ORDER BY hypertime ASC")
        formattered_index = cursor.fetchall()
        formattered_index = str(formattered_index[context.user_data["task_index"]])
        for symbol in REMOVE_SYMBOLS_ITEM:
            formattered_index = formattered_index.replace(symbol, "")
        cursor.execute("SELECT item_name FROM SchoolTasker")
        item_name = cursor.fetchall()
        item_name = str(item_name[int(formattered_index)])
        for symbol in REMOVE_SYMBOLS_ITEM:
            item_name = item_name.replace(symbol, "")
        cursor.execute("SELECT task_description FROM SchoolTasker")
        task_description = cursor.fetchall()
        task_description = str(task_description[int(formattered_index)])
        for symbol in REMOVE_SYMBOLS_ITEM:
            task_description = task_description.replace(symbol, "")
        cursor.execute("SELECT group_number FROM SchoolTasker")
        group_number = cursor.fetchall()
        group_number = str(group_number[int(formattered_index)])
        for symbol in REMOVE_SYMBOLS_ITEM:
            group_number = group_number.replace(symbol, "")
        cursor.execute("SELECT task_day FROM SchoolTasker")
        task_day = cursor.fetchall()
        task_day = str(task_day[int(formattered_index)])
        for symbol in REMOVE_SYMBOLS_ITEM:
            task_day = task_day.replace(symbol, "")
        cursor.execute("SELECT task_month FROM SchoolTasker")
        task_month = cursor.fetchall()
        task_month = str(task_month[int(formattered_index)])
        if item_name == "Английский язык" or item_name == "Информатика":
            LOGGER.info("The user %s (%s) has changed task: На %s.%s по %s(%sая группа): %s",
                        user.username, user.id, task_day, task_month, item_name, group_number, task_description)
        else:
            LOGGER.info("The user %s (%s) has changed task: На %s.%s по  %s: %s",
                        user.username, user.id, task_day, task_month, item_name, task_description)
        cursor.execute("UPDATE SchoolTasker set item_name = ? WHERE item_index = ?",
                       (context.user_data['task_item'], formattered_index,))
        connection.commit()
        return await TaskWasChanged().goto(update, context)


class ManageSchoolTasksChangeTask(Screen):
    description = "<strong>Введите текст задания:</strong>"
    current_index = int()
    task_description = str()

    async def add_default_keyboard(self, _update, _context):
        Global.is_changing_task_description = True
        payload = json.loads(await self.get_payload(_update, _context))
        _context.user_data["deletion_index"] = payload["deletion_index"]
        return [
            [
                Button("⬅Назад", self.go_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, update, context):
        Global.is_changing_task_description = False
        return await ManageSchoolTasksChangeBase().goto(update, context)


class ManageSchoolTasksChangeDay(Screen):
    description = "<strong>На какой день дано задание?</strong>"
    task_description = str()

    async def add_default_keyboard(self, _update, _context):
        Global.is_changing_day = True
        payload = json.loads(await self.get_payload(_update, _context))
        _context.user_data["deletion_index"] = payload["deletion_index"]
        return [
            [
                Button("⬅Назад", self.go_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, update, context):
        Global.is_changing_day = False
        return await ManageSchoolTasksChangeBase().goto(update, context)


class ManageSchoolTasksChangeMonth(Screen):
    description = "<strong>На какой месяц дано задание?</strong>"
    task_description = str()

    async def add_default_keyboard(self, _update, _context):
        Global.is_changing_month = True
        payload = json.loads(await self.get_payload(_update, _context))
        _context.user_data["deletion_index"] = payload["deletion_index"]
        return [
            [
                Button("⬅Назад", self.go_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, update, context):
        Global.is_changing_month = False
        return await ManageSchoolTasksChangeBase().goto(update, context)


class ManageSchoolTasksChangeGroupNumber(Screen):
    description = "<strong>Какой группе дано задание?</strong>"
    deletion_index = int()

    async def add_default_keyboard(self, _update, _context):
        self.deletion_index = _context.user_data['task_index']
        Global.is_changing_group_number = True
        cursor.execute("SELECT item_name FROM SchoolTasker ORDER BY hypertime ASC")
        check_item = cursor.fetchall()
        check_item = str(check_item[self.deletion_index])
        for symbol in REMOVE_SYMBOLS_ITEM:
            check_item = check_item.replace(symbol, "")
        if check_item == "Английский язык":
            return [
                [
                    Button('Группа 1️⃣(Мартиросян Астхик Нориковна)', self.change_group_number,
                           source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                           payload=json.dumps({"group_number": 1})),
                    Button('Группа 2️⃣(Кравцова Анна Сергеевна)', self.change_group_number,
                           source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                           payload=json.dumps({"group_number": 2}))
                ],
                [
                    Button('⬅️ Назад', self.go_back,
                           source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
                ],
            ]
        if check_item == "Информатика":
            return [
                [
                    Button('Группа 1️⃣(Мамедова Наталья Николаевна)', self.change_group_number,
                           source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                           payload=json.dumps({"group_number": 1})),
                    Button('Группа 2️⃣(Фокин Алексей Юрьевич)', self.change_group_number,
                           source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                           payload=json.dumps({"group_number": 2}))
                ],
                [
                    Button('⬅️ Назад', self.go_back,
                           source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
                ],
            ]

    @register_button_handler
    async def change_group_number(self, update, context):
        user = update.effective_user
        payload = json.loads(await self.get_payload(update, context))
        context.user_data["group_number"] = payload['group_number']
        cursor.execute("SELECT item_index FROM SchoolTasker ORDER BY hypertime ASC")
        formattered_index = cursor.fetchall()
        formattered_index = str(formattered_index[self.deletion_index])
        for symbol in REMOVE_SYMBOLS_ITEM:
            formattered_index = formattered_index.replace(symbol, "")
        logger_alert([user.username, user.id], "change", int(formattered_index))
        cursor.execute("UPDATE SchoolTasker SET group_number = ? WHERE item_index = ?",
                       (context.user_data["group_number"], formattered_index,))
        connection.commit()
        return await TaskWasChanged().goto(update, context)

    @register_button_handler
    async def go_back(self, update, context):
        Global.is_changing_group_number = False
        return await ManageSchoolTasksChangeBase().goto(update, context)
