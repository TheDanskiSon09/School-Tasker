from logging import getLogger
from sqlite3 import connect
from gino import Gino
from utils import *
from PIL import Image
from hammett.conf import settings
from psycopg2 import connect
from psycopg2.errors import InFailedSqlTransaction
from contextlib import suppress

db = Gino()

connection = connect(
    dbname=str(settings.DATABASE_NAME),
    host=str(settings.DATABASE_HOST),
    user=str(settings.DATABASE_USER),
    password=str(settings.DATABASE_PASSWORD),
    port=str(settings.DATABASE_PORT)
)

# connection = connect('school_tasker.db')
cursor = connection.cursor()


# with suppress(InFailedSqlTransaction):
#     cursor.execute('''
# CREATE TABLE IF NOT EXISTS Community (
# name TEXT UNIQUE,
# password TEXT UNIQUE
# )
# ''')



with suppress(InFailedSqlTransaction):
    cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
send_notification TEXT,
id TEXT PRIMARY KEY,
name TEXT
)
''')

with suppress(InFailedSqlTransaction):
    cursor.execute('''
CREATE TABLE IF NOT EXISTS UserCommunities (
user_id TEXT,
class_name TEXT,
user_role_in_class TEXT
)
''')
LOGGER = getLogger('hammett')


class Global:
    last_day = int()
    last_month = int()
    last_year = int()
    index_store = int(0)
    open_date = True


async def convert_to_webp(input_path: str, output_path: str):
    img = Image.open(input_path).convert("RGB")
    img.save(output_path, "webp", quality=80)


async def get_var_from_database(index, need_variable, order: bool, _context):
    if order:
        variable_order = {"item_name": "SELECT item_name FROM " + _context.user_data[
            'CURRENT_CLASS_NAME'] + "_Tasks ORDER BY hypertime ASC",
                          "group_number": "SELECT group_number FROM " + _context.user_data[
                              'CURRENT_CLASS_NAME'] + "_Tasks ORDER BY hypertime ASC",
                          "task_description": "SELECT task_description FROM " + _context.user_data[
                              'CURRENT_CLASS_NAME'] + "_Tasks ORDER BY hypertime ASC",
                          "task_day": "SELECT task_day FROM " + _context.user_data[
                              'CURRENT_CLASS_NAME'] + "_Tasks ORDER BY hypertime ASC",
                          "task_month": "SELECT task_month FROM " + _context.user_data[
                              'CURRENT_CLASS_NAME'] + "_Tasks ORDER BY hypertime ASC",
                          "item_index": "SELECT item_index FROM " + _context.user_data[
                              'CURRENT_CLASS_NAME'] + "_Tasks ORDER BY hypertime ASC",
                          "database_length_SchoolTasker": "SELECT count(*) FROM " + _context.user_data[
                              'CURRENT_CLASS_NAME'] + "_Tasks",
                          "database_length_Users": "SELECT count(*) FROM " + _context.user_data[
                              'CURRENT_CLASS_NAME'] + "_Tasks",
                          "task_year": "SELECT task_year FROM " + _context.user_data[
                              'CURRENT_CLASS_NAME'] + "_Tasks ORDER BY hypertime ASC"}
        title = variable_order[need_variable]
        with suppress(InFailedSqlTransaction):
            cursor.execute(title)
            variable = cursor.fetchall()
            if need_variable == "database_length_SchoolTasker" or need_variable == "database_length_Users":
                variable = get_clean_var(variable, "to_int", False, True)
                return int(variable)
            else:
                variable = get_clean_var(variable, "to_string", index, True)
                return str(variable)
    else:
        variable_select = {"item_name": "SELECT item_name FROM " + _context.user_data[
            'CURRENT_CLASS_NAME'] + "_Tasks WHERE item_index = %s",
                           "group_number": "SELECT group_number FROM " + _context.user_data[
                               'CURRENT_CLASS_NAME'] + "_Tasks WHERE item_index = %s",
                           "task_description": "SELECT task_description FROM " + _context.user_data[
                               'CURRENT_CLASS_NAME'] + "_Tasks WHERE item_index = %s",
                           "task_day": "SELECT task_day FROM " + _context.user_data[
                               'CURRENT_CLASS_NAME'] + "_Tasks WHERE item_index = %s",
                           "task_month": "SELECT task_month FROM " + _context.user_data[
                               'CURRENT_CLASS_NAME'] + "_Tasks WHERE item_index = %s",
                           "task_year": "SELECT task_year FROM " + _context.user_data[
                               'CURRENT_CLASS_NAME'] + "_Tasks WHERE item_index = %s"
                           }
        title = variable_select[need_variable]
        with suppress(InFailedSqlTransaction):
            cursor.execute(title, (index,))
            variable = cursor.fetchone()
            if need_variable == "item_name":
                variable = get_clean_var(variable, "to_string", False, True)
                return str(variable)
            elif need_variable == "task_description":
                variable = get_clean_var(variable, "to_string", False, False)
                return str(variable)
            else:
                variable = get_clean_var(variable, "to_int", False, True)
                return int(variable)


async def logger_alert(user: list, status: str, formattered_index, is_order: bool, _context):
    item_name = await get_var_from_database(formattered_index, "item_name", is_order, _context)
    task_description = await get_var_from_database(formattered_index, "task_description", is_order, _context)
    group_number = await get_var_from_database(formattered_index, "group_number", is_order, _context)
    task_day = await get_var_from_database(formattered_index, "task_day", is_order, _context)
    task_month = await get_var_from_database(formattered_index, "task_month", is_order, _context)
    status_dict = {"add": "added",
                   "delete": "deleted",
                   "change": "changed"}
    title = "The "
    if len(user) < 1:
        title += "SchoolTasker was "
    else:
        title += "user " + str(user[0]) + " (" + str(user[1]) + ")" + " was "
    status = status_dict[status]
    status += " task"
    title += status
    title += ": На " + str(task_day) + "." + str(task_month) + " по " + str(item_name)
    with suppress(InFailedSqlTransaction):
        cursor.execute('SELECT groups FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
                       (item_name,))
        check_groups = cursor.fetchall()
        check_groups = get_clean_var(check_groups, 'to_int', 0, True)
        if check_groups > 1:
            title += "(" + str(group_number) + "ая группа)"
        title += ": " + str(task_description)
        LOGGER.info(title)


async def once_delete_task(school_tasks_screen, _context):
    await logger_alert([], "delete", 0, False, _context)
    try:
        cursor.execute("DELETE FROM SchoolTasker WHERE item_index = %s", (0,))
        connection.commit()
    except InFailedSqlTransaction:
        connection.rollback()
    school_tasks_screen.description = "<strong>На данный момент список заданий пуст!</strong>"


async def get_multipy_async(index, title, _context):
    Global.index_store = await get_var_from_database(None, "database_length_SchoolTasker", True, _context)
    task_day = await get_var_from_database(index, "task_day", True, _context)
    check_day = int(task_day)
    task_month = await get_var_from_database(index, "task_month", True, _context)
    check_month = int(task_month)
    task_year = await get_var_from_database(index, "task_year", True, _context)
    check_year = int(task_year)
    task_month_int = int(task_month)
    task_month = recognise_month(task_month)
    if Global.last_day == task_day and Global.last_month == task_month and Global.last_year == task_year:
        if Global.open_date:
            week_day = get_week_day(task_year, task_month_int, int(task_day))
            if int(task_year) == datetime.now().year:
                task_time = ("<strong>На " + "<em>" + week_day + ", " + str(task_day) + " " + str(
                    task_month) + "</em>"
                             + " :</strong>" + "\n\n")
            else:
                task_time = ("<strong>На " + "<em>" + week_day + ", " + str(task_day) + " " + str(
                    task_month) + " " + str(task_year) + "го года" + "</em>"
                             + " :</strong>" + "\n\n")
        else:
            task_time = ""
    else:
        week_day = get_week_day(task_year, task_month_int, int(task_day))
        if int(task_year) == datetime.now().year:
            task_time = ("<strong>На " + "<em>" + week_day + ", " + str(task_day) + " " + str(
                task_month) + "</em>"
                         + " :</strong>" + "\n\n")
        else:
            task_time = ("<strong>На " + "<em>" + week_day + ", " + str(task_day) + " " + str(
                task_month) + " " + str(task_year) + "го года" + "</em>"
                         + " :</strong>" + "\n\n")
    Global.last_day = task_day
    Global.last_month = task_month
    Global.last_year = task_year
    item_name = await get_var_from_database(index, "item_name", True, _context)
    html_start = "<strong>"
    with suppress(InFailedSqlTransaction):
        cursor.execute('SELECT emoji FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
                       (item_name,))
        emoji = cursor.fetchall()
        emoji = get_clean_var(emoji, 'to_string', 0, True)
    with suppress(InFailedSqlTransaction):
        cursor.execute('SELECT groups FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
                       (item_name,))
        groups_check = cursor.fetchone()
        groups_check = get_clean_var(groups_check, 'to_int', 0, True)
        if groups_check > 1:
            item_name = html_start = "<strong>" + str(emoji) + item_name
            item_name += " ("
            group_number = await get_var_from_database(index, "group_number", True, _context)
            item_name += str(group_number)
            item_name += "ая группа): "
    item_name += '</strong>'
    task_description = await get_var_from_database(index, "task_description", True, _context)
    task_description = recognise_n_tag(task_description)
    html_end = "</strong>\n\n"
    task_description = html_start + task_description + html_end
    current_title = task_time + item_name + task_description
    title += current_title
    return title, current_title, check_day, check_month, check_year


async def get_button_title(index, _context):
    with suppress(InFailedSqlTransaction):
        cursor.execute('SELECT item_name FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Tasks')
        item_name = cursor.fetchall()
        item_name = get_clean_var(item_name, 'to_string', index, True)
    with suppress(InFailedSqlTransaction):
        cursor.execute('SELECT emoji FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
                       (item_name,))
        emoji = cursor.fetchall()
        emoji = get_clean_var(emoji, 'to_string', 0, True)
    with suppress(InFailedSqlTransaction):
        cursor.execute('SELECT groups FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
                       (item_name,))
        check = cursor.fetchall()
        check = get_clean_var(check, 'to_int', False, True)
        item_name = str(emoji) + str(item_name)
        if check > 1:
            group_number = await get_var_from_database(index, "group_number", True, _context)
            item_name += " (" + str(group_number) + "ая группа) "
    task_description = await get_var_from_database(index, "task_description", True, _context)
    task_description = recognise_n_tag(task_description)
    title = item_name
    title += " : "
    title += task_description
    return title


async def get_notification_title(_context, task_description, task_day, task_month_int, task_month,
                                 task_year, stat):
    status_dict = {"change": "изменено",
                   "add": "добавлено"}
    week_day = get_week_day(task_year, task_month_int, int(task_day))
    title = 'В сообществе ' + _context.user_data['CURRENT_CLASS_NAME'] + " на " + "<em>" + week_day + ", " + str(
        task_day)
    if str(task_year) == str(datetime.now().year):
        add_month_txt = " " + str(task_month) + "</em>"
    else:
        add_month_txt = " " + str(task_month) + " " + str(task_year) + "го года" + "</em>"
    title += str(add_month_txt)
    status = status_dict[stat]
    title += " было " + status + " задание по "
    with suppress(InFailedSqlTransaction):
        cursor.execute('SELECT emoji FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE item_index = %s',
                       (_context.user_data['ADDING_TASK_INDEX'],))
        emoji = cursor.fetchall()
        emoji = get_clean_var(emoji, 'to_string', 0, True)
    with suppress(InFailedSqlTransaction):
        cursor.execute(
            'SELECT rod_name FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE item_index = %s',
            (_context.user_data['ADDING_TASK_INDEX'],))
        rod_name = cursor.fetchall()
        rod_name = get_clean_var(rod_name, 'to_string', 0, True)
        add_task_txt = emoji + rod_name
        title += add_task_txt
    with suppress(InFailedSqlTransaction):
        cursor.execute('SELECT groups FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
                       (_context.user_data['ADDING_TASK_NAME'],))
        check_group = cursor.fetchall()
        check_group = get_clean_var(check_group, 'to_int', 0, True)
        if check_group > 1:
            group_txt = " (" + _context.user_data['ADDING_TASK_GROUPS'] + "ая " + "группа) "
            title += group_txt
    title += ": " + task_description + "</strong>"
    return title


async def check_task_status(_context):
    check_db = str(_context.user_data['db_check'])
    with suppress(InFailedSqlTransaction):
        cursor.execute('SELECT * FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Tasks')
        real_db = cursor.fetchall()
        real_db = get_clean_var(real_db, "to_string", 0, True)
        if check_db != real_db:
            return False
        else:
            return True
