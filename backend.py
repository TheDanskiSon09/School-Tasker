from logging import getLogger
from sqlite3 import connect
from utils import *
from PIL import Image

# import psycopg2 as postgresql

# connection = postgresql.connect(database=DATABASE_NAME,
#                                 host=DATABASE_HOST,
#                                 user=DATABASE_USER,
#                                 password=DATABASE_PASSWORD,
#                                 port=DATABASE_PORT)
connection = connect('school_tasker.db')
cursor = connection.cursor()

# cursor.execute('''
# CREATE TABLE IF NOT EXISTS SchoolTasker (
# item_name TEXT,
# item_index INTEGER,
# group_number INTEGER,
# task_description TEXT,
# task_day INT,
# task_month INT,
# task_year INT,
# hypertime INT
# )
# ''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Community (
name UNIQUE,
password UNIQUE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
send_notification TEXT,
id INT PRIMARY KEY,
name TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS UserCommunities (
user_id INT,
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
    is_changing_task_description = False
    is_changing_day = False
    is_changing_month = False
    is_changing_group_number = False
    is_creating_class = False
    is_adding_password_to_class = False
    is_creating_item_name = False
    is_creating_item_rod_name = False
    is_creating_item_group = False
    is_creating_item_emoji = False
    is_changing_item_name = False
    is_changing_item_rod_name = False
    is_changing_item_groups = False
    is_changing_item_emoji = False
    is_changing_class_name = False
    is_changing_class_password = False


async def convert_to_webm(input_path: str, output_path: str):
    img = Image.open(input_path).convert("RGB")
    img.save(output_path, "webp", quality=80)


async def get_var_from_database(index, need_variable, order: bool, context):
    global cursor
    if order:
        variable_order = {"item_name": "SELECT item_name FROM " + context.user_data[
            'CURRENT_CLASS_NAME'] + "_Tasks ORDER BY hypertime ASC",
                          "group_number": "SELECT group_number FROM " + context.user_data[
                              'CURRENT_CLASS_NAME'] + "_Tasks ORDER BY hypertime ASC",
                          "task_description": "SELECT task_description FROM " + context.user_data[
                              'CURRENT_CLASS_NAME'] + "_Tasks ORDER BY hypertime ASC",
                          "task_day": "SELECT task_day FROM " + context.user_data[
                              'CURRENT_CLASS_NAME'] + "_Tasks ORDER BY hypertime ASC",
                          "task_month": "SELECT task_month FROM " + context.user_data[
                              'CURRENT_CLASS_NAME'] + "_Tasks ORDER BY hypertime ASC",
                          "item_index": "SELECT item_index FROM " + context.user_data[
                              'CURRENT_CLASS_NAME'] + "_Tasks ORDER BY hypertime ASC",
                          "database_length_SchoolTasker": "SELECT count(*) FROM " + context.user_data[
                              'CURRENT_CLASS_NAME'] + "_Tasks",
                          "database_length_Users": "SELECT count(*) FROM " + context.user_data[
                              'CURRENT_CLASS_NAME'] + "_Tasks",
                          "task_year": "SELECT task_year FROM " + context.user_data[
                              'CURRENT_CLASS_NAME'] + "_Tasks ORDER BY hypertime ASC"}
        title = variable_order[need_variable]
        cursor.execute(title)
        variable = cursor.fetchall()
        if need_variable == "database_length_SchoolTasker" or need_variable == "database_length_Users":
            variable = get_clean_var(variable, "to_int", False, True)
            return int(variable)
        else:
            variable = get_clean_var(variable, "to_string", index, True)
            return str(variable)
    else:
        variable_select = {"item_name": "SELECT item_name FROM " + context.user_data[
            'CURRENT_CLASS_NAME'] + "_Tasks WHERE item_index = ?",
                           "group_number": "SELECT group_number FROM " + context.user_data[
                               'CURRENT_CLASS_NAME'] + "_Tasks WHERE item_index = ?",
                           "task_description": "SELECT task_description FROM " + context.user_data[
                               'CURRENT_CLASS_NAME'] + "_Tasks WHERE item_index = ?",
                           "task_day": "SELECT task_day FROM " + context.user_data[
                               'CURRENT_CLASS_NAME'] + "_Tasks WHERE item_index = ?",
                           "task_month": "SELECT task_month FROM " + context.user_data[
                               'CURRENT_CLASS_NAME'] + "_Tasks WHERE item_index = ?",
                           "task_year": "SELECT task_year FROM " + context.user_data[
                               'CURRENT_CLASS_NAME'] + "_Tasks WHERE item_index = ?"
                           }
        title = variable_select[need_variable]
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


async def logger_alert(user: list, status: str, formattered_index, is_order: bool, context):
    global cursor
    item_name = await get_var_from_database(formattered_index, "item_name", is_order, context)
    task_description = await get_var_from_database(formattered_index, "task_description", is_order, context)
    group_number = await get_var_from_database(formattered_index, "group_number", is_order, context)
    task_day = await get_var_from_database(formattered_index, "task_day", is_order, context)
    task_month = await get_var_from_database(formattered_index, "task_month", is_order, context)
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
    if item_name == "Английский язык" or item_name == "Информатика":
        title += "(" + str(group_number) + "ая группа)"
    title += ": " + str(task_description)
    LOGGER.info(title)


async def once_delete_task(school_tasks_screen, context):
    await logger_alert([], "delete", 0, False, context)
    cursor.execute("DELETE FROM SchoolTasker WHERE item_index = ?", (0,))
    connection.commit()
    school_tasks_screen.description = "<strong>На данный момент список заданий пуст!</strong>"


async def get_multipy_async(index, title, context):
    Global.index_store = await get_var_from_database(None, "database_length_SchoolTasker", True, context)
    task_day = await get_var_from_database(index, "task_day", True, context)
    check_day = int(task_day)
    task_month = await get_var_from_database(index, "task_month", True, context)
    check_month = int(task_month)
    task_year = await get_var_from_database(index, "task_year", True, context)
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
    item_name = await get_var_from_database(index, "item_name", True, context)
    a = "<strong>"
    b = item_name
    cursor.execute('SELECT emoji FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = ?',
                   (item_name,))
    emoji = cursor.fetchall()
    emoji = get_clean_var(emoji, 'to_string', 0, True)
    item_name = str(a) + str(emoji) + str(b)
    if item_name == "<strong>🇬🇧󠁧󠁢󠁧󠁢Английский язык" or item_name == "<strong>💻Информатика":
        item_name += " ("
        group_number = await get_var_from_database(index, "group_number", True, context)
        item_name += str(group_number)
        item_name += "ая группа)"
    item_name += " : </strong>"
    task_description = await get_var_from_database(index, "task_description", True, context)
    task_description = recognise_n_tag(task_description)
    a = "<strong>"
    b = task_description
    c = "</strong>\n\n"
    task_description = str(a) + str(b) + str(c)
    current_title = task_time + item_name + task_description
    title += current_title
    return title, current_title, check_day, check_month, check_year


async def get_button_title(index, context):
    cursor.execute('SELECT item_name FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks')
    item_name = cursor.fetchall()
    item_name = get_clean_var(item_name, 'to_string', index, True)
    cursor.execute('SELECT emoji FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = ?',
                   (item_name,))
    emoji = cursor.fetchall()
    emoji = get_clean_var(emoji, 'to_string', 0, True)
    cursor.execute('SELECT groups FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = ?',
                   (item_name,))
    check = cursor.fetchall()
    check = get_clean_var(check, 'to_int', False, True)
    item_name = str(emoji) + str(item_name)
    if check > 1:
        group_number = await get_var_from_database(index, "group_number", True, context)
        item_name += " (" + str(group_number) + "ая группа) "
    task_description = await get_var_from_database(index, "task_description", True, context)
    task_description = recognise_n_tag(task_description)
    title = item_name
    title += " : "
    title += task_description
    return title


async def get_notification_title(context, task_description, task_day, task_month_int, task_month,
                                 task_year, stat):
    status_dict = {"change": "изменено",
                   "add": "добавлено"}
    week_day = get_week_day(task_year, task_month_int, int(task_day))
    title = 'В сообществе ' + context.user_data['CURRENT_CLASS_NAME'] + " на " + "<em>" + week_day + ", " + str(
        task_day)
    if str(task_year) == str(datetime.now().year):
        add_month_txt = " " + str(task_month) + "</em>"
    else:
        add_month_txt = " " + str(task_month) + " " + str(task_year) + "го года" + "</em>"
    title += str(add_month_txt)
    status = status_dict[stat]
    title += " было " + status + " задание по "
    cursor.execute('SELECT emoji FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE item_index = ?',
                   (context.user_data['ADDING_TASK_INDEX'],))
    emoji = cursor.fetchall()
    emoji = get_clean_var(emoji, 'to_string', 0, True)
    cursor.execute('SELECT rod_name FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE item_index = ?',
                   (context.user_data['ADDING_TASK_INDEX'],))
    rod_name = cursor.fetchall()
    rod_name = get_clean_var(rod_name, 'to_string', 0, True)
    add_task_txt = emoji + rod_name
    title += add_task_txt
    if int(context.user_data['ADDING_TASK_GROUPS']) > 1:
        group_txt = " (" + context.user_data['ADDING_TASK_GROUPS'] + "ая " + "группа) "
        title += group_txt
    title += ": " + task_description + "</strong>"
    return title


async def check_task_status(context):
    check_db = str(context.user_data['db_check'])
    cursor.execute('SELECT * FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks')
    real_db = cursor.fetchall()
    real_db = get_clean_var(real_db, "to_string", False, True)
    if check_db != real_db:
        return False
    else:
        return True
