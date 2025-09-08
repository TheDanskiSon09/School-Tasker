from contextlib import suppress
from logging import getLogger
from os import listdir, makedirs, remove
from os.path import exists

from bs4 import BeautifulSoup
from hammett.conf import settings
from hammett.core import Button
from hammett.core.constants import RenderConfig, SourceTypes
from mysql.connector import IntegrityError, connect
from PIL import Image
from telegram.error import BadRequest, Forbidden

from captions import BUTTON_BACK_TO_MENU
from utils import *

connection = connect(
    host=str(settings.DATABASE_HOST),
    user=str(settings.DATABASE_USER),
    password=str(settings.DATABASE_PASSWORD),
    database=str(settings.DATABASE_NAME),
    port=str(settings.DATABASE_PORT),
)

cursor = connection.cursor(buffered=True)

cursor.execute("""
CREATE TABLE IF NOT EXISTS Community (
name VARCHAR(255) UNIQUE,
password VARCHAR(255) UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Users (
send_notification TEXT,
id VARCHAR(255) PRIMARY KEY,
name TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS UserCommunities (
user_id TEXT,
class_name TEXT,
user_role_in_class TEXT
)
""")
LOGGER = getLogger('hammett')


async def _execute_query(query, params=None):
    if params is None:
        params = ()
    cursor.execute(query, params)
    operation = query.strip().split()[0].upper()
    if operation == 'SELECT':
        return cursor.fetchall()
    connection.commit()
    return None


async def get_count_of_class_items(context):
    return await _execute_query(
        'SELECT COUNT(*) FROM ' +
        context.user_data['CURRENT_CLASS_NAME'] +
        '_Items',
    )


async def get_main_name_of_class_item(context):
    return await _execute_query('SELECT main_name FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items')


async def get_emoji_of_class_item(context, main_name):
    return await _execute_query(
        'SELECT emoji FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
        (main_name,))


async def update_item_name_of_task(context):
    await _execute_query('UPDATE ' + context.user_data[
        'CURRENT_CLASS_NAME'] + '_Tasks set item_name = %s WHERE item_index = %s',
                         (context.user_data['task_item'], context.user_data['task_index']))


async def get_rod_name_of_class_item(context, main_name):
    return await _execute_query(
        'SELECT rod_name FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
        (main_name,))


async def get_group_of_class_item(context, main_name):
    return await _execute_query(
        'SELECT groups_list FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
        (main_name,))


async def get_item_index_of_class_item(context, main_name):
    return await _execute_query(
        'SELECT item_index FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
        (main_name,))


async def get_count_of_community():
    return await _execute_query('SELECT COUNT(*) FROM Community')


async def get_name_of_community():
    return await _execute_query('SELECT name FROM Community')


async def get_count_of_classes_with_class_name_and_user_id(context, update):
    return await _execute_query(
        'SELECT COUNT(*) '
        'FROM UserCommunities '
        'WHERE class_name = %s '
        'AND user_id = %s',
        (context.user_data['ENTER_COMMUNITY_NAME'], update.effective_user.id),
    )


async def get_password_of_community_by_name(context):
    return await _execute_query('SELECT password FROM Community WHERE name = %s',
                                (context.user_data['CURRENT_CLASS_NAME'],))


async def get_count_of_user_communities_by_name(context):
    return await _execute_query('SELECT COUNT(*) FROM UserCommunities WHERE class_name = %s',
                                (context.user_data['CURRENT_CLASS_NAME'],))


async def get_count_of_user_communities_by_id(update):
    return await _execute_query('SELECT COUNT(*) FROM UserCommunities WHERE user_id = %s',
                                (update.effective_user.id,))


async def get_count_of_user_communities_where_user_is_host(update):
    return await _execute_query(
        'SELECT COUNT(*) FROM UserCommunities WHERE user_id = %s and user_role_in_class = "HOST"',
        (update.effective_user.id,))


async def get_count_of_user_communities_where_user_is_host_or_admin(update):
    return await _execute_query(
        "SELECT COUNT(*) FROM UserCommunities WHERE user_id = %s AND user_role_in_class IN ('ADMIN', 'HOST')",
        (update.effective_user.id,))


async def get_class_name_of_user_communities_where_user_is_host_or_admin(update):
    return await _execute_query(
        "SELECT class_name FROM UserCommunities WHERE user_id = %s AND user_role_in_class IN ('ADMIN', 'HOST')",
        (update.effective_user.id,))


async def get_count_of_user_communities_by_user_id(update):
    return await _execute_query('SELECT COUNT(*) FROM UserCommunities WHERE user_id = %s', (update.effective_user.id,))


async def get_class_name_of_user_communities_by_user_id(update):
    return await _execute_query('SELECT class_name FROM UserCommunities WHERE user_id = %s',
                                (update.effective_user.id,))


async def get_user_id_from_user_communities_by_class_name_and_user_id(context, update):
    return await _execute_query('SELECT user_id FROM UserCommunities WHERE class_name = %s AND user_id != %s',
                                (context.user_data['CURRENT_CLASS_NAME'], update.effective_user.id))


async def get_name_from_users_by_id(user_id):
    return await _execute_query('SELECT name FROM Users WHERE id = %s', (user_id,))


async def get_role_from_user_community_by_id_and_class_name(context):
    return await _execute_query('SELECT user_role_in_class FROM UserCommunities WHERE user_id = %s AND class_name = %s',
                                (context.user_data['CHANGE_USER_ROLE_ID'],
                                 context.user_data['CURRENT_CLASS_NAME']))


async def get_class_name_from_user_community_by_id(update):
    return await _execute_query('SELECT class_name FROM UserCommunities WHERE user_id = %s',
                                (update.effective_user.id,))


async def get_send_notification_from_users_by_id(user_id):
    return await _execute_query('SELECT send_notification FROM Users WHERE id = %s', (user_id,))


async def update_users_set_send_notification_by_user_id(notification_permission, user):
    await _execute_query('UPDATE Users set send_notification = %s WHERE id = %s', (notification_permission, user.id))


async def get_groups_by_name(context, check_item):
    return await _execute_query(
        'SELECT groups_list FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
        (check_item,))


async def update_class_tasks_set_task_day_by_id(context):
    await _execute_query('UPDATE ' + context.user_data[
        'CURRENT_CLASS_NAME'] + '_Tasks SET task_day = %s WHERE item_index = %s',
                         (context.user_data['ADDING_TASK_TASK_DAY'], context.user_data['ADDING_TASK_INDEX']))
    day = await _execute_query(
        'SELECT task_day FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
        (context.user_data['ADDING_TASK_INDEX'],))
    day = get_clean_var(day, 'to_string', 0, True)
    year = await _execute_query(
        'SELECT task_year FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
        (context.user_data['ADDING_TASK_INDEX'],))
    year = get_clean_var(year, 'to_string', 0, True)
    hypertime = get_hypertime(context.user_data['ADDING_TASK_TASK_MONTH'], int(day), int(year))
    await _execute_query(
        'UPDATE ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks SET hypertime = %s WHERE item_index = %s',
        (hypertime, context.user_data['ADDING_TASK_INDEX'],))


async def update_community_set_name_by_name(new_community_name, context):
    await _execute_query('UPDATE Community SET name = %s WHERE name = %s',
                         (new_community_name, context.user_data['CURRENT_CLASS_NAME']))


async def get_item_name_from_community_task_by_index(context):
    return await _execute_query(
        'SELECT item_name FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
        (context.user_data['ADDING_TASK_INDEX'],))


async def get_item_index_from_community_items_by_index(context, item_name):
    return await _execute_query(
        'SELECT item_index FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
        (item_name,))


async def update_community_task_set_group_number_by_index(context):
    await _execute_query(
        'UPDATE ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks SET group_number = %s WHERE item_index = %s',
        (context.user_data['ADDING_TASK_GROUP_NUMBER'], context.user_data['ADDING_TASK_INDEX']))


async def get_item_name_from_community_tasks_by_index(context, media_index):
    return await _execute_query(
        'SELECT item_name FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
        (media_index,))


async def get_item_index_from_community_items_by_main_name(context, item_name):
    return await _execute_query(
        'SELECT item_index FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
        (item_name,))


async def get_all_from_community_tasks(context):
    return await _execute_query('SELECT * FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks')


async def get_count_from_community_tasks(context):
    return await _execute_query('SELECT COUNT(*) FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks')


async def get_item_index_from_community_tasks(context):
    return await _execute_query('SELECT item_index FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks')


async def update_community_tasks_set_task_month_by_index(context):
    await _execute_query('UPDATE ' + context.user_data[
        'CURRENT_CLASS_NAME'] + '_Tasks SET task_month = %s WHERE item_index = %s',
                         (context.user_data['ADDING_TASK_TASK_MONTH'], context.user_data['ADDING_TASK_INDEX']))
    day = await _execute_query(
        'SELECT task_day FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
        (context.user_data['ADDING_TASK_INDEX'],))
    day = get_clean_var(day, 'to_string', 0, True)
    year = await _execute_query(
        'SELECT task_year FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
        (context.user_data['ADDING_TASK_INDEX'],))
    year = get_clean_var(year, 'to_string', 0, True)
    hypertime = get_hypertime(context.user_data['ADDING_TASK_TASK_MONTH'], int(day), int(year))
    await _execute_query(
        'UPDATE ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks SET hypertime = %s WHERE item_index = %s',
        (hypertime, context.user_data['ADDING_TASK_INDEX'],))


async def get_all_from_community_task(context):
    return await _execute_query('SELECT * FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks')


async def get_count_of_community_tasks(context):
    return await _execute_query('SELECT COUNT(*) FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks')


async def get_item_index_from_community_tasks_order_by(context):
    return await _execute_query('SELECT item_index FROM ' + context.user_data[
        'CURRENT_CLASS_NAME'] + '_Tasks ORDER BY hypertime ASC')


async def get_group_from_community_tasks_by_name(context, media_item_name):
    return await _execute_query('SELECT groups_list FROM ' + context.user_data[
        'CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s', (media_item_name,))


async def get_group_number_from_community_tasks_by_index(context, media_index):
    return await _execute_query('SELECT group_number FROM ' + context.user_data[
        'CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s', (media_index,))


async def get_task_description_from_community_tasks_by_index(context, media_index):
    return await _execute_query('SELECT task_description FROM ' + context.user_data[
        'CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s', (media_index,))


async def delete_task_from_community_tasks_by_index(context, task_id):
    await _execute_query('DELETE FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
                         (task_id,))


async def get_name_from_users_by_index(context):
    return await _execute_query('SELECT name FROM Users WHERE id = %s', (context.user_data['CHANGE_USER_ROLE_ID'],))


async def update_user_communities_set_user_role_by_user_id_and_class_name(new_role, context):
    await _execute_query('UPDATE UserCommunities SET user_role_in_class = %s WHERE user_id = %s AND class_name = %s',
                         (new_role, context.user_data['CHANGE_USER_ROLE_ID'], context.user_data['CURRENT_CLASS_NAME']))


async def add_or_update_user(user_id, user_name, success_outcome, failure_outcome):
    try:
        await _execute_query('INSERT INTO Users (send_notification, id, name) '
                             'VALUES'
                             '(%s,%s,%s)', (1, str(user_id), user_name))
        return success_outcome
    except IntegrityError or AttributeError:
        await _execute_query('UPDATE Users SET name = %s WHERE id = %s', (user_name, user_id))
        return failure_outcome


async def get_count_of_user_communities_by_user_id_where_user_is_host(update):
    return await _execute_query(
        "SELECT COUNT(*) FROM UserCommunities WHERE user_id = %s AND user_role_in_class = 'HOST'",
        (update.effective_user.id,))


async def get_class_name_of_user_communities_by_user_id_where_user_is_host(update):
    return await _execute_query(
        "SELECT class_name FROM UserCommunities WHERE user_id = %s AND user_role_in_class  = 'HOST'",
        (update.effective_user.id,))


async def delete_task(context, formatted_index):
    await _execute_query(
        """DELETE FROM """ + context.user_data['CURRENT_CLASS_NAME'] + """_Tasks WHERE item_index = %s""",
        (formatted_index,))


async def delete_item(context):
    await _execute_query('DELETE FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE item_index = %s',
                         (context.user_data['MANAGE_ITEM_INDEX'],))


async def delete_task_from_deleted_item(context):
    await _execute_query('DELETE FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_name = %s',
                         (context.user_data['MANAGE_ITEM_MAIN_NAME'],))


async def update_user_community_set_class_name_by_class_name(new_community_name, context):
    await _execute_query('UPDATE UserCommunities SET class_name = %s WHERE class_name = %s',
                         (new_community_name, context.user_data['CURRENT_CLASS_NAME']))


async def rename_items_table(context, new_community_name):
    await _execute_query('ALTER TABLE ' + context.user_data[
        'CURRENT_CLASS_NAME'] + '_Items RENAME TO ' + new_community_name + '_Items')


async def rename_tasks_table(context, new_community_name):
    await _execute_query('ALTER TABLE ' + context.user_data[
        'CURRENT_CLASS_NAME'] + '_Tasks RENAME TO ' + new_community_name + '_Tasks')


async def update_task_description(context):
    await _execute_query('UPDATE ' + context.user_data[
        'CURRENT_CLASS_NAME'] + '_Tasks SET task_description = %s WHERE item_index = %s',
                         (context.user_data['ADDING_TASK_TASK_DESCRIPTION'],
                          context.user_data['ADDING_TASK_INDEX']))


async def get_item_name_from_tasks_by_item_index(context):
    return await _execute_query('SELECT item_name FROM ' + context.user_data[
        'CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s', (context.user_data['ADDING_TASK_INDEX'],))


async def get_item_index_from_items_by_main_name(context, item_name):
    return await _execute_query(
        'SELECT item_index FROM ' + context.user_data[
            'CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s', (item_name,))


async def get_group_number_from_tasks_by_item_index(context, item_index):
    return await _execute_query(
        'SELECT group_number FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks '
                                                                                'WHERE item_index = %s',
        (item_index,))


async def update_community_password_by_name(update, context):
    await _execute_query('UPDATE Community set password = %s WHERE name = %s',
                         (update.message.text, context.user_data['CURRENT_CLASS_NAME']))


async def update_items_set_main_name_by_main_name(context, update):
    await _execute_query('UPDATE ' + context.user_data[
        'CURRENT_CLASS_NAME'] + '_Items SET main_name = %s WHERE main_name = %s',
                         (update.message.text, context.user_data['MANAGE_ITEM_MAIN_NAME']))


async def update_tasks_set_item_name_by_item_name(context, update):
    await _execute_query('UPDATE ' + context.user_data[
        'CURRENT_CLASS_NAME'] + '_Tasks SET item_name = %s WHERE item_name = %s',
                         (update.message.text, context.user_data['MANAGE_ITEM_MAIN_NAME']))


async def update_items_set_rod_name_by_item_index(context, update):
    await _execute_query('UPDATE ' + context.user_data[
        'CURRENT_CLASS_NAME'] + '_Items SET rod_name = %s WHERE item_index = %s',
                         (update.message.text, context.user_data['MANAGE_ITEM_INDEX']))


async def update_items_set_groups_list_by_main_name(context, update):
    await _execute_query('UPDATE ' + context.user_data[
        'CURRENT_CLASS_NAME'] + '_Items SET groups_list = %s WHERE main_name = %s',
                         (update.message.text, context.user_data['MANAGE_ITEM_MAIN_NAME'],))


async def update_items_set_emoji_by_main_name(context, update):
    await _execute_query('UPDATE ' + context.user_data[
        'CURRENT_CLASS_NAME'] + '_Items SET emoji = %s WHERE main_name = %s',
                         (context.user_data['CHANGE_ITEM_EMOJI'], context.user_data['MANAGE_ITEM_MAIN_NAME'],))


async def create_new_school_item(context):
    await _execute_query('INSERT INTO ' + context.user_data[
        'CURRENT_CLASS_NAME'] + '_Items (item_index, emoji, main_name, rod_name, groups_list) VALUES (%s, %s, %s, '
                                '%s, %s)', (generate_id(), context.user_data['CREATING_ITEM_EMOJI'],
                                            context.user_data['CREATING_ITEM_NAME'],
                                            context.user_data['CREATING_ITEM_ROD_NAME'],
                                            context.user_data['CREATING_ITEM_GROUPS']))


async def create_community_table(context):
    await _execute_query('INSERT INTO Community (name, password) VALUES (%s,%s)',
                         (context.user_data['CURRENT_CLASS_NAME'],
                          context.user_data['CURRENT_CLASS_PASSWORD']))


async def create_tasks_table(context):
    await _execute_query("""
                CREATE TABLE IF NOT EXISTS """ + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks' + """ (
                item_name TEXT,
                item_index TEXT,
                group_number TEXT,
                task_description TEXT,
                task_day TEXT,
                task_month TEXT,
                task_year TEXT,
                hypertime TEXT
                )
                """)


async def create_items_table(context):
    await _execute_query("""
                                             CREATE TABLE IF NOT EXISTS """ + context.user_data[
        'CURRENT_CLASS_NAME'] + '_Items' + """ (
                                            item_index TEXT,
                                            emoji TEXT,
                                            main_name VARCHAR(255) UNIQUE,
                                            rod_name VARCHAR(255) UNIQUE,
                                            groups_list TEXT
                                            )
                                            """)


async def add_new_community(update, context):
    await _execute_query(
        'INSERT INTO UserCommunities (user_id, class_name, user_role_in_class) VALUES (%s,%s,%s)',
        (update.message.chat.id, context.user_data['CURRENT_CLASS_NAME'], 'HOST'))


async def add_user_to_community(update, context):
    await _execute_query(
        'INSERT INTO UserCommunities (user_id, class_name, user_role_in_class) VALUES (%s,%s,%s)',
        (update.effective_user.id, context.user_data['ENTER_COMMUNITY_NAME'], 'ANONIM',))


async def get_users_to_send_notification(context):
    return await _execute_query(
        'SELECT id FROM Users WHERE send_notification = 1 AND id IN (SELECT user_id FROM UserCommunities WHERE class_name = %s)',
        (context.user_data['CURRENT_CLASS_NAME'],))


async def get_username_by_id(user_id):
    return await _execute_query('SELECT name FROM Users WHERE id = %s', (user_id,))


async def get_community_passwords():
    return await _execute_query('SELECT password FROM Community')


async def show_notification_screen(update, context, translation_type: str, description, keyboard):
    from school_tasker.screens.screen_notification import ScreenNotification
    new_config = RenderConfig()
    new_config.description = description
    new_config.keyboard = keyboard
    if translation_type == 'send':
        return await ScreenNotification().send(context, config=new_config)
    elif translation_type == 'render':
        return await ScreenNotification().render(update, context, config=new_config)


async def send_update_notification(update, context, status, index, is_order: bool, logger_status):
    from school_tasker.screens import main_menu
    from school_tasker.screens.carousel_notification_screen import CarouselNotificationScreen
    from school_tasker.screens.school_task_change_main import SchoolTaskChangeMain
    from school_tasker.screens.school_task_management_main import SchoolTaskManagementMain
    from school_tasker.screens.static_notification_screen import StaticNotificationScreen
    user = update.effective_user
    name = get_username(user.first_name, user.last_name, user.username)
    await logger_alert([name, user.id], logger_status, index, is_order, context)
    task_description = await get_var_from_database(index, 'task_description', is_order, context)
    task_day = await get_var_from_database(index, 'task_day', is_order, context)
    task_month = await get_var_from_database(index, 'task_month', is_order, context)
    task_month_int = int(task_month)
    task_month = recognise_month(task_month)
    task_year = await get_var_from_database(index, 'task_year', is_order, context)
    user_id_list = []
    extracted_id = await get_users_to_send_notification(context)
    for id_row in extracted_id:
        id_row = list(id_row)
        id_row = int(id_row[0])
        user_id_list.append(id_row)
    for user_id in user_id_list:
        new_config = RenderConfig(
            chat_id=user_id,
        )
        notification_screen_class = None
        try:
            if not notification_screen_class:
                if len(context.user_data['MEDIA_ADD']) > 1:
                    notification_screen_class = CarouselNotificationScreen()
                    new_notification = notification_screen_class
                else:
                    notification_screen_class = StaticNotificationScreen()
                    new_notification = notification_screen_class
                    new_notification.images = []
            else:
                new_notification = notification_screen_class
            if exists(str(settings.MEDIA_ROOT) + '/' + str(index) + '/'):
                add_images = listdir(str(settings.MEDIA_ROOT) + '/' + str(index) + '/')
                for image in add_images:
                    user_name = await get_username_by_id(user_id)
                    user_name = get_clean_var(user_name, 'to_string', 0, True)
                    notification_title = '<strong>Здравствуйте, ' + str(user_name) + '!' + '\n'
                    notification_title += await get_notification_title(context, task_description, task_day,
                                                                       task_month_int,
                                                                       task_month,
                                                                       task_year, logger_status)
                    path = str(index) + '/' + str(image)
                    item = [settings.MEDIA_ROOT / path, notification_title]
                    new_notification.images.append(item)
                if len(context.user_data['MEDIA_ADD']) == 1:
                    user_name = await get_username_by_id(user_id)
                    user_name = get_clean_var(user_name, 'to_string', 0, True)
                    notification_title = '<strong>Здравствуйте, ' + str(user_name) + '!' + '\n'
                    notification_title += await get_notification_title(context, task_description, task_day,
                                                                       task_month_int,
                                                                       task_month,
                                                                       task_year, logger_status)
                user_name = await get_username_by_id(user_id)
                user_name = get_clean_var(user_name, 'to_string', 0, True)
                notification_title = '<strong>Здравствуйте, ' + str(user_name) + '!' + '\n'
                notification_title += await get_notification_title(context, task_description, task_day,
                                                                   task_month_int,
                                                                   task_month,
                                                                   task_year, logger_status)
                new_notification.description = notification_title
                new_notification.current_images = new_notification.images[0]
                new_notification.cover = new_notification.current_images[0]
            else:
                user_name = await get_username_by_id(user_id)
                user_name = get_clean_var(user_name, 'to_string', 0, True)
                notification_title = '<strong>Здравствуйте, ' + str(user_name) + '!' + '\n'
                notification_title += await get_notification_title(context, task_description, task_day, task_month_int,
                                                                   task_month,
                                                                   task_year, logger_status)
                new_notification.images = [
                    [settings.MEDIA_ROOT / 'logo.webp', notification_title],
                ]
                new_notification.description = notification_title
        except KeyError:
            user_name = await get_username_by_id(user_id)
            user_name = get_clean_var(user_name, 'to_string', 0, True)
            notification_title = '<strong>Здравствуйте, ' + str(user_name) + '!' + '\n'
            notification_title += await get_notification_title(context, task_description, task_day, task_month_int,
                                                               task_month,
                                                               task_year, logger_status)
            new_notification = StaticNotificationScreen()
            new_notification.description = notification_title
            new_notification.images = [
                [settings.MEDIA_ROOT / 'logo.webp', notification_title],
            ]
        new_config.keyboard = [
            [
                Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                       source_type=SourceTypes.JUMP_SOURCE_TYPE),
            ],
        ]
        try:
            await new_notification.send(context, config=new_config, extra_data=None)
        except Forbidden:
            pass
        except BadRequest:
            for x in range(0, len(notification_title), settings.MAX_CAPTION_LENGTH):
                current_description = notification_title[x:x + settings.MAX_CAPTION_LENGTH]
                save_markers = save_html_markers(current_description)
                soup = BeautifulSoup(save_markers, 'html.parser')
                soup.prettify()
                current_description = str(soup)
                current_description = load_html_markers(current_description)
                current_description = '<strong>' + current_description + '</strong>'
                if x + settings.MAX_CAPTION_LENGTH >= len(notification_title):
                    new_config.description = current_description
                    return await new_notification.send(context, config=new_config)
                else:
                    await update.effective_chat.send_message(current_description, parse_mode='HTML')
        with suppress(KeyError):
            if context.user_data['MEDIA_ADD']:
                context.user_data['MEDIA_ADD'].clear()
        new_notification.cover = settings.MEDIA_ROOT / 'logo.webp'
        new_notification.images = []
        if logger_status == 'change' or status == 'change':
            return await show_notification_screen(update, context, 'send',
                                                  '✅<strong>Задание успешно изменено!</strong>', [
                                                      [Button('⬅️ В меню редактора', SchoolTaskManagementMain,
                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE)],
                                                      [Button('⬅ Изменить ещё задания', SchoolTaskChangeMain,
                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE)],
                                                      [Button('⬅️ На главный экран', main_menu.MainMenu,
                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE)]])


async def add_task_school(update, context, task_item, task_description, group_number, task_day, task_month,
                          task_year):
    from school_tasker.screens import main_menu
    from school_tasker.screens.school_task_addition import SchoolTaskAddition
    from school_tasker.screens.school_task_management_main import SchoolTaskManagementMain
    db_length = await _execute_query(
        'SELECT COUNT(*) FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE item_index = %s',
        (context.user_data['ADDING_TASK_INDEX'],))
    db_length = get_clean_var(db_length, 'to_int', 0, True)
    if db_length > 0:
        hypertime = get_hypertime(int(task_month), int(task_day), int(task_year))
        await _execute_query(
            'INSERT INTO ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks (item_name, item_index, group_number, '
                                                                       'task_description, task_day, task_month,'
                                                                       'task_year, hypertime)'
                                                                       'VALUES'
                                                                       '(%s,%s,%s,%s,%s,%s,%s,%s)',
            (task_item, context.user_data['ADD_TASK_ITEM_INDEX'], group_number, task_description,
             task_day, task_month, task_year, hypertime))
        with suppress(KeyError):
            if context.user_data['MEDIA_ADD']:
                makedirs('media/' + context.user_data['ADD_TASK_ITEM_INDEX'])
                for file in context.user_data['MEDIA_ADD']:
                    filename = context.user_data['ADD_TASK_ITEM_INDEX'] + '/' + str(generate_id())
                    title = 'media/'
                    original = title + filename
                    await file.download_to_drive(original + '.jpeg')
                    await convert_to_webp(original + '.jpeg', original + '.webp')
                    remove(original + '.jpeg')
        context.user_data['IS_IN_MEDIA_SCREEN'] = False
        context.user_data['MEDIA_ADD'] = []
        del context.user_data['ADDING_TASK_TASK_DESCRIPTION']
        await send_update_notification(update, context, 'add', context.user_data['ADD_TASK_ITEM_INDEX'],
                                       False, 'add')
        return await show_notification_screen(update, context, 'send', '✅<strong>Задание успешно добавлено!</strong>',
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
                                                          source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                   ]])


async def convert_to_webp(input_path: str, output_path: str):
    img = Image.open(input_path).convert('RGB')
    img.save(output_path, 'webp', optimize=True, quality=80)


async def get_var_from_database(index, need_variable, order: bool, context):
    if order:
        variable_order = {'item_name': 'SELECT item_name FROM ' + context.user_data[
            'CURRENT_CLASS_NAME'] + '_Tasks ORDER BY hypertime ASC',
                          'group_number': 'SELECT group_number FROM ' + context.user_data[
                              'CURRENT_CLASS_NAME'] + '_Tasks ORDER BY hypertime ASC',
                          'task_description': 'SELECT task_description FROM ' + context.user_data[
                              'CURRENT_CLASS_NAME'] + '_Tasks ORDER BY hypertime ASC',
                          'task_day': 'SELECT task_day FROM ' + context.user_data[
                              'CURRENT_CLASS_NAME'] + '_Tasks ORDER BY hypertime ASC',
                          'task_month': 'SELECT task_month FROM ' + context.user_data[
                              'CURRENT_CLASS_NAME'] + '_Tasks ORDER BY hypertime ASC',
                          'item_index': 'SELECT item_index FROM ' + context.user_data[
                              'CURRENT_CLASS_NAME'] + '_Tasks ORDER BY hypertime ASC',
                          'database_length_SchoolTasker': 'SELECT count(*) FROM ' + context.user_data[
                              'CURRENT_CLASS_NAME'] + '_Tasks',
                          'database_length_Users': 'SELECT count(*) FROM ' + context.user_data[
                              'CURRENT_CLASS_NAME'] + '_Tasks',
                          'task_year': 'SELECT task_year FROM ' + context.user_data[
                              'CURRENT_CLASS_NAME'] + '_Tasks ORDER BY hypertime ASC'}
        title = variable_order[need_variable]
        cursor.execute(title)
        variable = cursor.fetchall()
        if need_variable == 'database_length_SchoolTasker' or need_variable == 'database_length_Users':
            variable = get_clean_var(variable, 'to_int', False, True)
            return int(variable)
        else:
            try:
                variable = get_clean_var(variable, 'to_string', index, True)
            except TypeError:
                variable = get_clean_var(variable, 'to_string', 0, True)
            return str(variable)
    else:
        variable_select = {'item_name': 'SELECT item_name FROM ' + context.user_data[
            'CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
                           'group_number': 'SELECT group_number FROM ' + context.user_data[
                               'CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
                           'task_description': 'SELECT task_description FROM ' + context.user_data[
                               'CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
                           'task_day': 'SELECT task_day FROM ' + context.user_data[
                               'CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
                           'task_month': 'SELECT task_month FROM ' + context.user_data[
                               'CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
                           'task_year': 'SELECT task_year FROM ' + context.user_data[
                               'CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
                           }
        title = variable_select[need_variable]
        cursor.execute(title, (index,))
        variable = cursor.fetchone()
        if need_variable == 'item_name':
            variable = get_clean_var(variable, 'to_string', False, True)
            return str(variable)
        elif need_variable == 'task_description':
            variable = get_clean_var(variable, 'to_string', False, False)
            return str(variable)
        else:
            variable = get_clean_var(variable, 'to_int', False, True)
            return int(variable)


async def logger_alert(user: list, status: str, formattered_index, is_order: bool, context):
    item_name = await get_var_from_database(formattered_index, 'item_name', is_order, context)
    task_description = await get_var_from_database(formattered_index, 'task_description', is_order, context)
    group_number = await get_var_from_database(formattered_index, 'group_number', is_order, context)
    task_day = await get_var_from_database(formattered_index, 'task_day', is_order, context)
    task_month = await get_var_from_database(formattered_index, 'task_month', is_order, context)
    status_dict = {'add': 'added',
                   'delete': 'deleted',
                   'change': 'changed'}
    title = 'The '
    if len(user) < 1:
        title += 'SchoolTasker was '
    else:
        title += 'user ' + str(user[0]) + ' (' + str(user[1]) + ')' + ' was '
    status = status_dict[status]
    status += ' task'
    title += status
    title += ': На ' + str(task_day) + '.' + str(task_month) + ' по ' + str(item_name)
    check_groups = await _execute_query(
        'SELECT groups_list FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
        (item_name,))
    check_groups = get_clean_var(check_groups, 'to_string', 0, True)
    if int(check_groups) > 1:
        title += '(' + str(group_number) + 'ая группа)'
    title += ': ' + str(task_description)
    LOGGER.info(title)


async def once_delete_task(school_tasks_screen, context):
    await logger_alert([], 'delete', 0, False, context)
    await _execute_query('DELETE FROM SchoolTasker WHERE item_index = %s', (0,))
    school_tasks_screen.description = '<strong>На данный момент список заданий пуст!</strong>'


async def get_multipy_async(index, title, context):
    context.user_data.setdefault('RENDER_LAST_DAY', 0)
    context.user_data.setdefault('RENDER_LAST_MONTH', 0)
    context.user_data.setdefault('RENDER_LAST_YEAR', 0)
    context.user_data.setdefault('RENDER_OPEN_DATE', True)
    task_day = await get_var_from_database(index, 'task_day', True, context)
    check_day = int(task_day)
    task_month = await get_var_from_database(index, 'task_month', True, context)
    check_month = int(task_month)
    task_year = await get_var_from_database(index, 'task_year', True, context)
    check_year = int(task_year)
    task_month_int = int(task_month)
    task_month = recognise_month(task_month)
    if context.user_data['RENDER_LAST_DAY'] == task_day and context.user_data['RENDER_LAST_MONTH'] == task_month and \
            context.user_data['RENDER_LAST_YEAR'] == task_year:
        if context.user_data['RENDER_OPEN_DATE']:
            week_day = get_week_day(task_year, task_month_int, int(task_day))
            if int(task_year) == datetime.now().year:
                task_time = ('<strong>На ' + '<em>' + week_day + ', ' + str(task_day) + ' ' + str(
                    task_month) + '</em>'
                             + ' :</strong>' + '\n\n')
            else:
                task_time = ('<strong>На ' + '<em>' + week_day + ', ' + str(task_day) + ' ' + str(
                    task_month) + ' ' + str(task_year) + 'го года' + '</em>'
                             + ' :</strong>' + '\n\n')
        else:
            task_time = ''
    else:
        week_day = get_week_day(task_year, task_month_int, int(task_day))
        if int(task_year) == datetime.now().year:
            task_time = ('<strong>На ' + '<em>' + week_day + ', ' + str(task_day) + ' ' + str(
                task_month) + '</em>'
                         + ' :</strong>' + '\n\n')
        else:
            task_time = ('<strong>На ' + '<em>' + week_day + ', ' + str(task_day) + ' ' + str(
                task_month) + ' ' + str(task_year) + 'го года' + '</em>'
                         + ' :</strong>' + '\n\n')
    context.user_data['RENDER_LAST_DAY'] = task_day
    context.user_data['RENDER_LAST_MONTH'] = task_month
    context.user_data['RENDER_LAST_YEAR'] = task_year
    item_name = await get_var_from_database(index, 'item_name', True, context)
    html_start = '<strong>'
    emoji = await _execute_query(
        'SELECT emoji FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s', (item_name,))
    emoji = get_clean_var(emoji, 'to_string', 0, True)
    groups_check = await _execute_query(
        'SELECT groups_list FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
        (item_name,))
    groups_check = get_clean_var(groups_check, 'to_string', 0, True)
    item_name = html_start + str(emoji) + item_name
    if int(groups_check) > 1:
        item_name += ' ('
        group_number = await get_var_from_database(index, 'group_number', True, context)
        item_name += 'Группа ' + str(group_number) + ')'
    task_description = await get_var_from_database(index, 'task_description', True, context)
    task_description = recognise_n_tag(task_description)
    html_end = '</strong>\n\n'
    task_description = item_name + ': ' + task_description + html_end
    current_title = task_time + task_description
    title += current_title
    return title, current_title, check_day, check_month, check_year


async def get_button_title(index, context):
    item_name = await _execute_query('SELECT item_name FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks ORDER BY hypertime')
    item_name = get_clean_var(item_name, 'to_string', index, True)
    emoji = await _execute_query(
        'SELECT emoji FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s', (item_name,))
    emoji = get_clean_var(emoji, 'to_string', 0, True)
    check = await _execute_query(
        'SELECT groups_list FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
        (item_name,))
    check = get_clean_var(check, 'to_string', False, True)
    reserve_item_name = item_name
    item_name = str(emoji) + str(item_name)
    if int(check) > 1:
        group_number_count = await _execute_query('SELECT COUNT(group_number) FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_name = %s ORDER BY hypertime',
            (reserve_item_name,))
        group_number_count = get_clean_var(group_number_count, 'to_int', 0, True)
        group_number = await _execute_query(
            'SELECT group_number FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_name = %s ORDER BY hypertime',
            (reserve_item_name,))
        if group_number_count > 1:
            group_number = get_clean_var(group_number, 'to_string', index, True)
        else:
            group_number = get_clean_var(group_number, 'to_string', 0, True)
        item_name += ' (Группа ' + str(group_number) + ') '
    task_description_count = await _execute_query('SELECT COUNT(task_description) FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_name = %s ORDER BY hypertime',
        (reserve_item_name,))
    task_description_count = get_clean_var(task_description_count, 'to_int', 0, True)
    task_description = await _execute_query(
        'SELECT task_description FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_name = %s ORDER BY hypertime',
        (reserve_item_name,))
    if task_description_count > 1:
        task_description = get_clean_var(task_description, 'to_string', index, True)
    else:
        task_description = get_clean_var(task_description, 'to_string', 0, True)
    task_description = recognise_n_tag(task_description)
    title = item_name
    title += ' : '
    title += task_description
    return title


async def get_notification_title(context, task_description, task_day, task_month_int, task_month,
                                 task_year, stat):
    status_dict = {'change': 'изменено',
                   'add': 'добавлено'}
    week_day = get_week_day(task_year, task_month_int, int(task_day))
    title = 'В сообществе ' + context.user_data['CURRENT_CLASS_NAME'] + ' на ' + '<em>' + week_day + ', ' + str(
        task_day)
    if str(task_year) == str(datetime.now().year):
        add_month_txt = ' ' + str(task_month) + '</em>'
    else:
        add_month_txt = ' ' + str(task_month) + ' ' + str(task_year) + 'го года' + '</em>'
    title += str(add_month_txt)
    status = status_dict[stat]
    title += ' было ' + status + ' задание по '
    try:
        emoji = await _execute_query(
            'SELECT emoji FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE item_index = %s',
            (context.user_data['ADDING_TASK_INDEX'],))
        emoji = get_clean_var(emoji, 'to_string', 0, True)
        rod_name = await _execute_query(
            'SELECT rod_name FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE item_index = %s',
            (context.user_data['ADDING_TASK_INDEX'],))
    except IndexError:
        task_year = await _execute_query(
            'SELECT task_year FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
            (context.user_data['ADDING_TASK_INDEX'],))
        task_year = get_clean_var(task_year, 'to_string', 0, True)
        task_month_int = await _execute_query(
            'SELECT task_month FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
            (context.user_data['ADDING_TASK_INDEX'],))
        task_month_int = get_clean_var(task_month_int, 'to_string', 0, True)
        task_day = await _execute_query(
            'SELECT task_day FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
            (context.user_data['ADDING_TASK_INDEX'],))
        task_day = get_clean_var(task_day, 'to_string', 0, True)
        week_day = get_week_day(int(task_year), int(task_month_int), int(task_day))
        title = '<strong>В сообществе ' + context.user_data[
            'CURRENT_CLASS_NAME'] + ' на ' + '<em>' + week_day + ', ' + str(
            task_day)
        if str(task_year) == str(datetime.now().year):
            add_month_txt = ' ' + str(task_month) + '</em>'
        else:
            add_month_txt = ' ' + str(task_month) + ' ' + str(task_year) + 'го года' + '</em>'
        title += str(add_month_txt)
        status = status_dict[stat]
        title += ' было ' + status + ' задание по '
        main_name = await _execute_query(
            'SELECT item_name FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
            (context.user_data['ADDING_TASK_INDEX'],))
        main_name = get_clean_var(main_name, 'to_string', 0, True)
        emoji = await _execute_query(
            'SELECT emoji FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
            (main_name,))
        emoji = get_clean_var(emoji, 'to_string', 0, True)
        rod_name = await _execute_query(
            'SELECT rod_name FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
            (main_name,))
    rod_name = get_clean_var(rod_name, 'to_string', 0, True)
    add_task_txt = emoji + rod_name
    title += add_task_txt
    check_group = await _execute_query(
        'SELECT groups_list FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
        (context.user_data['ADDING_TASK_NAME'],))
    check_group = get_clean_var(check_group, 'to_string', 0, True)
    if int(check_group) > 1:
        group_txt = ' (Группа ' + context.user_data['ADDING_TASK_GROUP_NUMBER'] + ')'
        title += group_txt
    title += ': ' + task_description + '</strong>'
    return title


async def check_task_status(context):
    check_db = str(context.user_data['db_check'])
    real_db = await _execute_query('SELECT * FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks')
    real_db = get_clean_var(real_db, 'to_string', 0, True)
    if check_db != real_db:
        return False
    return True
