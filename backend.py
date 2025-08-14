from contextlib import suppress
from logging import getLogger
from os import listdir, makedirs, remove
from os.path import exists

from bs4 import BeautifulSoup
from hammett.core import Button
from hammett.core.constants import RenderConfig, SourceTypes
from telegram.error import Forbidden, BadRequest

from constants import BUTTON_BACK_TO_MENU
from utils import *
from PIL import Image
from hammett.conf import settings
from mysql.connector import connect

connection = connect(
    host=str(settings.DATABASE_HOST),
    user=str(settings.DATABASE_USER),
    password=str(settings.DATABASE_PASSWORD),
    database=str(settings.DATABASE_NAME),
    port=str(settings.DATABASE_PORT),
    connection_timeout=10,
    autocommit=True
)

cursor = connection.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS Community (
name VARCHAR(255) UNIQUE,
password VARCHAR(255) UNIQUE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
send_notification TEXT,
id VARCHAR(255) PRIMARY KEY,
name TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS UserCommunities (
user_id TEXT,
class_name TEXT,
user_role_in_class TEXT
)
''')
LOGGER = getLogger('hammett')


async def show_notification_screen(update, context, translation_type: str, description, keyboard):
    from school_tasker.screens.screen_notification import ScreenNotification
    new_config = RenderConfig()
    new_config.description = description
    new_config.keyboard = keyboard
    if translation_type == 'send':
        return await ScreenNotification().send(context, config=new_config)
    elif translation_type == 'render':
        return await ScreenNotification().render(update, context, config=new_config)


async def send_update_notification(update, context, status, index, is_order: bool):
    from school_tasker.screens import main_menu
    from school_tasker.screens.carousel_notification_screen import CarouselNotificationScreen
    from school_tasker.screens.school_task_change_main import SchoolTaskChangeMain
    from school_tasker.screens.school_task_management_main import SchoolTaskManagementMain
    from school_tasker.screens.static_notification_screen import StaticNotificationScreen
    user = update.effective_user
    name = get_username(user.first_name, user.last_name, user.username)
    await logger_alert([name, user.id], status, index, is_order, context)
    task_description = await get_var_from_database(index, "task_description", is_order, context)
    task_day = await get_var_from_database(index, "task_day", is_order, context)
    task_month = await get_var_from_database(index, "task_month", is_order, context)
    task_month_int = int(task_month)
    task_month = recognise_month(task_month)
    task_year = await get_var_from_database(index, "task_year", is_order, context)
    user_id_list = []
    cursor.execute(
        'SELECT id FROM Users WHERE send_notification = 1 AND id IN (SELECT user_id FROM UserCommunities WHERE class_name = %s)',
        (context.user_data['CURRENT_CLASS_NAME'],))
    extracted_id = cursor.fetchall()
    for id_row in extracted_id:
        id_row = list(id_row)
        id_row = int(id_row[0])
        user_id_list.append(id_row)
    for user_id in user_id_list:
        cursor.execute("SELECT name FROM Users WHERE id = %s", (user_id,))
        user_name = cursor.fetchall()
        user_name = get_clean_var(user_name, "to_string", 0, True)
        notification_title = "<strong>Здравствуйте, " + str(user_name) + "!" + "\n"
        notification_title += await get_notification_title(context, task_description, task_day, task_month_int,
                                                           task_month,
                                                           task_year, status)
        new_config = RenderConfig(
            chat_id=user_id
        )
        try:
            if len(context.user_data['MEDIA_ADD']) > 1:
                new_notification = CarouselNotificationScreen()
            else:
                new_notification = StaticNotificationScreen()
                new_notification.images = []
            if exists(str(settings.MEDIA_ROOT) + '/' + str(index) + '/'):
                add_images = listdir(str(settings.MEDIA_ROOT) + '/' + str(index) + "/")
                for image in add_images:
                    path = str(index) + "/" + str(image)
                    item = [settings.MEDIA_ROOT / path, notification_title]
                    new_notification.images.append(item)
                if len(context.user_data['MEDIA_ADD']) == 1:
                    new_notification.description = notification_title
                    new_notification.current_images = new_notification.images[0]
                    new_notification.cover = new_notification.current_images[0]
            else:
                new_notification.images = [
                    [settings.MEDIA_ROOT / 'logo.webp', notification_title]
                ]
        except KeyError:
            new_notification = StaticNotificationScreen()
            new_notification.description = notification_title
            new_notification.images = [
                [settings.MEDIA_ROOT / 'logo.webp', ""]
            ]
        new_config.keyboard = [
            [
                Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                       source_type=SourceTypes.JUMP_SOURCE_TYPE)
            ]
        ]
        try:
            await new_notification.send(context, config=new_config, extra_data=None)
        except Forbidden:
            pass
        except BadRequest:
            for x in range(0, len(notification_title), settings.MAX_CAPTION_LENGTH):
                current_description = notification_title[x:x + settings.MAX_CAPTION_LENGTH]
                save_markers = save_html_markers(current_description)
                soup = BeautifulSoup(save_markers, "html.parser")
                soup.prettify()
                current_description = str(soup)
                current_description = load_html_markers(current_description)
                current_description = "<strong>" + current_description + '</strong>'
                if x + settings.MAX_CAPTION_LENGTH >= len(notification_title):
                    new_config.description = current_description
                    return await new_notification.send(context, config=new_config)
                else:
                    await update.effective_chat.send_message(current_description, parse_mode='HTML')
        with suppress(KeyError):
            context.user_data["MEDIA_ADD"].clear()
        if status == 'change':
            return await show_notification_screen(update, context, 'send',
                                                  "✅<strong>Задание успешно изменено!</strong>", [
                                                      [Button('⬅️ В меню редактора', SchoolTaskManagementMain,
                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE)],
                                                      [Button("⬅ Изменить ещё задания", SchoolTaskChangeMain,
                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE)],
                                                      [Button('⬅️ На главный экран', main_menu.MainMenu,
                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE)]])


async def add_task_school(update, context, task_item, task_description, group_number, task_day, task_month,
                          task_year):
    from school_tasker.screens import main_menu
    from school_tasker.screens.school_task_addition import SchoolTaskAddition
    from school_tasker.screens.school_task_management_main import SchoolTaskManagementMain
    cursor.execute('SELECT COUNT(*) FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE item_index = %s',
                   (context.user_data['ADDING_TASK_INDEX'],))
    db_length = cursor.fetchall()
    db_length = get_clean_var(db_length, 'to_int', 0, True)
    if db_length > 0:
        hypertime = get_hypertime(int(task_month), int(task_day), int(task_year))
        cursor.execute(
            'INSERT INTO ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks (item_name, item_index, group_number, '
                                                                       'task_description, task_day, task_month,'
                                                                       'task_year, hypertime)'
                                                                       'VALUES'
                                                                       '(%s,%s,%s,%s,%s,%s,%s,%s)',
            (task_item, context.user_data["ADD_TASK_ITEM_INDEX"], group_number, task_description, task_day,
             task_month, task_year, hypertime,))
        connection.commit()
        with suppress(KeyError):
            if context.user_data["MEDIA_ADD"]:
                makedirs("media/" + context.user_data["ADD_TASK_ITEM_INDEX"])
                for file in context.user_data["MEDIA_ADD"]:
                    filename = context.user_data["ADD_TASK_ITEM_INDEX"] + "/" + str(generate_id())
                    title = "media/"
                    original = title + filename
                    await file.download_to_drive(original + '.jpeg')
                    await convert_to_webp(original + '.jpeg', original + '.webp')
                    remove(original + '.jpeg')
        context.user_data["IS_IN_MEDIA_SCREEN"] = False
        await send_update_notification(update, context, "add", context.user_data["ADD_TASK_ITEM_INDEX"],
                                       False)
        return await show_notification_screen(update, context, 'send', "✅<strong>Задание успешно добавлено!</strong>",
                                              [
                                                  [Button('⬅️ В меню редактора', SchoolTaskManagementMain,
                                                          source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                   ],
                                                  [Button('⬅️ Добавить ещё задание', SchoolTaskAddition,
                                                          source_type=SourceTypes.MOVE_SOURCE_TYPE)],
                                                  [Button('⬅️ На главный экран', main_menu.MainMenu,
                                                          source_type=SourceTypes.MOVE_SOURCE_TYPE)]])
    else:
        return await show_notification_screen(update, context, 'render',
                                              '<strong>Перед добавлением данного задания предмет был удалён!</strong>',
                                              [
                                                  [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                          source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                   ]])


async def convert_to_webp(input_path: str, output_path: str):
    img = Image.open(input_path).convert("RGB")
    img.save(output_path, "webp", quality=80)


async def get_var_from_database(index, need_variable, order: bool, context):
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
            try:
                variable = get_clean_var(variable, "to_string", index, True)
            except TypeError:
                variable = get_clean_var(variable, "to_string", 0, True)
            return str(variable)
    else:
        variable_select = {"item_name": "SELECT item_name FROM " + context.user_data[
            'CURRENT_CLASS_NAME'] + "_Tasks WHERE item_index = %s",
                           "group_number": "SELECT group_number FROM " + context.user_data[
                               'CURRENT_CLASS_NAME'] + "_Tasks WHERE item_index = %s",
                           "task_description": "SELECT task_description FROM " + context.user_data[
                               'CURRENT_CLASS_NAME'] + "_Tasks WHERE item_index = %s",
                           "task_day": "SELECT task_day FROM " + context.user_data[
                               'CURRENT_CLASS_NAME'] + "_Tasks WHERE item_index = %s",
                           "task_month": "SELECT task_month FROM " + context.user_data[
                               'CURRENT_CLASS_NAME'] + "_Tasks WHERE item_index = %s",
                           "task_year": "SELECT task_year FROM " + context.user_data[
                               'CURRENT_CLASS_NAME'] + "_Tasks WHERE item_index = %s"
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
    cursor.execute(
        'SELECT groups_list FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
        (item_name,))
    check_groups = cursor.fetchall()
    check_groups = get_clean_var(check_groups, 'to_string', 0, True)
    if int(check_groups) > 1:
        title += "(" + str(group_number) + "ая группа)"
    title += ": " + str(task_description)
    LOGGER.info(title)


async def once_delete_task(school_tasks_screen, context):
    await logger_alert([], "delete", 0, False, context)
    cursor.execute("DELETE FROM SchoolTasker WHERE item_index = %s", (0,))
    connection.commit()
    connection.rollback()
    school_tasks_screen.description = "<strong>На данный момент список заданий пуст!</strong>"


async def get_multipy_async(index, title, context):
    context.user_data.setdefault('RENDER_LAST_DAY', 0)
    context.user_data.setdefault('RENDER_LAST_MONTH', 0)
    context.user_data.setdefault('RENDER_LAST_YEAR', 0)
    context.user_data.setdefault('RENDER_OPEN_DATE', True)
    task_day = await get_var_from_database(index, "task_day", True, context)
    check_day = int(task_day)
    task_month = await get_var_from_database(index, "task_month", True, context)
    check_month = int(task_month)
    task_year = await get_var_from_database(index, "task_year", True, context)
    check_year = int(task_year)
    task_month_int = int(task_month)
    task_month = recognise_month(task_month)
    if context.user_data['RENDER_LAST_DAY'] == task_day and context.user_data['RENDER_LAST_MONTH'] == task_month and \
            context.user_data['RENDER_LAST_YEAR'] == task_year:
        if context.user_data['RENDER_OPEN_DATE']:
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
    context.user_data['RENDER_LAST_DAY'] = task_day
    context.user_data['RENDER_LAST_MONTH'] = task_month
    context.user_data['RENDER_LAST_YEAR'] = task_year
    item_name = await get_var_from_database(index, "item_name", True, context)
    html_start = "<strong>"
    cursor.execute('SELECT emoji FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
                   (item_name,))
    emoji = cursor.fetchall()
    emoji = get_clean_var(emoji, 'to_string', 0, True)
    cursor.execute(
        'SELECT groups_list FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
        (item_name,))
    groups_check = cursor.fetchone()
    groups_check = get_clean_var(groups_check, 'to_int', 0, True)
    item_name = html_start + str(emoji) + item_name
    if groups_check > 1:
        item_name += " ("
        group_number = await get_var_from_database(index, "group_number", True, context)
        item_name += 'Группа ' + str(group_number) + ')'
    task_description = await get_var_from_database(index, "task_description", True, context)
    task_description = recognise_n_tag(task_description)
    html_end = "</strong>\n\n"
    task_description = item_name + ': ' + task_description + html_end
    current_title = task_time + task_description
    title += current_title
    return title, current_title, check_day, check_month, check_year


async def get_button_title(index, context):
    cursor.execute('SELECT item_name FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks')
    item_name = cursor.fetchall()
    item_name = get_clean_var(item_name, 'to_string', index, True)
    cursor.execute('SELECT emoji FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
                   (item_name,))
    emoji = cursor.fetchall()
    emoji = get_clean_var(emoji, 'to_string', 0, True)
    cursor.execute(
        'SELECT groups_list FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
        (item_name,))
    check = cursor.fetchall()
    check = get_clean_var(check, 'to_string', False, True)
    item_name = str(emoji) + str(item_name)
    if int(check) > 1:
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
    cursor.execute('SELECT emoji FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE item_index = %s',
                   (context.user_data['ADDING_TASK_INDEX'],))
    emoji = cursor.fetchall()
    emoji = get_clean_var(emoji, 'to_string', 0, True)
    cursor.execute(
        'SELECT rod_name FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE item_index = %s',
        (context.user_data['ADDING_TASK_INDEX'],))
    rod_name = cursor.fetchall()
    rod_name = get_clean_var(rod_name, 'to_string', 0, True)
    add_task_txt = emoji + rod_name
    title += add_task_txt
    cursor.execute(
        'SELECT groups_list FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
        (context.user_data['ADDING_TASK_NAME'],))
    check_group = cursor.fetchall()
    check_group = get_clean_var(check_group, 'to_string', 0, True)
    if int(check_group) > 1:
        group_txt = " (Группа " + context.user_data['ADDING_TASK_GROUP_NUMBER'] + ")"
        title += group_txt
    title += ": " + task_description + "</strong>"
    return title


async def check_task_status(context):
    check_db = str(context.user_data['db_check'])
    cursor.execute('SELECT * FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks')
    real_db = cursor.fetchall()
    real_db = get_clean_var(real_db, "to_string", 0, True)
    if check_db != real_db:
        return False
    else:
        return True
