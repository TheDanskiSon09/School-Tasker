from json import dumps
from os import makedirs, listdir, remove
from shutil import rmtree
from sqlite3 import IntegrityError, OperationalError
from emoji import is_emoji
from telegram.error import Forbidden, BadRequest
from backend import *
from bs4 import BeautifulSoup
from os.path import exists
from constants import *
from contextlib import suppress
from hammett_extensions.carousel import STCarouselWidget
from hammett.core.exceptions import ScreenDescriptionIsEmpty
from hammett.core import Screen, Button
from hammett.core.constants import SourcesTypes, RenderConfig
from hammett.core.handlers import register_button_handler, register_typing_handler
from hammett.core.hiders import ONLY_FOR_ADMIN, Hider
from hammett.core.mixins import StartMixin
from hammett_extensions.handlers import register_input_handler
from settings import ADMIN_GROUP, MEDIA_ROOT, MAX_CAPTION_LENGTH


async def send_update_notification(update, context, status, index, is_order: bool):
    user = update.effective_user
    name = get_username(user.first_name, user.last_name, user.username)
    await logger_alert([name, user.id], status, index, is_order, context)
    task_description = await get_var_from_database(index, "task_description", is_order, context)
    task_day = await get_var_from_database(index, "task_day", is_order, context)
    task_month = await get_var_from_database(index, "task_month", is_order, context)
    task_month_int = int(task_month)
    task_month = recognise_month(task_month)
    task_year = await get_var_from_database(index, "task_year", is_order, context)
    id_result = []
    # for id_row in cursor.execute('SELECT id FROM Users WHERE send_notification = 1 AND user_id != ?,
    # user_id FROM UserCommunities WHERE class_name = ?',
    #                              (user.id, context.user_data['CURRENT_CLASS_NAME'])):
    for id_row in cursor.execute('SELECT id FROM Users WHERE send_notification = 1'):
        id_row = list(id_row)
        id_row = int(id_row[0])
        id_result.append(id_row)
    for user_id in id_result:
        cursor.execute("SELECT name FROM Users WHERE id = ?", (user_id,))
        name = cursor.fetchall()
        name = get_clean_var(name, "to_string", 0, True)
        notification_title = "<strong>Здравствуйте, " + str(name) + "!" + "\n"
        notification_title += await get_notification_title(context, task_description, task_day, task_month_int,
                                                           task_month,
                                                           task_year, status)
        ns_config = RenderConfig(
            chat_id=user_id
        )
        new_notification = NotificationScreen()
        new_notification.images = []
        if exists("media/" + str(index) + '/'):
            add_images = listdir('media/' + str(index) + "/")
            for image in add_images:
                path = str(index) + "/" + str(image)
                item = [MEDIA_ROOT / path, ""]
                new_notification.images.append(item)
        else:
            new_notification.images = [
                [MEDIA_ROOT / 'logo.webp', ""]
            ]
        new_notification.description = notification_title
        with suppress(Forbidden):
            await new_notification.send(context, config=ns_config, extra_data=None)


async def add_task_school(_update, _context, task_item, task_description, group_number, task_day, task_month,
                          task_year):
    cursor.execute('SELECT COUNT(*) FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE item_index = ?',
                   (_context.user_data['ADDING_TASK_INDEX'],))
    db_check = cursor.fetchall()
    db_check = get_clean_var(db_check, 'to_int', 0, True)
    if db_check > 0:
        hypertime = get_hypertime(int(task_month), int(task_day), int(task_year))
        cursor.execute(
            'INSERT INTO ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Tasks (item_name, item_index, group_number, '
                                                                        'task_description, task_day, task_month,'
                                                                        'task_year, hypertime)'
                                                                        'VALUES'
                                                                        '(?,?,?,?,?,?,?,?)',
            (task_item, _context.user_data["ADD_TASK_ITEM_INDEX"], group_number, task_description, task_day,
             task_month, task_year, hypertime,))
        connection.commit()
        with suppress(KeyError):
            if _context.user_data["MEDIA_ADD"]:
                makedirs("media/" + _context.user_data["ADD_TASK_ITEM_INDEX"])
                for file in _context.user_data["MEDIA_ADD"]:
                    filename = _context.user_data["ADD_TASK_ITEM_INDEX"] + "/" + str(generate_id())
                    title = "media/"
                    original = title + filename
                    await file.download_to_drive(original + '.jpeg')
                    await convert_to_webm(original + '.jpeg', original + '.webm')
                    remove(original + '.jpeg')
        with suppress(KeyError):
            _context.user_data["MEDIA_ADD"].clear()
        _context.user_data["IS_IN_MEDIA_SCREEN"] = False
        await send_update_notification(_update, _context, "add", _context.user_data["ADD_TASK_ITEM_INDEX"],
                                       False)
        return await show_notification_screen(_update, _context, 'send', "✅<strong>Задание успешно добавлено!</strong>",
                                              [
                                                  [Button('⬅️ В меню редактора', ManageSchoolTasksMain,
                                                          source_type=SourcesTypes.GOTO_SOURCE_TYPE),
                                                   ],
                                                  [Button('⬅️ Добавить ещё задание', ManageSchoolTasksAdd,
                                                          source_type=SourcesTypes.GOTO_SOURCE_TYPE)],
                                                  [Button('⬅️ На главный экран', MainMenu,
                                                          source_type=SourcesTypes.GOTO_SOURCE_TYPE)]])
    else:
        return await show_notification_screen(_update, _context, 'render',
                                              '<strong>Перед добавлением данного задания предмет был удалён!</strong>',
                                              [
                                                  [Button(BUTTON_BACK_TO_MENU, MainMenu,
                                                          source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                   ]])


class BaseScreen(Screen):
    cache_covers = True
    hide_keyboard = True
    cover = 'media/logo.webp'


class NewsNotificationScreen(BaseScreen):
    pass


class ScreenNotification(BaseScreen):
    pass


async def show_notification_screen(update, context, translation_type: str, description, keyboard):
    new_config = RenderConfig()
    new_config.description = description
    new_config.keyboard = keyboard
    if translation_type == 'send':
        return await ScreenNotification().send(context, config=new_config)
    elif translation_type == 'render':
        return await ScreenNotification().render(update, context, config=new_config)


class MainMenu(StartMixin, BaseScreen):

    async def get_config(self, update, _context, **_kwargs):
        user_id = update.effective_user.id
        config = RenderConfig()
        name = get_username(update.effective_user.first_name, update.effective_user.last_name,
                            update.effective_user.username)
        try:
            cursor.execute(
                'INSERT INTO Users (send_notification, id, name) '
                'VALUES'
                '(?,?,?)',
                (1, user_id, name))
            connection.commit()
            config.description = FIRST_GREET[randint(0, 2)]
        except IntegrityError or AttributeError:
            cursor.execute("UPDATE Users SET name = ? WHERE id = ?", (name, user_id,))
            connection.commit()
            config.description = get_greet(name)
        config.keyboard = []
        cursor.execute('SELECT COUNT(*) FROM UserCommunities WHERE user_id = ?', (update.effective_user.id,))
        db_length = cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            config.keyboard.append([Button('Зайти в задачник📓', self.check_class_name_watch,
                                           source_type=SourcesTypes.HANDLER_SOURCE_TYPE), ])
        cursor.execute(
            "SELECT COUNT(*) FROM UserCommunities WHERE user_id = ? AND user_role_in_class IN ('ADMIN', 'HOST')",
            (update.effective_user.id,))
        db_length = cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            config.keyboard.append([
                Button('Внести изменения в задачник🔧', self.check_class_name_tasks,
                       hiders=Hider(ONLY_FOR_ADMIN),
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)])
        cursor.execute("SELECT COUNT(*) FROM UserCommunities WHERE user_id = ? AND user_role_in_class = 'HOST'",
                       (update.effective_user.id,))
        db_length = cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            config.keyboard.append([
                Button('Внести изменения в сообщество🔪', self.check_class_name_manage,
                       hiders=Hider(ONLY_FOR_ADMIN),
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE),
            ])
        config.keyboard.append([Button('Сообщества👥', CommunitiesMain,
                                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)])
        config.keyboard.append([Button('Настройки⚙', Options,
                                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)])
        config.keyboard.append([Button('Что нового сегодня?✨', WhatsNew,
                                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)])
        config.keyboard.append([Button('Подробнее о School Tasker📋', SocialMedia,
                                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)])
        return config

    @register_button_handler
    async def check_class_name_watch(self, _update, _context):
        cursor.execute("SELECT COUNT(*) FROM UserCommunities WHERE user_id = ?", (_update.effective_user.id,))
        db_length = cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length == 1:
            cursor.execute('SELECT class_name FROM UserCommunities WHERE user_id = ?',
                           (_update.effective_user.id,))
            _context.user_data['CURRENT_CLASS_NAME'] = cursor.fetchall()
            _context.user_data['CURRENT_CLASS_NAME'] = \
                get_clean_var(_context.user_data['CURRENT_CLASS_NAME'], 'to_string', 0, True)
            st_screen = SchoolTasks()
            st_screen.back_button.caption = BUTTON_BACK_TO_MENU
            st_screen.back_button.source = MainMenu
            await st_screen.check_tasks(_update, _context, SchoolTasks)
        elif db_length > 1:
            return await SelectCommunityToWatch().goto(_update, _context)

    @register_button_handler
    async def check_class_name_tasks(self, _update, _context):
        cursor.execute(
            "SELECT COUNT(*) FROM UserCommunities WHERE user_id = ? AND user_role_in_class IN ('ADMIN', 'HOST')",
            (_update.effective_user.id,))
        db_length = cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length == 1:
            cursor.execute(
                "SELECT class_name FROM UserCommunities WHERE user_id = ? AND user_role_in_class IN ('ADMIN', 'HOST')",
                (_update.effective_user.id,))
            _context.user_data['CURRENT_CLASS_NAME'] = cursor.fetchall()
            _context.user_data['CURRENT_CLASS_NAME'] = \
                get_clean_var(_context.user_data['CURRENT_CLASS_NAME'], 'to_string', 0, True)
            return await ManageSchoolTasksMain().goto(_update, _context)
        elif db_length > 1:
            return await SelectCommunityToTasks().goto(_update, _context)

    @register_button_handler
    async def check_class_name_manage(self, _update, _context):
        cursor.execute("SELECT COUNT(*) FROM UserCommunities WHERE user_id = ? AND user_role_in_class == 'HOST'",
                       (_update.effective_user.id,))
        db_length = cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length == 1:
            cursor.execute(
                "SELECT class_name FROM UserCommunities WHERE user_id = ? AND user_role_in_class  == 'HOST'",
                (_update.effective_user.id,))
            _context.user_data['CURRENT_CLASS_NAME'] = cursor.fetchall()
            _context.user_data['CURRENT_CLASS_NAME'] = \
                get_clean_var(_context.user_data['CURRENT_CLASS_NAME'], 'to_string', 0, True)
            return await ManageCommunityMain().goto(_update, _context)
        elif db_length > 1:
            return await SelectCommunityToManage().goto(_update, _context)

    @register_button_handler
    async def school_tasks(self, update, context):
        await SchoolTasks().check_tasks(update, context, SchoolTasks)

    async def start(self, update, context):
        """Replies to the /start command. """
        try:
            user = update.message.from_user
        except AttributeError:
            # When the start handler is invoked through editing
            # the message with the /start command.
            user = update.edited_message.from_user
        user_name = get_username(user.first_name, user.last_name, user.username)
        LOGGER.info('The user %s (%s) was entered to School Tasker', user_name, user.id)
        return await super().start(update, context)


class ChangeCurrentCommunity(BaseScreen):
    description = '<strong>Выберите доступное Вам сообщество: </strong>'

    async def add_default_keyboard(self, _update, _context):
        keyboard = []
        cursor.execute('SELECT class_name FROM UserCommunities WHERE user_id = ?', (_update.effective_user.id,))
        name_list = cursor.fetchall()
        cursor.execute('SELECT COUNT(*) FROM UserCommunities WHERE user_id = ?', (_update.effective_user.id,))
        db_length = cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        for i in range(db_length):
            new_name = get_clean_var(name_list, 'to_string', i - 1, True)
            new_button = [Button(new_name, self.change_class,
                                 source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                                 payload=dumps({"CURRENT_CLASS_NAME": new_name}))]
            keyboard.append(new_button)
        keyboard.append([Button(BUTTON_BACK_TO_MENU, MainMenu,
                                source_type=SourcesTypes.GOTO_SOURCE_TYPE)])
        return keyboard

    @register_button_handler
    async def change_class(self, _update, _context):
        await get_payload_safe(self, _update, _context, "CHANGE_CURRENT_CLASS_NAME", 'CURRENT_CLASS_NAME')
        return await MainMenu().goto(_update, _context)


class SelectCommunityToWatch(BaseScreen):

    async def get_description(self, _update, _context):
        cursor.execute('SELECT COUNT(*) FROM UserCommunities WHERE user_id = ?', (_update.effective_user.id,))
        db_length = cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            return '<strong>Выберите одно из предоставленных сообществ: </strong>'
        else:
            return ('<strong>На данный момент Вы не состоите в каком-нибудь сообществе, чтобы посмотреть домашнее'
                    ' задание</strong>')

    async def add_default_keyboard(self, _update, _context):
        keyboard = []
        cursor.execute('SELECT class_name FROM UserCommunities WHERE user_id = ?', (_update.effective_user.id,))
        name_list = cursor.fetchall()
        cursor.execute('SELECT COUNT(*) FROM UserCommunities WHERE user_id = ?', (_update.effective_user.id,))
        db_length = cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            for i in range(db_length):
                new_name = get_clean_var(name_list, 'to_string', i - 1, True)
                new_button = [Button(new_name, self.press_button,
                                     source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                                     payload=dumps({"CURRENT_CLASS_NAME": new_name}))]
                keyboard.append(new_button)
        keyboard.append([Button(BUTTON_BACK_TO_MENU, MainMenu,
                                source_type=SourcesTypes.GOTO_SOURCE_TYPE)])
        return keyboard

    @register_button_handler
    async def press_button(self, _update, _context):
        await get_payload_safe(self, _update, _context, 'SHOW_TASKS_FOR_CURRENT_CLASS_NAME', 'CURRENT_CLASS_NAME')
        st_screen = SchoolTasks()
        st_screen.back_button.caption = BUTTON_BACK
        st_screen.back_button.source = SelectCommunityToWatch
        await st_screen.check_tasks(_update, _context, SchoolTasks)


class SelectCommunityToTasks(BaseScreen):
    async def get_description(self, _update, _context):
        cursor.execute(
            "SELECT COUNT(*) FROM UserCommunities WHERE user_id = ? AND user_role_in_class IN ('ADMIN', 'HOST')",
            (_update.effective_user.id,))
        db_length = cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            return '<strong>Выберите одно из предоставленных сообществ: </strong>'
        else:
            return ('<strong>На данный момент Вы не состоите в каком-нибудь сообществе, чтобы посмотреть домашнее'
                    ' задание</strong>')

    async def add_default_keyboard(self, _update, _context):
        keyboard = []
        cursor.execute(
            'SELECT class_name FROM UserCommunities WHERE user_id = ? AND user_role_in_class IN ("ADMIN", "HOST")',
            (_update.effective_user.id,))
        name_list = cursor.fetchall()
        cursor.execute(
            'SELECT COUNT(*) FROM UserCommunities WHERE user_id = ? AND user_role_in_class IN ("ADMIN", "HOST")',
            (_update.effective_user.id,))
        db_length = cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            for i in range(db_length):
                new_name = get_clean_var(name_list, 'to_string', i - 1, True)
                new_button = [Button(new_name, self.press_button,
                                     source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                                     payload=dumps({"CURRENT_CLASS_NAME": new_name}))]
                keyboard.append(new_button)
        keyboard.append([Button(BUTTON_BACK_TO_MENU, MainMenu,
                                source_type=SourcesTypes.GOTO_SOURCE_TYPE)])
        return keyboard

    @register_button_handler
    async def press_button(self, _update, _context):
        await get_payload_safe(self, _update, _context, 'MANAGE_TASKS_FOR_CURRENT_CLASS_NAME', 'CURRENT_CLASS_NAME')
        return await ManageSchoolTasksMain().goto(_update, _context)


class SelectCommunityToManage(BaseScreen):
    async def get_description(self, _update, _context):
        cursor.execute("SELECT COUNT(*) FROM UserCommunities WHERE user_id = ? AND user_role_in_class == 'HOST'",
                       (_update.effective_user.id,))
        db_length = cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            return '<strong>Выберите одно из предоставленных сообществ: </strong>'
        else:
            return ('<strong>На данный момент Вы не состоите в каком-нибудь сообществе, чтобы посмотреть домашнее'
                    ' задание</strong>')

    async def add_default_keyboard(self, _update, _context):
        keyboard = []
        cursor.execute("SELECT COUNT(*) FROM UserCommunities WHERE user_id = ? AND user_role_in_class == 'HOST'",
                       (_update.effective_user.id,))
        db_length = cursor.fetchall()
        cursor.execute("SELECT class_name FROM UserCommunities WHERE user_id = ? AND user_role_in_class == 'HOST'",
                       (_update.effective_user.id,))
        name_list = cursor.fetchall()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            for i in range(db_length):
                new_name = get_clean_var(name_list, 'to_string', i - 1, True)
                new_button = [Button(new_name, self.press_button,
                                     source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                                     payload=dumps({"CURRENT_CLASS_NAME": new_name}))]
                keyboard.append(new_button)
        keyboard.append([Button(BUTTON_BACK_TO_MENU, MainMenu,
                                source_type=SourcesTypes.GOTO_SOURCE_TYPE)])
        return keyboard

    @register_button_handler
    async def press_button(self, _update, _context):
        await get_payload_safe(self, _update, _context, 'MANAGE_CLASS_FOR_CURRENT_CLASS_NAME', 'CURRENT_CLASS_NAME')
        return await ManageCommunityMain().goto(_update, _context)


class ManageCommunityMain(BaseScreen):

    async def get_description(self, _update, _context):
        cursor.execute('SELECT password FROM Community WHERE name = ?', (_context.user_data['CURRENT_CLASS_NAME'],))
        _context.user_data['CURRENT_CLASS_PASSWORD'] = cursor.fetchall()
        _context.user_data['CURRENT_CLASS_PASSWORD'] = \
            get_clean_var(_context.user_data['CURRENT_CLASS_PASSWORD'], 'to_string', 0, True)
        return '<strong>Название сообщества: ' + _context.user_data['CURRENT_CLASS_NAME'] + (
                '\nПароль: ' + _context.user_data['CURRENT_CLASS_PASSWORD'] + '</strong>')

    async def add_default_keyboard(self, _update, _context):
        keyboard = [
            [
                Button('Изменить название сообщества', self.change_community_name,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button('Изменить пароль', self.change_community_password,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button('Добавить/удалить предметы', ManageCommunityItems,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]
        cursor.execute('SELECT COUNT(*) FROM UserCommunities WHERE class_name = ?',
                       (_context.user_data['CURRENT_CLASS_NAME'],))
        db_length = cursor.fetchall()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 1:
            keyboard.append([
                Button('Изменить права пользователей сообщества', ManageCommunityChangeUser,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ])
        keyboard.append([
            Button(BUTTON_BACK, self.go_back,
                   source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
        ])
        return keyboard

    @register_button_handler
    async def change_community_name(self, _update, _context):
        Global.is_changing_class_name = True
        return await ManageCommunityChangeName().goto(_update, _context)

    @register_button_handler
    async def change_community_password(self, _update, _context):
        Global.is_changing_class_password = True
        return await ManageCommunityChangePassword().goto(_update, _context)

    @register_button_handler
    async def go_back(self, _update, _context):
        cursor.execute('SELECT COUNT(*) FROM UserCommunities WHERE user_id = ? and user_role_in_class == "HOST"',
                       (_update.effective_user.id,))
        db_length = cursor.fetchall()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 1:
            return await SelectCommunityToManage().goto(_update, _context)
        else:
            return await MainMenu().goto(_update, _context)


class ManageCommunityChangeName(BaseScreen):
    description = '<strong>Введите новое название для сообщества</strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, _update, _context):
        Global.is_changing_class_name = False
        return await ManageCommunityMain().goto(_update, _context)


class ManageCommunityChangePassword(BaseScreen):
    description = '<strong>Введите новый пароль для сообщества: </strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, _update, _context):
        Global.is_changing_class_password = False
        return await ManageCommunityMain().goto(_update, _context)


class ManageCommunityChangeUser(BaseScreen):
    description = 'change user'


class CommunitiesMain(BaseScreen):
    description = '<strong>Какое действие Вы хотите выполнить?</strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button('Создать своё сообщество➕', self.go_create_community,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button('Зайти в существующее сообщество😎', JoinCommunity,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ],
            [
                Button(BUTTON_BACK, MainMenu,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_create_community(self, _update, _context):
        Global.is_creating_class = True
        return await CreateCommunityName().goto(_update, _context)

    @register_button_handler
    async def join_class(self, _update, _context):
        print('aboba2')


class ManageCommunityItems(BaseScreen):

    async def get_description(self, _update, _context):
        cursor.execute('SELECT COUNT(*) FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + "_Items")
        db_length = cursor.fetchall()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            return '<strong>Выберите действие: </strong>'
        else:
            return '<strong>В сообществе пока нету предметов!</strong>'

    async def add_default_keyboard(self, _update, _context):
        keyboard = []
        cursor.execute('SELECT COUNT(*) FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + "_Items")
        db_length = cursor.fetchall()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            cursor.execute('SELECT main_name FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items')
            main_name_list = cursor.fetchall()
            cursor.execute('SELECT emoji FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items')
            emoji_list = cursor.fetchall()
            cursor.execute('SELECT rod_name FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items')
            rod_name_list = cursor.fetchall()
            cursor.execute('SELECT groups FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items')
            groups_list = cursor.fetchall()
            cursor.execute('SELECT item_index FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items')
            index_list = cursor.fetchall()
            for i in range(db_length):
                main_name = get_clean_var(main_name_list, 'to_string', i - 1, True)
                emoji = get_clean_var(emoji_list, 'to_string', i - 1, True)
                rod_name = get_clean_var(rod_name_list, 'to_string', i - 1, True)
                groups = get_clean_var(groups_list, 'to_string', i - 1, True)
                index = get_clean_var(index_list, 'to_string', i - 1, True)
                keyboard.append(
                    [Button(emoji + main_name, self.manage_item, source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                            payload=dumps({'MANAGE_ITEM_INDEX': index,
                                           "MANAGE_ITEM_MAIN_NAME": main_name,
                                           'MANAGE_ITEM_ROD_NAME': rod_name,
                                           'MANAGE_ITEM_GROUPS': groups}))])
        keyboard.append([Button(BUTTON_CREATE_ITEM, self.go_create_item,
                                source_type=SourcesTypes.HANDLER_SOURCE_TYPE)])
        keyboard.append([Button(BUTTON_BACK, ManageCommunityMain,
                                source_type=SourcesTypes.GOTO_SOURCE_TYPE)])
        return keyboard

    @register_button_handler
    async def go_create_item(self, _update, _context):
        Global.is_creating_item_name = True
        return await ManageCommunityItemsAddName().goto(_update, _context)

    @register_button_handler
    async def manage_item(self, _update, _context):
        await get_payload_safe(self, _update, _context, 'MANAGE_ITEM', "MANAGE_ITEM_INDEX")
        await get_payload_safe(self, _update, _context, 'MANAGE_ITEM', "MANAGE_ITEM_MAIN_NAME")
        await get_payload_safe(self, _update, _context, 'MANAGE_ITEM', "MANAGE_ITEM_ROD_NAME")
        await get_payload_safe(self, _update, _context, 'MANAGE_ITEM', "MANAGE_ITEM_GROUPS")
        return await ManageSchoolItem().goto(_update, _context)


class ManageSchoolItem(BaseScreen):
    description = '<strong>Что Вы хотите сделать с данным предметом?</strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button('Изменить название предмета', self.change_name,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button('Изменить название предмета в дательном падеже', self.change_rod_name,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button('Изменить количество групп предмета', self.change_group_number,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button('Изменить эмодзи предмета', self.change_emoji,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button('Удалить предмет', ConfirmDeletionSchoolItem,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ],
            [
                Button(BUTTON_BACK, ManageCommunityItems,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def change_name(self, _update, _context):
        Global.is_changing_item_name = True
        return await ManageSchoolItemChangeName().goto(_update, _context)

    @register_button_handler
    async def change_rod_name(self, _update, _context):
        Global.is_changing_item_rod_name = True
        return await ManageSchoolItemChangeRodName().goto(_update, _context)

    @register_button_handler
    async def change_group_number(self, _update, _context):
        Global.is_changing_group_number = True
        return await ManageSchoolItemChangeGroups().goto(_update, _context)

    @register_button_handler
    async def change_emoji(self, _update, _context):
        Global.is_changing_item_emoji = True
        return await ManageSchoolItemChangeEmoji().goto(_update, _context)


class ConfirmDeletionSchoolItem(BaseScreen):
    description = '<strong>Вы точно уверены, что хотите удалить данный предмет?</strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button('Удалить🗑️', self.delete_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button(BUTTON_BACK, ManageSchoolItem,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def delete_item(self, _update, _context):
        cursor.execute('DELETE FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE item_index = ?',
                       (_context.user_data['MANAGE_ITEM_INDEX'],))
        cursor.execute('DELETE FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_name = ?',
                       (_context.user_data['MANAGE_ITEM_MAIN_NAME'],))
        connection.commit()
        return await show_notification_screen(_update, _context, 'send', '<strong>Предмет был успешно удалён!</strong>',
                                              [
                                                  [Button('Вернуться в панель', ManageCommunityItems,
                                                          source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                   ],
                                                  [Button(BUTTON_BACK_TO_MENU, MainMenu,
                                                          source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                   ]])


class ManageSchoolItemChangeName(BaseScreen):
    description = '<strong>Введите новое название предмета: </strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, _update, _context):
        Global.is_changing_item_name = False
        return await ManageSchoolItem().goto(_update, _context)


class ManageSchoolItemChangeRodName(BaseScreen):
    description = '<strong>Введите новое название предмета в дательном падеже: </strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, _update, _context):
        Global.is_changing_item_rod_name = False
        return await ManageSchoolItem().goto(_update, _context)


class ManageSchoolItemChangeGroups(BaseScreen):
    description = '<strong>Введите новое количество групп: </strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, _update, _context):
        Global.is_changing_item_groups = False
        return await ManageSchoolItem().goto(_update, _context)


class ManageSchoolItemChangeEmoji(BaseScreen):
    description = '<strong>Введите новый эмодзи, ассоциирующийся с предметом: </strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, _update, _context):
        Global.is_changing_item_emoji = False
        return await ManageSchoolItem().goto(_update, _context)


class ManageCommunityItemsAddEmoji(BaseScreen):
    description = '<strong>Введите эмоджи, ассоциирующийся с предметом: </strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, _update, _context):
        Global.is_creating_item_emoji = False
        Global.is_creating_item_group = True
        return await ManageCommunityItemsAddGroup().goto(_update, _context)


class ManageCommunityItemsAddName(BaseScreen):
    description = '<strong>Введите название предмета: </strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, _update, _context):
        Global.is_creating_item_name = False
        return await ManageCommunityItems().goto(_update, _context)


class ManageCommunityItemsAddRodName(BaseScreen):
    description = '<strong>Введите название предмета в дательном падеже: </strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, _update, _context):
        Global.is_creating_item_rod_name = False
        Global.is_creating_item_name = True
        return await ManageCommunityItemsAddName().goto(_update, _context)


class ManageCommunityItemsAddGroup(BaseScreen):
    description = '<strong>Введите количество групп данного предмета</strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, _update, _context):
        Global.is_creating_item_group = False
        Global.is_creating_item_rod_name = True
        return await ManageCommunityItemsAddRodName().goto(_update, _context)


class CreateCommunityName(BaseScreen):
    description = '<strong>Введите название Вашего сообщества: </strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, _update, _context):
        Global.is_creating_class = False
        return await CommunitiesMain().goto(_update, _context)


class CreateCommunityPassword(BaseScreen):
    description = '<strong>Введите пароль Вашего сообщества: </strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, _update, _context):
        Global.is_adding_password_to_class = False
        Global.is_creating_class = True
        return await CreateCommunityName().goto(_update, _context)


class JoinCommunity(BaseScreen):
    description = '<strong>Выберите к какому сообществу Вы хотите присоединиться: </strong>'


class NotificationScreen(BaseScreen, STCarouselWidget):
    callback_button_type = "main_menu"
    callback_button_screen = MainMenu
    hide_keyboard = False


class SocialMedia(BaseScreen):
    description = '<strong>Подробнее о School Tasker Вы можете найти здесь:</strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button('Наш новостной журнал📰', 'https://t.me/SchoolTaskerNews',
                       source_type=SourcesTypes.URL_SOURCE_TYPE)
            ],
            [
                Button('Наш новостной журнал в ВК📰', 'https://vk.ru/schooltasker',
                       source_type=SourcesTypes.URL_SOURCE_TYPE)
            ],
            [
                Button('Связаться с разработчиком📞', 'https://t.me/TheDanskiSon09',
                       source_type=SourcesTypes.URL_SOURCE_TYPE)
            ],
            [
                Button('Репозиторий бота в Github🤖', 'https://github.com/TheDanskiSon09/School-Tasker',
                       source_type=SourcesTypes.URL_SOURCE_TYPE)
            ],
            [
                Button(BUTTON_BACK_TO_MENU, MainMenu,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]


class WhatsNew(BaseScreen):
    description = "_"

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button(BUTTON_BACK_TO_MENU, MainMenu, source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]

    async def get_description(self, _update, _context):
        current_day = datetime.now().day
        current_month = datetime.now().month
        try:
            title = str()
            title += "<strong>"
            month_dict = {1: MONTH_JAN,
                          2: MONTH_FEB,
                          3: MONTH_MARCH,
                          4: MONTH_APRIL,
                          5: MONTH_MAY,
                          6: MONTH_JUNE,
                          7: MONTH_JULY,
                          8: MONTH_AUG,
                          9: MONTH_SEP,
                          10: MONTH_OCT,
                          11: MONTH_NOV,
                          12: MONTH_DEC}
            month = month_dict[current_month]
            title += str(month[current_day])
            title += "</strong>"
            return title
        except KeyError:
            return "<strong>Сегодня никаких праздников и мероприятий</strong>"


class Options(BaseScreen):
    description = '<strong>Выберите подходящие для Вас параметры</strong>'

    async def add_default_keyboard(self, _update, _context):
        user = _update.effective_user
        notification_button_title = str()
        cursor.execute("SELECT send_notification FROM Users WHERE id = ?", (user.id,))
        notification_permission = cursor.fetchone()
        notification_permission = get_clean_var(notification_permission, "to_int", False, True)
        if notification_permission == 0:
            notification_button_title = "Включить "
        if notification_permission == 1:
            notification_button_title = "Выключить "
        notification_button_title += "рассылки от бота"
        return [
            [
                Button(notification_button_title, self.edit_notification_permission,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"index": notification_permission}))
            ],
            [
                Button(BUTTON_BACK_TO_MENU, MainMenu,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def edit_notification_permission(self, _update, _context):
        await get_payload_safe(self, _update, _context, "options", "index")
        notification_permission = _context.user_data['index']
        if notification_permission == 1:
            notification_permission = 0
        else:
            notification_permission = 1
        user = _update.effective_user
        cursor.execute(
            'UPDATE Users set send_notification = ? WHERE id = ?', (notification_permission, user.id))
        connection.commit()
        return await self.goto(_update, _context)


class SchoolTasks(BaseScreen):
    back_button = Button('_', SelectCommunityToWatch, source_type=SourcesTypes.GOTO_SOURCE_TYPE)

    async def check_tasks(self, update, context, target_screen):
        new_config = RenderConfig()
        new_config.keyboard = []
        Global.index_store = await get_var_from_database(None, "database_length_SchoolTasker", True, context)
        database_length = Global.index_store
        title = str()
        if database_length < 1:
            if target_screen:
                target_screen.description = "<strong>На данный момент список заданий пуст!</strong>"
                new_config.keyboard = [[self.back_button]]
                return await target_screen().render(update, context, config=new_config)
        else:
            Global.open_date = True
            new_title = str()
            tasks_to_delete = []
            for i in range(database_length):
                title, current_title, check_day, check_month, check_year = await get_multipy_async(i, title, context)
                if check_year == datetime.now().year:
                    if check_month == datetime.now().month:
                        if check_day <= datetime.now().day:
                            title = ""
                            cursor.execute("SELECT item_index FROM " + context.user_data[
                                'CURRENT_CLASS_NAME'] + "_Tasks ORDER BY hypertime ASC")
                            del_index = cursor.fetchall()
                            del_index = get_clean_var(del_index, "to_string", i, True)
                            if del_index not in tasks_to_delete:
                                tasks_to_delete.append(del_index)
                    if check_month < datetime.now().month:
                        title = ""
                        cursor.execute("SELECT item_index FROM " + context.user_data[
                            'CURRENT_CLASS_NAME'] + "_Tasks ORDER BY hypertime ASC")
                        del_index = cursor.fetchall()
                        del_index = get_clean_var(del_index, "to_string", i, True)
                        if del_index not in tasks_to_delete:
                            tasks_to_delete.append(del_index)
                if check_year < datetime.now().year:
                    title = ""
                    cursor.execute("SELECT item_index FROM " + context.user_data[
                        'CURRENT_CLASS_NAME'] + "_Tasks ORDER BY hypertime ASC")
                    del_index = cursor.fetchall()
                    del_index = get_clean_var(del_index, "to_string", i, True)
                    if del_index not in tasks_to_delete:
                        tasks_to_delete.append(del_index)
                else:
                    new_title = title
                    Global.open_date = False
                    cursor.execute("SELECT item_index FROM " + context.user_data[
                        'CURRENT_CLASS_NAME'] + "_Tasks ORDER BY hypertime ASC")
                    media_index = cursor.fetchall()
                    media_index = get_clean_var(media_index, "to_string", i, True)
                    if exists(str(MEDIA_ROOT) + "/" + media_index) and media_index not in tasks_to_delete:
                        media_button_title = str()
                        cursor.execute('SELECT item_name FROM ' + context.user_data[
                            'CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = ?', (media_index,))
                        media_item_name = cursor.fetchone()
                        media_item_name = get_clean_var(media_item_name, 'to_string', False, True)
                        media_button_title += "🖼" + media_item_name
                        if media_item_name == "Английский язык" or media_item_name == "Информатика":
                            cursor.execute('SELECT group_number FROM ' + context.user_data[
                                'CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = ?',
                                           (media_index,))
                            media_group_number = cursor.fetchone()
                            media_group_number = get_clean_var(media_group_number, 'to_string', False,
                                                               True)
                            media_button_title += '(' + media_group_number + "ая группа)"
                        media_button_title += ': '
                        cursor.execute('SELECT task_description FROM ' + context.user_data[
                            'CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = ?',
                                       (media_index,))
                        media_task_description = cursor.fetchone()
                        media_task_description = get_clean_var(media_task_description, 'to_string',
                                                               False, False)
                        media_button_title += media_task_description
                        new_config.keyboard.append([Button(media_button_title, self._goto_task_media,
                                                           source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                                                           payload=dumps({"MEDIA_INDEX_GOTO": media_index,
                                                                          'MEDIA_TITLE': current_title}))])
                if not new_title:
                    if target_screen:
                        target_screen.description = "<strong>На данный момент список заданий пуст!</strong>"
                else:
                    if target_screen:
                        target_screen.description = new_title
            for task_id in tasks_to_delete:
                await logger_alert([], "delete", task_id, False, context)
                cursor.execute('DELETE FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = ?',
                               (task_id,))
                connection.commit()
                if exists(str(MEDIA_ROOT) + '/' + task_id + '/'):
                    rmtree(str(MEDIA_ROOT) + '/' + task_id)
            else:
                if target_screen:
                    target_screen.description = new_title
            if database_length < 1:
                if target_screen:
                    target_screen.description = "<strong>На данный момент список заданий пуст!</strong>"
            if target_screen:
                new_config.keyboard.append([self.back_button])
                try:
                    return await target_screen().render(update, context, config=new_config)
                except ScreenDescriptionIsEmpty:
                    bad_config = RenderConfig()
                    bad_config.description = '<strong>На данный момент список заданий пуст!</strong>'
                    bad_config.keyboard = [[self.back_button]]
                    return await target_screen().render(update, context, config=bad_config)
                except BadRequest:
                    for x in range(0, len(target_screen.description), MAX_CAPTION_LENGTH):
                        current_description = target_screen.description[x:x + MAX_CAPTION_LENGTH]
                        save_markers = save_html_markers(current_description)
                        soup = BeautifulSoup(save_markers, "html.parser")
                        soup.prettify()
                        current_description = str(soup)
                        current_description = load_html_markers(current_description)
                        current_description = "<strong>" + current_description + '</strong>'
                        if x + MAX_CAPTION_LENGTH >= len(target_screen.description):
                            new_config.description = current_description
                            return await target_screen().send(context, config=new_config)
                        else:
                            await update.effective_chat.send_message(current_description, parse_mode='HTML')

    @register_button_handler
    async def _goto_task_media(self, update, context):
        await get_payload_safe(self, update, context, "task_media_index", 'MEDIA_INDEX_GOTO')
        await get_payload_safe(self, update, context, "task_media_index", 'MEDIA_TITLE')
        try:
            show_images = listdir('media/' + context.user_data['MEDIA_INDEX_GOTO'] + "/")
            TaskMedia.images = []
            for image in show_images:
                path = context.user_data['MEDIA_INDEX_GOTO'] + '/' + image
                item = [MEDIA_ROOT / path, context.user_data['MEDIA_TITLE']]
                TaskMedia.images.append(item)
            return await TaskMedia().goto(update, context)
        except FileNotFoundError:
            await SchoolTasks().check_tasks(update, context, SchoolTasks)


class TaskMedia(BaseScreen, STCarouselWidget):
    images = [
        [MEDIA_ROOT / "logo.webp", "_"]
    ]
    callback_button_type = 'school_tasks'
    callback_button_screen = SchoolTasks
    button_title = "⬅На главный экран"


class AlertAddingOldTask(BaseScreen):
    description = ("<strong>⚠Внимание!\nВы ввели дату и месяц задания, которые уже считаются устаревшими!"
                   " Если Вы добавите задание с данными характеристиками, оно будет удалено при"
                   " первом заходе в задачник!"
                   "\nВы точно хотите добавить данное задание?</strong>")
    task_args = list()
    task_context = str()
    current_index = int()

    async def get_description(self, _update, _context):
        if self.task_context == "add":
            word00 = "добавите "
            word01 = "добавить "
        elif self.task_context == "change":
            word00 = "измените "
            word01 = "изменить "
        else:
            word00 = ""
            word01 = ""
        part00 = "<strong>⚠Внимание!\nВы ввели дату и месяц задания, которые уже считаются устаревшими."
        part01 = " Если Вы " + word00 + ('задание с данными характеристиками, оно будет удалено при первом заходе в'
                                         ' задачник!')
        part02 = "\nВы точно хотите " + word01 + "данное задание?</strong>"
        return part00 + part01 + part02

    async def add_default_keyboard(self, _update, _context):
        keyboard = []
        if self.task_context == "add":
            keyboard.append([
                Button("Добавить данное задание➕", self.add_old_task, source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ])
        elif self.task_context == "change":
            keyboard.append([
                Button("Изменить данное задание✖", self.change_task, source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ])
        keyboard.append([
            Button("⬅️ Изменить дату/месяц задания", self.change_task_time,
                   source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
        ])
        keyboard.append([
            Button("⬅️ В меню редактора", ManageSchoolTasksMain, source_type=SourcesTypes.GOTO_SOURCE_TYPE)
        ])
        return keyboard

    @register_button_handler
    async def change_task_time(self, _update, _context):
        await ManageSchoolTasksAddDetails().set_stage(_update, _context, 1)
        return await ManageSchoolTasksAddDetails().goto(_update, _context)

    @register_button_handler
    async def add_old_task(self, _update, _context):
        await ManageSchoolTasksAddDetails().set_stage(_update, _context, 0)
        _context.user_data["ADD_TASK_ITEM_INDEX"] = str(generate_id())
        await add_task_school(_update, _context, self.task_args[0], self.task_args[1], self.task_args[2],
                              self.task_args[3], self.task_args[4], self.task_args[5])

    @register_button_handler
    async def change_task(self, _update, _context):
        self.task_args[5] = datetime.now().year
        cursor.execute('UPDATE SchoolTasker set task_day = ?, task_month = ?, task_year = ? WHERE item_index = ?',
                       (self.task_args[3], self.task_args[4], self.task_args[5], self.current_index,))
        connection.commit()
        hypertime = get_hypertime(self.task_args[4], self.task_args[3], self.task_args[5])
        cursor.execute("UPDATE SchoolTasker set hypertime = ? WHERE item_index = ?",
                       (hypertime, self.current_index,))
        connection.commit()
        await send_update_notification(_update, _context, "change", self.current_index, False)
        return await show_notification_screen(_update, _context, 'send', "✅<strong>Задание успешно изменено!</strong>",
                                              [
                                                  [Button('⬅️ В меню редактора', ManageSchoolTasksMain,
                                                          source_type=SourcesTypes.GOTO_SOURCE_TYPE)],
                                                  [Button("⬅ Изменить ещё задания", ManageSchoolTasksChangeMain,
                                                          source_type=SourcesTypes.GOTO_SOURCE_TYPE)],
                                                  [Button('⬅️ На главный экран', MainMenu,
                                                          source_type=SourcesTypes.GOTO_SOURCE_TYPE)]])


class ManageSchoolTasksMain(BaseScreen):
    description = '<strong>Какие изменения Вы хотите внести в задачник?</strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button('Добавить задание➕', ManageSchoolTasksAdd,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
            [
                Button('Изменить задание✖', ManageSchoolTasksChangeMain,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
            [
                Button('Удалить задание➖', ManageSchoolTasksRemove,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
            [
                Button(BUTTON_BACK_TO_MENU, MainMenu,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
        ]


class ManageSchoolTasksAdd(BaseScreen):

    async def get_description(self, _update, _context):
        cursor.execute('SELECT COUNT(*) FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items')
        db_length = cursor.fetchall()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            return '<strong>По какому предмету будет задание?</strong>'
        else:
            return '<strong>В сообществе пока нету предметов!</strong>'

    async def add_default_keyboard(self, _update, _context):
        keyboard = []
        cursor.execute('SELECT COUNT(*) FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items')
        db_length = cursor.fetchall()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            cursor.execute('SELECT main_name FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items')
            main_name_list = cursor.fetchall()
            cursor.execute('SELECT item_index FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items')
            item_index_list = cursor.fetchall()
            cursor.execute('SELECT groups FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items')
            groups_list = cursor.fetchall()
            cursor.execute('SELECT emoji FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Items')
            emoji_list = cursor.fetchall()
            for i in range(db_length):
                main_name = get_clean_var(main_name_list, 'to_string', i - 1, True)
                item_index = get_clean_var(item_index_list, 'to_string', i - 1, True)
                groups = get_clean_var(groups_list, 'to_string', i - 1, True)
                emoji = get_clean_var(emoji_list, 'to_string', i - 1, True)
                keyboard.append([Button(emoji + main_name, self.get_school_item,
                                        source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                                        payload=dumps({'ADDING_TASK_NAME': main_name,
                                                       'ADDING_TASK_INDEX': item_index,
                                                       'ADDING_TASK_GROUPS': groups}))])
        keyboard.append([Button(BUTTON_BACK, ManageSchoolTasksMain,
                                source_type=SourcesTypes.GOTO_SOURCE_TYPE)])
        return keyboard

    @register_button_handler
    async def get_school_item(self, update, context):
        await get_payload_safe(self, update, context, 'add_task_item', 'ADDING_TASK_NAME')
        await get_payload_safe(self, update, context, 'add_task_item', 'ADDING_TASK_GROUPS')
        await get_payload_safe(self, update, context, 'add_task_item', 'ADDING_TASK_INDEX')
        if int(context.user_data['ADDING_TASK_GROUPS']) > 1:
            return await ManageSchoolTasksAddGroupNumber().goto(update, context)
        else:
            context.user_data['CURRENT_TYPING_ACTION'] = 'ADDING_TASK'
            return await ManageSchoolTasksAddDetails().goto(update, context)


class ManageSchoolTasksAddGroupNumber(BaseScreen):
    description = '<strong>Какой группе дано задание?</strong>'

    async def add_default_keyboard(self, _update, _context):
        keyboard = []
        for i in range(int(_context.user_data['ADDING_TASK_GROUPS'])):
            keyboard.append([Button('Группа ' + str(i + 1), self.get_group_number,
                                    source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                                    payload=dumps({'ADDING_TASK_GROUP_NUMBER': str(i + 1)}))])
        keyboard.append([Button(BUTTON_BACK, ManageSchoolTasksAdd, source_type=SourcesTypes.GOTO_SOURCE_TYPE)])
        return keyboard

    @register_button_handler
    async def get_group_number(self, _update, _context):
        await get_payload_safe(self, _update, _context, 'add_task_group_number', 'ADDING_TASK_GROUP_NUMBER')
        _context.user_data['CURRENT_TYPING_ACTION'] = 'ADDING_TASK'
        return await ManageSchoolTasksAddDetails().goto(_update, _context)

    @register_button_handler
    async def return_back(self, _update, _context):
        return await ManageSchoolTasksAdd().goto(_update, _context)


async def go_to_alert(task_args: list, task_context: str, current_index, _update, _context):
    AlertAddingOldTask().task_context = task_context
    AlertAddingOldTask.task_args = task_args
    AlertAddingOldTask().current_index = current_index
    return await AlertAddingOldTask().jump(_update, _context)


class ManageSchoolTasksAddDetails(BaseScreen):
    description = '<strong>Введите текст задания:</strong>'
    staged_once = False
    staged_twice = False
    is_adding_task = False
    current_stage = 0
    task_month = None
    task_year = None
    task_day = None
    task_description = None
    group_number = None
    task_item = None

    async def add_default_keyboard(self, _update, _context):
        if not Global.is_changing_day and not Global.is_changing_month:
            self.is_adding_task = True
        return [
            [
                Button(BUTTON_BACK, self.return_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE),
            ],
        ]

    async def set_stage(self, _update, _context, stage: int):
        desc_state = {0: "<strong>Введите текст задания: </strong>",
                      1: "<strong>На какой месяц дано задание?</strong>",
                      2: "<strong>На какое число дано задание?</strong>"}
        self.description = desc_state[stage]
        self.current_stage = stage

    @register_button_handler
    async def return_back(self, _update, _context):
        if self.current_stage == 0:
            _context.user_data['CURRENT_TYPING_ACTION'] = False
            self.is_adding_task = False
            return await ManageSchoolTasksAdd().goto(_update, _context)
        elif self.current_stage == 1:
            await self.set_stage(_update, _context, 0)
            return await ManageSchoolTasksAddDetails().jump(_update, _context)
        elif self.current_stage == 2:
            await self.set_stage(_update, _context, 1)
            return await ManageSchoolTasksAddDetails().jump(_update, _context)
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
        user = update.effective_user
        try:
            deletion_index = context.user_data['deletion_index']
        except KeyError:
            deletion_index = int()
        if str(user.id) in ADMIN_GROUP:
            if self.is_adding_task:
                if self.current_stage == 0:
                    context.user_data["ADDING_TASK_TASK_DESCRIPTION"] = update.message.text
                    await self.set_stage(update, context, 1)
                    return await ManageSchoolTasksAddDetails().jump(update, context)
                elif self.current_stage == 1:
                    context.user_data["ADDING_TASK_TASK_DAY"] = update.message.text
                    try:
                        check_day = int(context.user_data["ADDING_TASK_TASK_DAY"])
                        if check_day > 31 or check_day < 1:
                            self.description = ("<strong>Извините, но в данном месяце не может быть такое количество "
                                                "дней!\nНа какое число дано задание?</strong>")
                            return await ManageSchoolTasksAddDetails().jump(update, context)
                        else:
                            await self.set_stage(update, context, 2)
                            return await ManageSchoolTasksAddDetails().jump(update, context)
                    except ValueError:
                        self.description = "<strong>Пожалуйста, введите число, на день который дано задание!</strong>"
                        return await ManageSchoolTasksAddDetails().jump(update, context)
                else:
                    context.user_data["ADDING_TASK_TASK_MONTH"] = update.message.text
                    try:
                        context.user_data["ADDING_TASK_TASK_MONTH"] = int(
                            get_user_month(context.user_data["ADDING_TASK_TASK_MONTH"]))
                    except TypeError:
                        self.description = "<strong>Пожалуйста, введите месяц, на которое дано задание!</strong>"
                        return await ManageSchoolTasksAddDetails().jump(update, context)
                    try:
                        if int(context.user_data["ADDING_TASK_TASK_DAY"]) > int(
                                monthrange(int(strftime("%Y", gmtime())),
                                           int(context.user_data["ADDING_TASK_TASK_MONTH"]))[1]):
                            self.description = ("<strong>Извините, но в данном месяце не может быть такое количество "
                                                "дней!\nНа какое число дано задание?</strong>")
                            return await ManageSchoolTasksAddDetails().jump(update, context)
                        else:
                            if datetime.now().month == 12 and int(context.user_data["ADDING_TASK_TASK_MONTH"]) < 9:
                                context.user_data["ADDING_TASK_TASK_YEAR"] = str(datetime.now().year + 1)
                            else:
                                context.user_data["ADDING_TASK_TASK_YEAR"] = str(datetime.now().year)
                            self.is_adding_task = False
                            self.description = "<strong>Введите текст задания:</strong>"
                            await self.set_stage(update, context, 0)
                            context.user_data["IS_IN_MEDIA_SCREEN"] = True
                            return await CatchMedia().jump(update, context)
                    except ValueError:
                        self.description = "<strong>Пожалуйста, введите число, на месяц которого дано задание!</strong>"
                        return await ManageSchoolTasksAddDetails().jump(update, context)
            if Global.is_changing_task_description:
                self.task_description = update.message.text
                Global.is_changing_task_description = False
                check_task = await check_task_status(context)
                if not check_task:
                    return await show_notification_screen(update, context, 'send',
                                                          "<strong>Я не могу выполнить Ваш запрос - пожалуйста, повторите попытку</strong>",
                                                          [
                                                              [Button("🔄Повторить попытку", ManageSchoolTasksMain,
                                                                      source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                               ],
                                                              [Button(BUTTON_BACK, ManageSchoolTasksMain,
                                                                      source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                               ]])
                else:
                    formattered_index = await get_var_from_database(deletion_index, "item_index", True, context)
                    cursor.execute("UPDATE " + context.user_data[
                        'CURRENT_CLASS_NAME'] + "_Tasks set task_description = ? WHERE item_index = ?",
                                   (self.task_description, formattered_index,))
                    connection.commit()
                    await send_update_notification(update, context, "change", formattered_index, False)
                    return await show_notification_screen(update, context, 'send',
                                                          "✅<strong>Задание успешно изменено!</strong>", [
                                                              [Button('⬅️ В меню редактора', ManageSchoolTasksMain,
                                                                      source_type=SourcesTypes.GOTO_SOURCE_TYPE)],
                                                              [Button("⬅ Изменить ещё задания",
                                                                      ManageSchoolTasksChangeMain,
                                                                      source_type=SourcesTypes.GOTO_SOURCE_TYPE)],
                                                              [Button('⬅️ На главный экран', MainMenu,
                                                                      source_type=SourcesTypes.GOTO_SOURCE_TYPE)]])
            elif Global.is_changing_day:
                self.task_day = update.message.text
                check_task = await check_task_status(context)
                if not check_task:
                    return await show_notification_screen(update, context, 'send',
                                                          "<strong>Я не могу выполнить Ваш запрос - пожалуйста, повторите попытку</strong>",
                                                          [
                                                              [Button("🔄Повторить попытку", ManageSchoolTasksMain,
                                                                      source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                               ],
                                                              [Button(BUTTON_BACK, ManageSchoolTasksMain,
                                                                      source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                               ]])
                else:
                    try:
                        self.task_day = int(self.task_day)
                    except ValueError:
                        self.description = "<strong>На какой день дано задание?</strong>"
                        return await ManageSchoolTasksAddDetails().jump(update, context)
                    if not self.task_day < 1 and not self.task_day >= 32:
                        self.task_month = await get_var_from_database(deletion_index, "task_month", True, context)
                        check_task_day = update_day(self.task_month, self.task_day)
                        if check_task_day:
                            self.task_year = await get_var_from_database(deletion_index, "task_year", True, context)
                            check_val = check_task_validity(self.task_day, self.task_month, self.task_year)
                            formattered_index = await get_var_from_database(deletion_index, "item_index", True, context)
                            if check_val:
                                Global.is_changing_month = False
                                Global.is_changing_day = False
                                cursor.execute("UPDATE" + context.user_data[
                                    'CURRENT_CLASS_NAME'] + "_Tasks set task_day = ? WHERE item_index = ?",
                                               (self.task_day, formattered_index,))
                                connection.commit()
                                task_month = await get_var_from_database(deletion_index, "task_month", True, context)
                                self.task_year = await get_var_from_database(deletion_index, "task_year", True, context)
                                hypertime = get_hypertime(task_month, self.task_day, self.task_year)
                                cursor.execute("UPDATE" + context.user_data[
                                    'CURRENT_CLASS_NAME'] + "_Tasks set hypertime = ? WHERE item_index = ?",
                                               (hypertime, formattered_index,))
                                connection.commit()
                                await send_update_notification(update, context, "change", formattered_index,
                                                               False)
                                return await show_notification_screen(update, context, 'send',
                                                                      "✅<strong>Задание успешно изменено!</strong>", [
                                                                          [Button('⬅️ В меню редактора',
                                                                                  ManageSchoolTasksMain,
                                                                                  source_type=SourcesTypes.GOTO_SOURCE_TYPE)],
                                                                          [Button("⬅ Изменить ещё задания",
                                                                                  ManageSchoolTasksChangeMain,
                                                                                  source_type=SourcesTypes.GOTO_SOURCE_TYPE)],
                                                                          [Button('⬅️ На главный экран', MainMenu,
                                                                                  source_type=SourcesTypes.GOTO_SOURCE_TYPE)]])
                            else:
                                self.task_item = await get_var_from_database(deletion_index, "item_name", True, context)
                                self.task_description = await get_var_from_database(deletion_index,
                                                                                    "task_description", True, context)
                                self.group_number = await get_var_from_database(deletion_index,
                                                                                "group_number", True, context)
                                await go_to_alert([self.task_item, self.task_description, self.group_number,
                                                   self.task_day, self.task_month, self.task_year],
                                                  "change", formattered_index, update, context)
                        else:
                            self.description = "<strong>На какое число дано задание?</strong>"
                            return await ManageSchoolTasksAddDetails().jump(update, context)
                    else:
                        self.description = "<strong>На какое число дано задание?</strong>"
                        return await ManageSchoolTasksAddDetails().jump(update, context)
            elif Global.is_changing_month:
                self.task_month = update.message.text
                check_task = await check_task_status(context)
                if not check_task:
                    return await show_notification_screen(update, context, 'send',
                                                          "<strong>Я не могу выполнить Ваш запрос - пожалуйста, повторите попытку</strong>",
                                                          [
                                                              [Button("🔄Повторить попытку", ManageSchoolTasksMain,
                                                                      source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                               ],
                                                              [Button(BUTTON_BACK, ManageSchoolTasksMain,
                                                                      source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                               ]])
                else:
                    check_day = await get_var_from_database(deletion_index, "task_day", True, context)
                    try:
                        check_month = update_month(int(check_day), self.task_month)
                    except TypeError:
                        ManageSchoolTasksAddDetails().description = "<strong>На какой месяц дано задание?</strong>"
                        return await ManageSchoolTasksAddDetails().jump(update, context)
                    if check_month:
                        formattered_index = await get_var_from_database(deletion_index, "item_index", True, context)
                        if check_month < 9:
                            self.task_year = await get_var_from_database(deletion_index, "task_year", True, context)
                            if int(self.task_year) < datetime.now().year + 1 and datetime.now().month == 12:
                                self.task_year = int(self.task_year) + 1
                            else:
                                self.task_year = datetime.now().year
                                cursor.execute("UPDATE" + context.user_data[
                                    'CURRENT_CLASS_NAME'] + "_Tasks set task_year = ? WHERE item_index = ?",
                                               (self.task_year, formattered_index,))
                        else:
                            self.task_year = datetime.now().year
                            cursor.execute("UPDATE" + context.user_data[
                                'CURRENT_CLASS_NAME'] + "_Tasks set task_year = ? WHERE item_index = ?",
                                           (self.task_year, formattered_index,))
                        self.task_day = await get_var_from_database(deletion_index, "task_day", True, context)
                        check_val = check_task_validity(self.task_day, check_month, self.task_year)
                        if check_val:
                            self.description = "<strong>Введите текст задания:</strong>"
                            Global.is_changing_month = False
                            Global.is_changing_day = False
                            hypertime = get_hypertime(check_month, int(self.task_day), self.task_year)
                            cursor.execute("UPDATE" + context.user_data[
                                'CURRENT_CLASS_NAME'] + "_Tasks set task_month = ? WHERE item_index = ?",
                                           (check_month, formattered_index,))
                            cursor.execute("UPDATE" + context.user_data[
                                'CURRENT_CLASS_NAME'] + "_Tasks set hypertime = ? WHERE item_index = ?",
                                           (hypertime, formattered_index,))
                            connection.commit()
                            if int(self.task_year) != datetime.now().year:
                                cursor.execute("UPDATE" + context.user_data[
                                    'CURRENT_CLASS_NAME'] + "_Tasks set task_year = ? WHERE item_index = ?",
                                               (self.task_year, formattered_index,))
                                connection.commit()
                            await send_update_notification(update, context, "change", formattered_index,
                                                           False)
                            return await show_notification_screen(update, context, 'send',
                                                                  "✅<strong>Задание успешно изменено!</strong>", [
                                                                      [Button('⬅️ В меню редактора',
                                                                              ManageSchoolTasksMain,
                                                                              source_type=SourcesTypes.GOTO_SOURCE_TYPE)],
                                                                      [Button("⬅ Изменить ещё задания",
                                                                              ManageSchoolTasksChangeMain,
                                                                              source_type=SourcesTypes.GOTO_SOURCE_TYPE)],
                                                                      [Button('⬅️ На главный экран', MainMenu,
                                                                              source_type=SourcesTypes.GOTO_SOURCE_TYPE)]])
                        else:
                            self.task_item = await get_var_from_database(formattered_index, "item_name", False, context)
                            self.task_description = await get_var_from_database(formattered_index,
                                                                                "task_description", False, context)
                            self.group_number = await get_var_from_database(formattered_index,
                                                                            "group_number", False, context)
                            await go_to_alert([self.task_item, self.task_description, self.group_number,
                                               int(self.task_day), check_month, self.task_year],
                                              "change", formattered_index, update, context)
                    else:
                        self.description = "<strong>На какой месяц дано задание?</strong>"
                        return await ManageSchoolTasksAddDetails().jump(update, context)
            elif Global.is_creating_class:
                context.user_data['CURRENT_CLASS_NAME'] = update.message.text
                context.user_data['CURRENT_CLASS_NAME'] = context.user_data['CURRENT_CLASS_NAME'].replace(' ', '')
                Global.is_creating_class = False
                Global.is_adding_password_to_class = True
                return await CreateCommunityPassword().jump(update, context)
            elif Global.is_adding_password_to_class:
                context.user_data['CURRENT_CLASS_PASSWORD'] = update.message.text
                Global.is_adding_password_to_class = False
                cursor.execute('INSERT INTO Community (name, password) VALUES (?,?)',
                               (context.user_data['CURRENT_CLASS_NAME'], context.user_data['CURRENT_CLASS_PASSWORD']))
                connection.commit()
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS ''' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks' + ''' (
                item_name TEXT,
                item_index INTEGER,
                group_number INTEGER,
                task_description TEXT,
                task_day INT,
                task_month INT,
                task_year INT,
                hypertime INT
                )
                ''')
                cursor.execute('''
                                                CREATE TABLE IF NOT EXISTS ''' + context.user_data[
                    'CURRENT_CLASS_NAME'] + '_Items' + ''' (
                                                item_index INT,
                                                emoji TEXT UNIQUE,
                                                main_name TEXT UNIQUE,
                                                rod_name TEXT UNIQUE,
                                                groups INT
                                                )
                                                ''')
                cursor.execute('INSERT INTO UserCommunities (user_id, class_name, user_role_in_class) VALUES (?,?,?)',
                               (update.message.chat.id, context.user_data['CURRENT_CLASS_NAME'], "HOST"))
                connection.commit()
                return await show_notification_screen(update, context, 'send',
                                                      '<strong>Ваше сообщество было создано! Не забудьте добавить к нему школьные предметы,'
                                                      'чтобы Вы и администраторы смогли добавлять задания!</strong>', [
                                                          [Button(BUTTON_BACK_TO_MENU, MainMenu,
                                                                  source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                           ]])
            elif Global.is_creating_item_name:
                context.user_data['CREATING_ITEM_NAME'] = update.message.text
                Global.is_creating_item_name = False
                Global.is_creating_item_rod_name = True
                return await ManageCommunityItemsAddRodName().jump(update, context)
            elif Global.is_creating_item_rod_name:
                context.user_data['CREATING_ITEM_ROD_NAME'] = update.message.text
                Global.is_creating_item_rod_name = False
                Global.is_creating_item_group = True
                return await ManageCommunityItemsAddGroup().jump(update, context)
            elif Global.is_creating_item_group:
                try:
                    context.user_data['CREATING_ITEM_GROUPS'] = int(update.message.text)
                except ValueError:
                    return await ManageCommunityItemsAddGroup().jump(update, context)
                context.user_data['CREATING_ITEM_GROUPS'] = update.message.text
                Global.is_creating_item_group = False
                Global.is_creating_item_emoji = True
                return await ManageCommunityItemsAddEmoji().jump(update, context)
            elif Global.is_creating_item_emoji:
                if len(update.message.text) - 1 == 1 and is_emoji(update.message.text):
                    Global.is_creating_item_emoji = False
                    context.user_data['CREATING_ITEM_EMOJI'] = update.message.text
                    cursor.execute('INSERT INTO ' + context.user_data[
                        'CURRENT_CLASS_NAME'] + '_Items (item_index, emoji, main_name, rod_name, groups) VALUES (?, ?, ?, ?, ?)',
                                   (generate_id(), context.user_data['CREATING_ITEM_EMOJI'],
                                    context.user_data['CREATING_ITEM_NAME'],
                                    context.user_data['CREATING_ITEM_ROD_NAME'],
                                    context.user_data['CREATING_ITEM_GROUPS']), )
                    connection.commit()
                    return await show_notification_screen(update, context, 'send',
                                                          '<strong>Ваш прдемет успешно создан и добавлен в Ваш класс!</strong>',
                                                          [
                                                              [Button('Создать ещё предмет', self.go_create_more_items,
                                                                      source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
                                                               ],
                                                              [Button('В центральное меню', ManageCommunityItems,
                                                                      source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                               ],
                                                              [Button(BUTTON_BACK_TO_MENU, MainMenu,
                                                                      source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                               ]])
                else:
                    return await ManageCommunityItemsAddEmoji().jump(update, context)
            elif Global.is_changing_class_name:
                new_community_name = update.message.text.replace(' ', '')
                cursor.execute('UPDATE Community SET name = ? WHERE name = ?',
                               (new_community_name, context.user_data['CURRENT_CLASS_NAME'],))
                cursor.execute('UPDATE UserCommunities SET class_name = ? WHERE class_name = ?',
                               (new_community_name, context.user_data['CURRENT_CLASS_NAME'],))
                with suppress(OperationalError):
                    cursor.execute('ALTER TABLE ' + context.user_data[
                        'CURRENT_CLASS_NAME'] + '_Items RENAME TO ' + new_community_name + '_Items')
                    cursor.execute('ALTER TABLE ' + context.user_data[
                        'CURRENT_CLASS_NAME'] + '_Tasks RENAME TO ' + new_community_name + '_Tasks')
                    connection.commit()
                context.user_data['CURRENT_CLASS_NAME'] = new_community_name
                Global.is_changing_class_name = False
                return await show_notification_screen(update, context, 'send',
                                                      '<strong>Название Вашего сообщества успешно изменено!</strong>', [
                                                          [Button('Ещё раз изменить название сообщества',
                                                                  self.go_change_name,
                                                                  source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
                                                           ],
                                                          [Button('В панель управления сообществом',
                                                                  ManageCommunityMain,
                                                                  source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                           ],
                                                          [Button(BUTTON_BACK_TO_MENU, MainMenu,
                                                                  source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                           ]])
            elif Global.is_changing_class_password:
                cursor.execute('UPDATE Community set password = ? WHERE name = ?',
                               (update.message.text, context.user_data['CURRENT_CLASS_NAME'],))
                connection.commit()
                return await show_notification_screen(update, context, 'send',
                                                      '<strong>Пароль Вашего сообщества был успешно изменён!</strong>',
                                                      [
                                                          [Button('Ещё раз изменить пароль сообщества',
                                                                  self.go_change_password,
                                                                  source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
                                                           ],
                                                          [Button('В панель управления сообществом',
                                                                  ManageCommunityMain,
                                                                  source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                           ],
                                                          [Button(BUTTON_BACK_TO_MENU, MainMenu,
                                                                  source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                           ]])
            elif Global.is_changing_item_name:
                cursor.execute('UPDATE ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items SET main_name = ?',
                               (update.message.text,))
                cursor.execute('UPDATE ' + context.user_data[
                    'CURRENT_CLASS_NAME'] + '_Tasks SET item_name = ? WHERE item_index = ?',
                               (update.message.text, context.user_data['MANAGE_ITEM_INDEX'],))
                connection.commit()
                Global.is_changing_item_name = False
                return await show_notification_screen(update, context, 'send',
                                                      '<strong>Название предмета успешно изменено!</strong>', [
                                                          [
                                                              Button('Ещё раз изменить название предмета',
                                                                     self.go_change_item_name,
                                                                     source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
                                                          ],
                                                          [
                                                              Button('В панель управления предметом', ManageSchoolItem,
                                                                     source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                          ],
                                                          [
                                                              Button('В панель управления сообществом',
                                                                     ManageCommunityMain,
                                                                     source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                          ],
                                                          [
                                                              Button(BUTTON_BACK_TO_MENU, MainMenu,
                                                                     source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                          ]
                                                      ])
            elif Global.is_changing_item_rod_name:
                cursor.execute('UPDATE ' + context.user_data[
                    'CURRENT_CLASS_NAME'] + '_Items SET rod_name = ? WHERE item_index = ?',
                               (update.message.text, context.user_data['MANAGE_ITEM_INDEX']))
                connection.commit()
                Global.is_changing_item_rod_name = False
                return await show_notification_screen(update, context, 'send',
                                                      '<strong>Название предмета в дательном падеже успешно изменено!</strong>',
                                                      [
                                                          [Button(
                                                              'Ещё раз изменить название предмета в дательном падеже',
                                                              self.go_change_rod_name,
                                                              source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
                                                          ],
                                                          [Button('В панель управления предметом', ManageSchoolItem,
                                                                  source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                           ],
                                                          [Button('В панель управления сообществом',
                                                                  ManageCommunityMain,
                                                                  source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                           ],
                                                          [Button(BUTTON_BACK_TO_MENU, MainMenu,
                                                                  source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                           ]])
            elif Global.is_changing_item_groups:
                try:
                    new_group_number = int(update.message.text)
                    if new_group_number > 0:
                        cursor.execute('UPDATE ' + context.user_data[
                            'CURRENT_CLASS_NAME'] + '_Items SET groups = ? WHERE item_index = ?',
                                       (update.message.text, context.user_data['MANAGE_ITEM_INDEX'],))
                        connection.commit()
                        Global.is_changing_group_number = False
                        return await show_notification_screen(update, context, 'send',
                                                              '<strong>Количество предмета было успешно изменено!</strong>',
                                                              [
                                                                  [Button('Ещё раз изменить количество групп предмета',
                                                                          self.go_change_groups,
                                                                          source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
                                                                   ],
                                                                  [Button('В панель управления предметом',
                                                                          ManageSchoolItem,
                                                                          source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                                   ],
                                                                  [Button('В панель управления сообществом',
                                                                          ManageCommunityMain,
                                                                          source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                                   ],
                                                                  [Button(BUTTON_BACK_TO_MENU, MainMenu,
                                                                          source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                                   ]
                                                              ])
                    else:
                        return await ManageSchoolItemChangeGroups().jump(update, context)
                except ValueError:
                    return await ManageSchoolItemChangeGroups().jump(update, context)
            elif Global.is_changing_item_emoji:
                if len(update.message.text) - 1 == 1 and is_emoji(update.message.text):
                    Global.is_changing_item_emoji = False
                    cursor.execute('UPDATE ' + context.user_data[
                        'CURRENT_CLASS_NAME'] + '_Items SET emoji = ? WHERE item_index = ?',
                                   (update.message.text, context.user_data['MANAGE_ITEM_INDEX']))
                    connection.commit()
                    return await show_notification_screen(update, context, 'send',
                                                          '<strong>Эмодзи предмета был успешно изменён!</strong>', [
                                                              [Button('Ещё раз изменить эмодзи предмета',
                                                                      self.go_change_emoji,
                                                                      source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
                                                               ],
                                                              [Button('В панель управления предметом', ManageSchoolItem,
                                                                      source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                               ],
                                                              [Button('В панель управления сообществом',
                                                                      ManageCommunityMain,
                                                                      source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                               ],
                                                              [Button(BUTTON_BACK_TO_MENU, MainMenu,
                                                                      source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                               ]
                                                          ])
                else:
                    return await ManageSchoolItemChangeEmoji().jump(update, context)

    @register_button_handler
    async def go_create_more_items(self, _update, _context):
        Global.is_creating_item_name = True
        return await ManageCommunityItemsAddName().goto(_update, _context)

    @register_button_handler
    async def go_change_name(self, _update, _context):
        Global.is_changing_class_name = True
        return await ManageCommunityChangeName().goto(_update, _context)

    @register_button_handler
    async def go_change_rod_name(self, _update, _context):
        Global.is_changing_item_rod_name = True
        return await ManageSchoolItemChangeRodName().goto(_update, _context)

    @register_button_handler
    async def go_change_password(self, _update, _context):
        Global.is_changing_class_password = True
        return await ManageCommunityChangePassword().goto(_update, _context)

    @register_button_handler
    async def go_change_item_name(self, _update, _context):
        Global.is_changing_item_name = True
        return await ManageSchoolItemChangeName().goto(_update, _context)

    @register_button_handler
    async def go_change_groups(self, _update, _context):
        Global.is_changing_item_groups = True
        return await ManageSchoolItemChangeGroups().goto(_update, _context)

    @register_button_handler
    async def go_change_emoji(self, _update, _context):
        Global.is_changing_item_emoji = True
        return await ManageSchoolItemChangeEmoji().goto(_update, _context)


class CatchMedia(BaseScreen):
    description = '<strong>Отправьте в чат фотографии, которые нужно закрепить к заданию: </strong>'

    @register_input_handler
    async def catch_media(self, update, context):
        if update.message.text and update.message.text == '/start':
            return await MainMenu().jump(update, context)
        with suppress(KeyError):
            if context.user_data["IS_IN_MEDIA_SCREEN"]:
                message = update.message
                if message.photo:
                    file = message.photo[-1]
                    file_id = file.file_id
                    file = await context.bot.get_file(file_id)
                    try:
                        context.user_data["MEDIA_ADD"].append(file)
                    except KeyError:
                        context.user_data["MEDIA_ADD"] = []
                        context.user_data["MEDIA_ADD"].append(file)
                    new_config = RenderConfig()
                    new_config.description = "✅<strong>Успешно получено! Что вы ещё хотите сделать?</strong>"
                    new_config.keyboard = [
                        [
                            Button("Создать задание➕", self.add_school_task,
                                   source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
                        ],
                        [
                            Button("Удалить присланные фотографии🗑️", self.delete_media,
                                   source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
                        ],
                        [
                            Button(BUTTON_BACK, self.go_to_task_screen,
                                   source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
                        ]
                    ]
                    return await CatchMedia().send(context, config=new_config, extra_data=None)

    @register_button_handler
    async def go_to_task_screen(self, update, context):
        context.user_data["MEDIA_ADD"] = []
        return await ManageSchoolTasksAdd().goto(update, context)

    @register_button_handler
    async def delete_media(self, update, context):
        new_config = RenderConfig()
        new_config.description = '<strong>Вы точно уверены, что хотите удалить присланные Вами изображения?</strong>'
        new_config.keyboard = [
            [
                Button('Удалить🗑️', self.confirm_delete,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]
        return await CatchMedia().send(context, config=new_config, extra_data=None)

    @register_button_handler
    async def go_back(self, update, context):
        new_config = RenderConfig()
        new_config.description = self.description
        new_config.keyboard = [
            [
                Button("Создать задание➕", self.add_school_task,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button("Удалить присланные фотографии🗑️", self.delete_media,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button(BUTTON_BACK, self.go_to_task_screen,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]
        return await CatchMedia().send(context, config=new_config, extra_data=None)

    @register_button_handler
    async def confirm_delete(self, update, context):
        context.user_data["MEDIA_ADD"] = []
        new_config = RenderConfig()
        new_config.description = "✅<strong>Фотографии успешно удалены! Что вы ещё хотите сделать?</strong>"
        new_config.keyboard = [
            [
                Button("Создать задание➕", self.add_school_task,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button(BUTTON_BACK, self.go_to_task_screen,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]
        return await CatchMedia().send(context, config=new_config, extra_data=None)

    @register_button_handler
    async def add_school_task(self, update, context):
        check = check_task_validity(int(context.user_data["ADDING_TASK_TASK_DAY"]),
                                    context.user_data["ADDING_TASK_TASK_MONTH"],
                                    context.user_data["ADDING_TASK_TASK_YEAR"])
        context.user_data["ADD_TASK_ITEM_INDEX"] = str(generate_id())
        if check:
            try:
                try:
                    await add_task_school(update, context, context.user_data["ADDING_TASK_NAME"],
                                            context.user_data["ADDING_TASK_TASK_DESCRIPTION"],
                                            context.user_data["ADDING_TASK_GROUP_NUMBER"],
                                            int(context.user_data["ADDING_TASK_TASK_DAY"]),
                                            int(context.user_data["ADDING_TASK_TASK_MONTH"]),
                                            int(context.user_data["ADDING_TASK_TASK_YEAR"]))
                except KeyError:
                    await add_task_school(update, context, context.user_data["ADDING_TASK_NAME"],
                                          context.user_data["ADDING_TASK_TASK_DESCRIPTION"],
                                          1,
                                          int(context.user_data["ADDING_TASK_TASK_DAY"]),
                                          int(context.user_data["ADDING_TASK_TASK_MONTH"]),
                                          int(context.user_data["ADDING_TASK_TASK_YEAR"]))
            except KeyError:
                await add_task_school(update, context, context.user_data["ADDING_TASK_NAME"],
                                      context.user_data["ADDING_TASK_TASK_DESCRIPTION"],
                                      1,
                                      int(context.user_data["ADDING_TASK_TASK_DAY"]),
                                      int(context.user_data["ADDING_TASK_TASK_MONTH"]),
                                      int(context.user_data["ADDING_TASK_TASK_YEAR"]))
        else:
            await go_to_alert([context.user_data["ADDING_TASK_TASK_ITEM"],
                               context.user_data["ADDING_TASK_TASK_DESCRIPTION"],
                               context.user_data["ADDING_TASK_GROUP_NUMBER"],
                               context.user_data["ADDING_TASK_TASK_DAY"],
                               context.user_data["ADDING_TASK_TASK_MONTH"],
                               context.user_data["ADDING_TASK_TASK_YEAR"]],
                              "add", context.user_data['ADD_TASK_ITEM_INDEX'], update, context)

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button("Добавить задание➕", self.add_school_task,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button(BUTTON_BACK, ManageSchoolTasksAdd,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]


class ManageSchoolTasksRemove(BaseScreen):

    async def add_default_keyboard(self, _update, _context):
        cursor.execute('SELECT * FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Tasks')
        db_check = cursor.fetchall()
        try:
            db_check = get_clean_var(db_check, "to_string", False, True)
        except IndexError:
            db_check = ""
        cursor.execute('SELECT COUNT(*) FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Tasks')
        db_length = cursor.fetchall()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        keyboard = []
        for task_index in range(db_length):
            with suppress(KeyError):
                button_name = await get_button_title(task_index, _context)
                button_list = [
                    Button(
                        str(button_name), self.remove_task,
                        source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                        payload=dumps({'task_index': task_index,
                                       'db_check': db_check}),
                    )
                ]
                keyboard.append(button_list)
        exit_button = [Button(BUTTON_BACK, ManageSchoolTasksMain,
                              source_type=SourcesTypes.GOTO_SOURCE_TYPE)]
        keyboard.append(exit_button)
        return keyboard

    async def get_description(self, _update, _context):
        await SchoolTasks().check_tasks(_update, _context, None)
        database_length = await get_var_from_database(None, "database_length_SchoolTasker", True, _context)
        if database_length >= 1:
            return "<strong>Какое из этих заданий Вы хотите удалить?</strong>"
        else:
            return "<strong>На данный момент список заданий пуст!</strong>"

    @register_button_handler
    async def remove_task(self, update, context):
        await get_payload_safe(self, update, context, 'delete_task', 'task_index')
        await get_payload_safe(self, update, context, 'delete_task', 'db_check')
        return await ManageSchoolTasksRemoveConfirm().goto(update, context)


class ManageSchoolTasksRemoveConfirm(BaseScreen):
    description = "<strong>Вы действительно хотите удалить данное задание?</strong>"
    deletion_index = 0

    async def add_default_keyboard(self, _update, _context):

        return [
            [
                Button("Удалить🗑️", self.delete_school_task, source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button(BUTTON_BACK, ManageSchoolTasksRemove, source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def delete_school_task(self, _update, _context):
        check_task = await check_task_status(_context)
        if not check_task:
            return await show_notification_screen(_update, _context, 'render',
                                                  "<strong>Я не могу выполнить Ваш запрос - пожалуйста, повторите попытку</strong>",
                                                  [
                                                      [Button("🔄Повторить попытку", ManageSchoolTasksMain,
                                                              source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                       ],
                                                      [Button(BUTTON_BACK, ManageSchoolTasksMain,
                                                              source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                       ]])
        else:
            Global.index_store -= 1
            task_index = _context.user_data['task_index']
            user = _update.effective_user
            formatted_index = await get_var_from_database(task_index, "item_index", True, _context)
            name = get_username(user.first_name, user.last_name, user.username)
            await logger_alert([name, user.id], "delete", formatted_index, False, _context)
            cursor.execute(
                '''DELETE FROM ''' + _context.user_data['CURRENT_CLASS_NAME'] + '''_Tasks WHERE item_index = ?''',
                (formatted_index,))
            connection.commit()
            if exists(str(MEDIA_ROOT) + '/' + formatted_index + '/'):
                rmtree(str(MEDIA_ROOT) + '/' + formatted_index)
            database_length = await get_var_from_database(None, "database_length_SchoolTasker", True, _context)
            if database_length > 0:
                keyboard = [
                    [
                        Button('⬅️ В меню редактора', ManageSchoolTasksMain,
                               source_type=SourcesTypes.GOTO_SOURCE_TYPE),
                    ],
                    [
                        Button('⬅️ Удалить  ещё задание', ManageSchoolTasksRemove,
                               source_type=SourcesTypes.GOTO_SOURCE_TYPE),
                    ],
                    [
                        Button('⬅️ На главный экран', MainMenu,
                               source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                    ],
                ]
            else:
                keyboard = [
                    [
                        Button('⬅️ В меню редактора', ManageSchoolTasksMain,
                               source_type=SourcesTypes.GOTO_SOURCE_TYPE),
                    ],
                    [
                        Button('⬅️ На главный экран', MainMenu,
                               source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                    ],
                ]
            return await show_notification_screen(_update, _context, 'render',
                                                  "✅<strong>Задание успешно удалено!</strong>", keyboard)

    async def get_description(self, _update, _context):
        return "<strong>Вы действительно хотите удалить данное задание?</strong>"


class ManageSchoolTasksChangeBase(BaseScreen):
    description = "<strong>Что Вы хотите изменить в данном задании?</strong>"

    async def add_default_keyboard(self, _update, _context):
        check_index = _context.user_data["task_index"]
        check_item = await get_var_from_database(check_index, "item_name", True, _context)
        keyboard = [
            [
                Button("Предмет", self.change_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"task_index": _context.user_data['task_index']}))
            ],
            [
                Button("Задание", self.change_school_task,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"deletion_index": _context.user_data['task_index']}))
            ],
            [
                Button("День", self.change_task_day,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"deletion_index": _context.user_data['task_index']}))
            ],
            [
                Button("Месяц", self.change_task_month,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"deletion_index": _context.user_data['task_index']}))
            ],
            [
                Button(BUTTON_BACK, ManageSchoolTasksChangeMain,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]
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
        await get_payload_safe(self, update, context, 'change_task_item', 'task_index')
        return await ManageSchoolTasksChangeItem().goto(update, context)


class ManageSchoolTasksChangeMain(BaseScreen):

    async def add_default_keyboard(self, _update, _context):
        cursor.execute('SELECT * FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Tasks')
        db_check = cursor.fetchall()
        try:
            db_check = get_clean_var(db_check, "to_string", False, True)
        except IndexError:
            db_check = ""
        cursor.execute('SELECT COUNT(*) FROM ' + _context.user_data['CURRENT_CLASS_NAME'] + '_Tasks')
        db_length = cursor.fetchall()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        keyboard = []
        for task_index in range(db_length):
            with suppress(KeyError):
                button_name = await get_button_title(task_index, _context)
                button_list = [
                    Button(
                        str(button_name), self.change_task,
                        source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                        payload=dumps({'task_index': task_index,
                                       'db_check': db_check}),
                    )
                ]
                keyboard.append(button_list)
        exit_button = [Button(BUTTON_BACK, ManageSchoolTasksMain,
                              source_type=SourcesTypes.GOTO_SOURCE_TYPE)]
        keyboard.append(exit_button)
        return keyboard

    async def get_description(self, _update, _context):
        await SchoolTasks().check_tasks(_update, _context, None)
        database_length = await get_var_from_database(None, "database_length_SchoolTasker", True, _context)
        if database_length > 0:
            return "<strong>Какое из этих заданий Вы хотите изменить?</strong>"
        if database_length < 1:
            return "<strong>На данный момент список заданий пуст!</strong>"

    @register_button_handler
    async def change_task(self, update, context):
        await get_payload_safe(self, update, context, 'change_task', 'task_index')
        await get_payload_safe(self, update, context, 'change_task', 'db_check')
        return await ManageSchoolTasksChangeBase().goto(update, context)


class ManageSchoolTasksChangeItem(BaseScreen):
    description = "<strong>По какому предмету будет задание?</strong>"

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button("Алгебра", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"task_item": "Алгебра", "task_index": _context.user_data['task_index']})),
                Button("Английский язык", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps(
                           {"task_item": "Английский язык", "task_index": _context.user_data['task_index']})),
                Button("Биология", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"task_item": "Биология", "task_index": _context.user_data['task_index']})),
                Button("География", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"task_item": "География", "task_index": _context.user_data['task_index']})),
                Button("Геометрия", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"task_item": "Геометрия", "task_index": _context.user_data['task_index']})),
            ],
            [
                Button("Информатика", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps(
                           {"task_item": "Информатика", "task_index": _context.user_data['task_index']})),
                Button("История", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"task_item": "История", "task_index": _context.user_data['task_index']})),
                Button("Литература", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"task_item": "Литература", "task_index": _context.user_data['task_index']})),
                Button("ОБЗР", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"task_item": "ОБЗР", "task_index": _context.user_data['task_index']})),
                Button("Обществознание", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps(
                           {"task_item": "Обществознание", "task_index": _context.user_data['task_index']})),
            ],
            [
                Button("Решение задач повышенного уровня по алгебре", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps(
                           {"task_item": "Решение задач повышенного уровня по алгебре",
                            "task_index": _context.user_data['task_index']})),
                Button("Русский язык", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps(
                           {"task_item": "Русский язык", "task_index": _context.user_data['task_index']})),
                Button("Технология", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"task_item": "Технология", "task_index": _context.user_data['task_index']})),
                Button("Физика", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"task_item": "Физика", "task_index": _context.user_data['task_index']})),
                Button("Химия", self.change_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"task_item": "Химия", "task_index": _context.user_data['task_index']}))
            ],
            [
                Button(BUTTON_BACK, ManageSchoolTasksChangeBase,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),

            ]
        ]

    @register_button_handler
    async def change_item(self, update, context):
        check_task = await check_task_status(context)
        if not check_task:
            return await show_notification_screen(update, context, 'render',
                                                  "<strong>Я не могу выполнить Ваш запрос - пожалуйста, повторите попытку</strong>",
                                                  [
                                                      [Button("🔄Повторить попытку", ManageSchoolTasksMain,
                                                              source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                       ],
                                                      [Button(BUTTON_BACK, ManageSchoolTasksMain,
                                                              source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                       ]])
        else:
            await get_payload_safe(self, update, context, 'change_task_item', 'task_index')
            await get_payload_safe(self, update, context, 'change_task_item', 'task_item')
            index = int(context.user_data["task_index"])
            new_index = await get_var_from_database(index, "item_index", True, context)
            cursor.execute("UPDATE SchoolTasker set item_name = ? WHERE item_index = ?",
                           (context.user_data['task_item'], new_index,))
            connection.commit()
            await send_update_notification(update, context, "change", new_index, False)
            return await show_notification_screen(update, context, 'render',
                                                  "✅<strong>Задание успешно изменено!</strong>", [
                                                      [Button('⬅️ В меню редактора', ManageSchoolTasksMain,
                                                              source_type=SourcesTypes.GOTO_SOURCE_TYPE)],
                                                      [Button("⬅ Изменить ещё задания", ManageSchoolTasksChangeMain,
                                                              source_type=SourcesTypes.GOTO_SOURCE_TYPE)],
                                                      [Button('⬅️ На главный экран', MainMenu,
                                                              source_type=SourcesTypes.GOTO_SOURCE_TYPE)]])


class ManageSchoolTasksChangeTask(BaseScreen):
    description = "<strong>Введите текст задания:</strong>"
    current_index = int()
    task_description = str()

    async def add_default_keyboard(self, _update, _context):
        Global.is_changing_task_description = True
        await get_payload_safe(self, _update, _context, 'change_task_description', 'deletion_index')
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, update, context):
        Global.is_changing_task_description = False
        return await ManageSchoolTasksChangeBase().goto(update, context)


class ManageSchoolTasksChangeDay(BaseScreen):
    description = "<strong>На какой день дано задание?</strong>"
    task_description = str()

    async def add_default_keyboard(self, _update, _context):
        Global.is_changing_day = True
        await get_payload_safe(self, _update, _context, 'change_task_day', 'deletion_index')
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, update, context):
        Global.is_changing_day = False
        return await ManageSchoolTasksChangeBase().goto(update, context)


class ManageSchoolTasksChangeMonth(BaseScreen):
    description = "<strong>На какой месяц дано задание?</strong>"
    task_description = str()

    async def add_default_keyboard(self, _update, _context):
        Global.is_changing_month = True
        await get_payload_safe(self, _update, _context, 'change_task_month', 'deletion_index')
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, update, context):
        Global.is_changing_month = False
        return await ManageSchoolTasksChangeBase().goto(update, context)


class ManageSchoolTasksChangeGroupNumber(BaseScreen):
    description = "<strong>Какой группе дано задание?</strong>"
    deletion_index = int()

    async def add_default_keyboard(self, _update, _context):
        self.deletion_index = _context.user_data['task_index']
        Global.is_changing_group_number = True
        check_item = await get_var_from_database(self.deletion_index, "item_name", True, _context)
        if check_item == "Английский язык":
            return [
                [
                    Button('Группа 1️⃣', self.change_group_number,
                           source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                           payload=dumps({"group_number": 1})),
                    Button('Группа 2️⃣', self.change_group_number,
                           source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                           payload=dumps({"group_number": 2}))
                ],
                [
                    Button(BUTTON_BACK, self.go_back,
                           source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
                ],
            ]
        if check_item == "Информатика":
            return [
                [
                    Button('Группа 1️⃣', self.change_group_number,
                           source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                           payload=dumps({"group_number": 1})),
                    Button('Группа 2️⃣', self.change_group_number,
                           source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                           payload=dumps({"group_number": 2}))
                ],
                [
                    Button(BUTTON_BACK, self.go_back,
                           source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
                ],
            ]

    @register_button_handler
    async def change_group_number(self, update, context):
        check_task = await check_task_status(context)
        if not check_task:
            return await show_notification_screen(update, context, 'render',
                                                  "<strong>Я не могу выполнить Ваш запрос - пожалуйста, повторите попытку</strong>",
                                                  [
                                                      [Button("🔄Повторить попытку", ManageSchoolTasksMain,
                                                              source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                       ],
                                                      [Button(BUTTON_BACK, ManageSchoolTasksMain,
                                                              source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                                                       ]])
        else:
            await get_payload_safe(self, update, context, 'change_task_group_number', 'group_number')
            formattered_index = await get_var_from_database(self.deletion_index, "item_index", True, context)
            cursor.execute("UPDATE SchoolTasker SET group_number = ? WHERE item_index = ?",
                           (context.user_data["group_number"], formattered_index,))
            connection.commit()
            await send_update_notification(update, context, "change", int(formattered_index), False)
            return await show_notification_screen(update, context, 'render',
                                                  "✅<strong>Задание успешно изменено!</strong>", [
                                                      [Button('⬅️ В меню редактора', ManageSchoolTasksMain,
                                                              source_type=SourcesTypes.GOTO_SOURCE_TYPE)],
                                                      [Button("⬅ Изменить ещё задания", ManageSchoolTasksChangeMain,
                                                              source_type=SourcesTypes.GOTO_SOURCE_TYPE)],
                                                      [Button('⬅️ На главный экран', MainMenu,
                                                              source_type=SourcesTypes.GOTO_SOURCE_TYPE)]])

    @register_button_handler
    async def go_back(self, update, context):
        Global.is_changing_group_number = False
        return await ManageSchoolTasksChangeBase().goto(update, context)
