from json import dumps
from os import makedirs, listdir
from shutil import rmtree
from sqlite3 import IntegrityError
from telegram.error import Forbidden, BadRequest
from backend import *
from os.path import exists
from constants import *
from contextlib import suppress
from hammett_extensions.carousel import STCarouselWidget
from hammett.core import Screen, Button
from hammett.core.constants import SourcesTypes, RenderConfig
from hammett.core.handlers import register_button_handler, register_typing_handler
from hammett.core.hiders import ONLY_FOR_ADMIN, Hider
from hammett.core.mixins import StartMixin
from hammett_extensions.handlers import register_input_handler
from settings import ADMIN_GROUP, MEDIA_ROOT, MAX_CAPTION_LENGTH


async def send_update_notification(update, context, status, index, is_order: bool):
    user = update.effective_user
    name = await get_username(user.first_name, user.last_name, user.username)
    await logger_alert([name, user.id], status, index, is_order)
    task_item = await get_var_from_database(index, "item_name", is_order)
    task_description = await get_var_from_database(index, "task_description", is_order)
    group_number = await get_var_from_database(index, "group_number", is_order)
    task_day = await get_var_from_database(index, "task_day", is_order)
    task_month = await get_var_from_database(index, "task_month", is_order)
    task_month_int = int(task_month)
    task_month = await recognise_month(task_month)
    task_year = await get_var_from_database(index, "task_year", is_order)
    id_result = []
    # for id_row in cursor.execute('SELECT user_id FROM Users WHERE user_permission = 1 AND user_id != ?',
    #                              (user.id,)):
    for id_row in cursor.execute('SELECT user_id FROM Users WHERE user_permission = 1'):
        id_row = list(id_row)
        id_row = int(id_row[0])
        id_result.append(id_row)
    for user_id in id_result:
        cursor.execute("SELECT user_name FROM Users WHERE user_id = ?", (user_id,))
        name = cursor.fetchall()
        name = await get_clean_var(name, "to_string", 0, True)
        notification_title = "<strong>Здравствуйте, " + str(name) + "!" + "\n"
        notification_title += await get_notification_title(task_item, task_description,
                                                           group_number, task_day, task_month_int, task_month,
                                                           task_year, status)
        ns_config = RenderConfig(
            chat_id=user_id
        )
        NotificationScreen.images = []
        if exists("media/" + str(index) + '/'):
            add_images = listdir('media/' + str(index) + "/")
            for image in add_images:
                path = str(index) + "/" + str(image)
                item = [MEDIA_ROOT / path, ""]
                NotificationScreen.images.append(item)
        else:
            NotificationScreen.images = [
                [MEDIA_ROOT / 'school_tasker_logo.webp', ""]
            ]
        NotificationScreen.description = notification_title
        with suppress(Forbidden):
            await NotificationScreen().send(context, config=ns_config, extra_data=None)


async def add_task_school(_update, _context, task_item, task_description, group_number, task_day, task_month,
                          task_year):
    hypertime = await get_hypertime(int(task_month), int(task_day), int(task_year))
    cursor.execute(
        'INSERT INTO SchoolTasker (item_name, item_index, group_number, task_description, task_day, task_month, '
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
                filename = _context.user_data["ADD_TASK_ITEM_INDEX"] + "/" + str(await generate_id()) + ".webp"
                title = "media/" + filename
                await file.download_to_drive(title)
    with suppress(KeyError):
        _context.user_data["MEDIA_ADD"].clear()
    _context.user_data["IS_IN_MEDIA_SCREEN"] = False
    await send_update_notification(_update, _context, "add", _context.user_data["ADD_TASK_ITEM_INDEX"],
                                   False)
    return await TaskWasAdded().jump(_update, _context)


class BaseScreen(Screen):
    cache_covers = True
    hide_keyboard = True
    cover = 'media/school_tasker_logo.webp'


class NewsNotificationScreen(BaseScreen):
    pass


class TaskCantBeChanged(BaseScreen):
    description = "<strong>Я не могу выполнить Ваш запрос - пожалуйста, повторите попытку</strong>"

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button("🔄Повторить попытку", ManageSchoolTasksMain,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ],
            [
                Button("⬅Назад", ManageSchoolTasksMain,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]


class MainMenu(StartMixin, BaseScreen):

    async def get_config(self, update, _context, **_kwargs):
        user_id = update.effective_user.id
        config = RenderConfig()
        name = await get_username(update.effective_user.first_name, update.effective_user.last_name,
                                  update.effective_user.username)
        try:
            cursor.execute(
                'INSERT INTO Users (user_permission, user_id, user_name) '
                'VALUES'
                '(?,?,?)',
                (1, user_id, name))
            connection.commit()
            if str(user_id) in ADMIN_GROUP:
                config.description = GREET_ADMIN_FIRST[randint(0, 2)]
            else:
                config.description = GREET_ANONIM_FIRST[randint(0, 2)]
        except IntegrityError or AttributeError:
            cursor.execute("UPDATE Users SET user_name = ? WHERE user_id = ?", (name, user_id,))
            connection.commit()
            if str(user_id) in ADMIN_GROUP:
                config.description = await get_greet(name)
                # config.description = GREET_ADMIN_LATEST[randint(0, 2)]
            else:
                config.description = await get_greet(name)
                # config.description = GREET_ANONIM_LATEST[randint(0, 2)]
        config.keyboard = [
            [
                Button('Зайти в задачник📓', self.school_tasks,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE),
            ],
            [
                Button('Внести изменения в задачник🔧', ManageSchoolTasksMain,
                       hiders=Hider(ONLY_FOR_ADMIN),
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
            [
                Button('Настройки⚙', Options,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
            [
                Button('Что нового сегодня?✨', WhatsNew,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
            [
                Button('Подробнее о School Tasker📋', SocialMedia,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]
        return config

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
        user_name = await get_username(user.first_name, user.last_name, user.username)
        if str(user.id) in ADMIN_GROUP:
            LOGGER.info('The user %s (%s) was added to the admin group.', user_name, user.id)
        else:
            LOGGER.info('The user %s (%s) was added to the anonim group.', user_name, user.id)
        return await super().start(update, context)

    # @register_input_handler
    # @check_media_screen
    # async def catch_media(self, update, context):
    #     if not update.message.text:
    #         message = update.message
    #         if message.photo:
    #             file = message.photo[-1]
    #             file_id = file.file_id
    #             file = await context.bot.get_file(file_id)
    #             title = "FILE" + str(randint(0, 99)) + ".jpg"
    #             await file.download_to_drive(title)
    #             await update.message.reply_text("GOT IMAGE!")
    #         elif message.video:
    #             file_id = message.video.file_id
    #             file = await context.bot.get_file(file_id)
    #             await file.download_to_drive('video.mp4')
    #             await update.message.reply_text("GOT VIDEO!")
    #         # elif message.audio:
    #         #     file_id = message.audio.file_id
    #         #     file = await context.bot.get_file(file_id)
    #         #     await file.download('audio.mp3')
    #         #     await update.message.reply_text("GOT AUDIO!")
    #         else:
    #             await update.message.reply_text("UNSUPORRTED FILE!")


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
                Button("⬅Вернуться на главный экран", MainMenu,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]


class WhatsNew(BaseScreen):
    description = "_"

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button("⬅Вернуться на главный экран", MainMenu, source_type=SourcesTypes.GOTO_SOURCE_TYPE)
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
        cursor.execute("SELECT user_permission FROM Users WHERE user_id = ?", (user.id,))
        notification_permission = cursor.fetchone()
        notification_permission = await get_clean_var(notification_permission, "to_int", False, True)
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
                Button('⬅️ Вернуться на главный экран', MainMenu,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def edit_notification_permission(self, _update, _context):
        await main_get_payload(self, _update, _context, "options", "index")
        notification_permission = _context.user_data['index']
        if notification_permission == 1:
            notification_permission = 0
        else:
            notification_permission = 1
        user = _update.effective_user
        cursor.execute(
            'UPDATE Users set user_permission = ? WHERE user_id = ?', (notification_permission, user.id))
        connection.commit()
        return await self.goto(_update, _context)


class SchoolTasks(BaseScreen):

    async def check_tasks(self, update, context, target_screen):
        new_config = RenderConfig()
        new_config.keyboard = []
        Global.index_store = await get_var_from_database(None, "database_length_SchoolTasker", True)
        database_length = Global.index_store
        title = str()
        if database_length < 1:
            if target_screen:
                target_screen.description = "<strong>На данный момент список заданий пуст!</strong>"
                new_config.keyboard = [[Button('⬅️ Вернуться на главный экран', MainMenu,
                                               source_type=SourcesTypes.GOTO_SOURCE_TYPE)]]
                return await target_screen().render(update, context, config=new_config)
        else:
            Global.open_date = True
            new_title = str()
            tasks_to_delete = []
            for i in range(database_length):
                title, current_title, check_day, check_month, check_year = await get_multipy_async(i, title)
                if check_year == datetime.now().year:
                    if check_month == datetime.now().month:
                        if check_day <= datetime.now().day:
                            title = ""
                            cursor.execute("SELECT item_index FROM SchoolTasker ORDER BY hypertime ASC")
                            del_index = cursor.fetchall()
                            del_index = await get_clean_var(del_index, "to_string", i, True)
                            if del_index not in tasks_to_delete:
                                tasks_to_delete.append(del_index)
                    if check_month < datetime.now().month:
                        title = ""
                        cursor.execute("SELECT item_index FROM SchoolTasker ORDER BY hypertime ASC")
                        del_index = cursor.fetchall()
                        del_index = await get_clean_var(del_index, "to_string", i, True)
                        if del_index not in tasks_to_delete:
                            tasks_to_delete.append(del_index)
                if check_year < datetime.now().year:
                    title = ""
                    cursor.execute("SELECT item_index FROM SchoolTasker ORDER BY hypertime ASC")
                    del_index = cursor.fetchall()
                    del_index = await get_clean_var(del_index, "to_string", i, True)
                    if del_index not in tasks_to_delete:
                        tasks_to_delete.append(del_index)
                else:
                    new_title = title
                    Global.open_date = False
                    cursor.execute("SELECT item_index FROM SchoolTasker ORDER BY hypertime ASC")
                    media_index = cursor.fetchall()
                    media_index = await get_clean_var(media_index, "to_string", i, True)
                    if exists(str(MEDIA_ROOT) + "/" + media_index) and media_index not in tasks_to_delete:
                        media_button_title = str()
                        cursor.execute('SELECT item_name FROM SchoolTasker WHERE item_index = ?', (media_index,))
                        media_item_name = cursor.fetchone()
                        media_item_name = await get_clean_var(media_item_name, 'to_string', False, True)
                        media_button_title += "🖼" + media_item_name
                        if media_item_name == "Английский язык" or media_item_name == "Информатика":
                            cursor.execute('SELECT group_number FROM SchoolTasker WHERE item_index = ?',
                                           (media_index,))
                            media_group_number = cursor.fetchone()
                            media_group_number = await get_clean_var(media_group_number, 'to_string', False,
                                                                     True)
                            media_button_title += '(' + media_group_number + "ая группа)"
                        media_button_title += ': '
                        cursor.execute('SELECT task_description FROM SchoolTasker WHERE item_index = ?',
                                       (media_index,))
                        media_task_description = cursor.fetchone()
                        media_task_description = await get_clean_var(media_task_description, 'to_string',
                                                                     False, True)
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
                await logger_alert([], "delete", task_id, False)
                cursor.execute('DELETE FROM SchoolTasker WHERE item_index = ?', (task_id,))
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
                new_config.keyboard.append([Button('⬅️ Вернуться на главный экран', MainMenu,
                                                   source_type=SourcesTypes.GOTO_SOURCE_TYPE)])
                try:
                    return await target_screen().render(update, context, config=new_config)
                except BadRequest:
                    for i in range(0, len(target_screen.description), MAX_CAPTION_LENGTH):
                        target_screen.description = target_screen.description[i:i + MAX_CAPTION_LENGTH]
                        return await target_screen().send(context, config=new_config)

    @register_button_handler
    async def _goto_task_media(self, update, context):
        await main_get_payload(self, update, context, "task_media_index", 'MEDIA_INDEX_GOTO')
        await main_get_payload(self, update, context, "task_media_index", 'MEDIA_TITLE')
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
        [MEDIA_ROOT / "school_tasker_logo.webp", "_"]
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
        # ManageSchoolTasksAddDetails.task_item = self.task_args[0]
        # ManageSchoolTasksAddDetails.task_description = self.task_args[1]
        # ManageSchoolTasksAddDetails.group_number = self.task_args[2]
        # ManageSchoolTasksAddDetails.task_day = self.task_args[3]
        # ManageSchoolTasksAddDetails.task_month = self.task_args[4]
        # ManageSchoolTasksAddDetails.task_year = self.task_args[5]
        return await ManageSchoolTasksAddDetails().goto(_update, _context)

    @register_button_handler
    async def add_old_task(self, _update, _context):
        await ManageSchoolTasksAddDetails().set_stage(_update, _context, 0)
        _context.user_data["ADD_TASK_ITEM_INDEX"] = str(await generate_id())
        await add_task_school(_update, _context, self.task_args[0], self.task_args[1], self.task_args[2],
                              self.task_args[3], self.task_args[4], self.task_args[5])

    @register_button_handler
    async def change_task(self, _update, _context):
        self.task_args[5] = datetime.now().year
        cursor.execute('UPDATE SchoolTasker set task_day = ?, task_month = ?, task_year = ? WHERE item_index = ?',
                       (self.task_args[3], self.task_args[4], self.task_args[5], self.current_index,))
        connection.commit()
        hypertime = await get_hypertime(self.task_args[4], self.task_args[3], self.task_args[5])
        cursor.execute("UPDATE SchoolTasker set hypertime = ? WHERE item_index = ?",
                       (hypertime, self.current_index,))
        connection.commit()
        await send_update_notification(_update, _context, "change", self.current_index, False)
        return await TaskWasChanged().jump(_update, _context)


class ManageSchoolTasksMain(BaseScreen):
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
                Button('⬅️ Вернуться на главный экран', MainMenu,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def go_to_remove_tasks_screen(self, _update, _context):
        database_length = await get_var_from_database(None, "database_length_SchoolTasker", True)
        if database_length >= 1:
            ManageSchoolTasksRemove.description = "<strong>Какое из этих заданий Вы хотите удалить?</strong>"
        else:
            ManageSchoolTasksRemove.description = "<strong>На данный момент список заданий пуст!</strong>"
        return await ManageSchoolTasksRemove().goto(_update, _context)

    @register_button_handler
    async def go_to_change_tasks_screen(self, _update, _context):
        database_length = await get_var_from_database(None, "database_length_SchoolTasker", True)
        if database_length > 0:
            ManageSchoolTasksChangeMain.description = "<strong>Какое из этих заданий Вы хотите изменить?</strong>"
        else:
            ManageSchoolTasksChangeMain.description = "<strong>На данный момент список заданий пуст!</strong>"
        return await ManageSchoolTasksChangeMain().goto(_update, _context)


class ManageSchoolTasksAdd(BaseScreen):
    description = '<strong>По какому предмету будет задание?</strong>'

    async def add_default_keyboard(self, _update, _context):
        return [
            [
                Button("Алгебра", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({'ADDING_TASK_TASK_ITEM': "Алгебра"})),
                Button("Английский язык", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({'ADDING_TASK_TASK_ITEM': "Английский язык"})),
                Button("Биология", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({'ADDING_TASK_TASK_ITEM': "Биология"})),
                Button("География", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({'ADDING_TASK_TASK_ITEM': "География"})),
                Button("Геометрия", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({'ADDING_TASK_TASK_ITEM': "Геометрия"})),
            ],
            [
                Button("Информатика", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({'ADDING_TASK_TASK_ITEM': "Информатика"})),
                Button("История", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({'ADDING_TASK_TASK_ITEM': "История"})),
                Button("Литература", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({'ADDING_TASK_TASK_ITEM': "Литература"})),
                Button("ОБЗР", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({'ADDING_TASK_TASK_ITEM': "ОБЗР"})),
                Button("Обществознание", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({'ADDING_TASK_TASK_ITEM': "Обществознание"})),
            ],
            [
                Button("Решение задач повышенного уровня по алгебре", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({'ADDING_TASK_TASK_ITEM': "Решение задач повышенного уровня по алгебре"})),
                Button("Русский язык", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({'ADDING_TASK_TASK_ITEM': "Русский язык"})),
                Button("Технология", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({'ADDING_TASK_TASK_ITEM': "Технология"})),
                Button("Физика", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({'ADDING_TASK_TASK_ITEM': "Физика"})),
                Button("Химия", self.get_school_item,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({'ADDING_TASK_TASK_ITEM': "Химия"})),
            ],
            [
                Button('⬅️ Назад', ManageSchoolTasksMain,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),
            ]
        ]

    @register_button_handler
    async def get_school_item(self, update, context):
        await main_get_payload(self, update, context, 'add_task_item', 'ADDING_TASK_TASK_ITEM')
        if (context.user_data["ADDING_TASK_TASK_ITEM"] == "Английский язык" or
                context.user_data["ADDING_TASK_TASK_ITEM"] == "Информатика"):
            return await ManageSchoolTasksAddGroupNumber().goto(update, context)
        else:
            return await ManageSchoolTasksAddDetails().goto(update, context)


class ManageSchoolTasksAddGroupNumber(BaseScreen):
    description = '<strong>Какой группе дано задание?</strong>'

    async def add_default_keyboard(self, _update, _context):
        keyboard = []
        buttons = []
        if _context.user_data["ADDING_TASK_TASK_ITEM"] == "Английский язык":
            buttons.append(
                Button('Группа 1️⃣', self.get_group_number,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"ADDING_TASK_GROUP_NUMBER": 1})))
            buttons.append(
                Button('Группа 2️⃣', self.get_group_number,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"ADDING_TASK_GROUP_NUMBER": 2})))
        if _context.user_data['ADDING_TASK_TASK_ITEM'] == "Информатика":
            buttons.append(
                Button('Группа 1️⃣', self.get_group_number,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"ADDING_TASK_GROUP_NUMBER": 1})))
            buttons.append(
                Button('Группа 2️⃣', self.get_group_number,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"ADDING_TASK_GROUP_NUMBER": 2})))
        keyboard.append(buttons)
        keyboard.append(
            [
                Button('⬅️ Назад', self.return_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ])
        return keyboard

    @register_button_handler
    async def get_group_number(self, _update, _context):
        await main_get_payload(self, _update, _context, 'add_task_group_number', 'ADDING_TASK_GROUP_NUMBER')
        return await ManageSchoolTasksAddDetails().goto(_update, _context)

    @register_button_handler
    async def return_back(self, _update, _context):
        return await ManageSchoolTasksAdd().goto(_update, _context)


class TaskWasChanged(BaseScreen):
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
                Button('⬅️ На главный экран', MainMenu,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ],
        ]


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

    async def add_default_keyboard(self, _update, _context):
        if not Global.is_changing_day and not Global.is_changing_month:
            self.is_adding_task = True
        return [
            [
                Button('⬅️ Назад', self.return_back,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE),
            ],
        ]

    async def set_stage(self, _update, _context, stage: int):
        desc_state = {0: "<strong>Введите текст задания: </strong>",
                      1: "<strong>На какое число дано задание?</strong>",
                      2: "<strong>На какой месяц дано задание?</strong>"}
        self.description = desc_state[stage]
        self.current_stage = stage

    @register_button_handler
    async def return_back(self, _update, _context):
        if self.current_stage == 0:
            self.is_adding_task = False
            return await ManageSchoolTasksAdd().goto(_update, _context)
        # else:
        #     await self.set_stage(_update, _context, self.current_stage - 1)
        #     return await ManageSchoolTasksAddDetails().jump(_update, _context)
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
                if (context.user_data['ADDING_TASK_TASK_ITEM'] != "Английский язык" and
                        context.user_data['ADDING_TASK_TASK_ITEM'] != "Информатика"):
                    context.user_data['ADDING_TASK_GROUP_NUMBER'] = 1
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
                            await get_user_month(context.user_data["ADDING_TASK_TASK_MONTH"]))
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
                                # self.task_year = datetime.now().year + 1
                                context.user_data["ADDING_TASK_TASK_YEAR"] = str(datetime.now().year + 1)
                            else:
                                # self.task_year = datetime.now().year
                                context.user_data["ADDING_TASK_TASK_YEAR"] = str(datetime.now().year)
                            # check = await check_task_validity(int(context.user_data["ADDING_TASK_TASK_DAY"]),
                            #                                   context.user_data["ADDING_TASK_TASK_MONTH"],
                            #                                   context.user_data["ADDING_TASK_TASK_YEAR"])
                            self.is_adding_task = False
                            # if check:
                            self.description = "<strong>Введите текст задания:</strong>"
                            await self.set_stage(update, context, 0)
                            context.user_data["IS_IN_MEDIA_SCREEN"] = True
                            return await CatchMedia().jump(update, context)
                            # await add_task_school(update, context, self.task_item, self.task_description,
                            #                       self.group_number, self.task_day, self.task_month,
                            #                       self.task_year)
                            #     await add_task_school(update, context, context.user_data["ADDING_TASK_TASK_ITEM"],
                            #                           context.user_data["ADDING_TASK_TASK_DESCRIPTION"],
                            #                           context.user_data["ADDING_TASK_GROUP_NUMBER"],
                            #                           int(context.user_data["ADDING_TASK_TASK_DAY"]),
                            #                           int(context.user_data["ADDING_TASK_TASK_MONTH"]),
                            #                           int(context.user_data["ADDING_TASK_TASK_YEAR"]))
                            # else:
                            #     await go_to_alert([context.user_data["ADDING_TASK_TASK_ITEM"],
                            #                        context.user_data["ADDING_TASK_TASK_DESCRIPTION"],
                            #                        context.user_data["ADDING_TASK_GROUP_NUMBER"],
                            #                        context.user_data["ADDING_TASK_TASK_DAY"],
                            #                        context.user_data["ADDING_TASK_TASK_MONTH"],
                            #                        context.user_data["ADDING_TASK_TASK_YEAR"]],
                            #                       "add", deletion_index, update, context)
                    except ValueError:
                        self.description = "<strong>Пожалуйста, введите число, на месяц которого дано задание!</strong>"
                        return await ManageSchoolTasksAddDetails().jump(update, context)
            if Global.is_changing_task_description:
                self.task_description = update.message.text
                Global.is_changing_task_description = False
                check_task = await check_task_status(context)
                if not check_task:
                    return await TaskCantBeChanged().jump(update, context)
                else:
                    formattered_index = await get_var_from_database(deletion_index, "item_index", True)
                    cursor.execute("UPDATE SchoolTasker set task_description = ? WHERE item_index = ?",
                                   (self.task_description, formattered_index,))
                    connection.commit()
                    await send_update_notification(update, context, "change", formattered_index, False)
                    return await TaskWasChanged().jump(update, context)
            elif Global.is_changing_day:
                self.task_day = update.message.text
                check_task = await check_task_status(context)
                if not check_task:
                    return await TaskCantBeChanged().jump(update, context)
                else:
                    try:
                        self.task_day = int(self.task_day)
                    except ValueError:
                        self.description = "<strong>На какой день дано задание?</strong>"
                        return await ManageSchoolTasksAddDetails().jump(update, context)
                    if not self.task_day < 1 and not self.task_day >= 32:
                        self.task_month = await get_var_from_database(deletion_index, "task_month", True)
                        check_task_day = await update_day(self.task_month, self.task_day)
                        if check_task_day:
                            self.task_year = await get_var_from_database(deletion_index, "task_year", True)
                            check_val = await check_task_validity(self.task_day, self.task_month, self.task_year)
                            formattered_index = await get_var_from_database(deletion_index, "item_index", True)
                            if check_val:
                                Global.is_changing_month = False
                                Global.is_changing_day = False
                                cursor.execute("UPDATE SchoolTasker set task_day = ? WHERE item_index = ?",
                                               (self.task_day, formattered_index,))
                                connection.commit()
                                task_month = await get_var_from_database(deletion_index, "task_month", True)
                                self.task_year = await get_var_from_database(deletion_index, "task_year", True)
                                hypertime = await get_hypertime(task_month, self.task_day, self.task_year)
                                cursor.execute("UPDATE SchoolTasker set hypertime = ? WHERE item_index = ?",
                                               (hypertime, formattered_index,))
                                connection.commit()
                                await send_update_notification(update, context, "change", formattered_index,
                                                               False)
                                return await TaskWasChanged().jump(update, context)
                            else:
                                self.task_item = await get_var_from_database(deletion_index, "item_name", True)
                                self.task_description = await get_var_from_database(deletion_index,
                                                                                    "task_description", True)
                                self.group_number = await get_var_from_database(deletion_index,
                                                                                "group_number", True)
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
                    return await TaskCantBeChanged().jump(update, context)
                else:
                    check_day = await get_var_from_database(deletion_index, "task_day", True)
                    try:
                        check_month = await update_month(int(check_day), self.task_month)
                    except TypeError:
                        ManageSchoolTasksAddDetails().description = "<strong>На какой месяц дано задание?</strong>"
                        return await ManageSchoolTasksAddDetails().jump(update, context)
                    if check_month:
                        formattered_index = await get_var_from_database(deletion_index, "item_index", True)
                        if check_month < 9:
                            self.task_year = await get_var_from_database(deletion_index, "task_year", True)
                            if int(self.task_year) < datetime.now().year + 1 and datetime.now().month == 12:
                                self.task_year = int(self.task_year) + 1
                            else:
                                self.task_year = datetime.now().year
                                cursor.execute("UPDATE SchoolTasker set task_year = ? WHERE item_index = ?",
                                               (self.task_year, formattered_index,))
                        else:
                            self.task_year = datetime.now().year
                            cursor.execute("UPDATE SchoolTasker set task_year = ? WHERE item_index = ?",
                                           (self.task_year, formattered_index,))
                        self.task_day = await get_var_from_database(deletion_index, "task_day", True)
                        check_val = await check_task_validity(self.task_day, check_month, self.task_year)
                        if check_val:
                            self.description = "<strong>Введите текст задания:</strong>"
                            Global.is_changing_month = False
                            Global.is_changing_day = False
                            hypertime = await get_hypertime(check_month, int(self.task_day), self.task_year)
                            cursor.execute("UPDATE SchoolTasker set task_month = ? WHERE item_index = ?",
                                           (check_month, formattered_index,))
                            cursor.execute("UPDATE SchoolTasker set hypertime = ? WHERE item_index = ?",
                                           (hypertime, formattered_index,))
                            connection.commit()
                            if int(self.task_year) != datetime.now().year:
                                cursor.execute("UPDATE SchoolTasker set task_year = ? WHERE item_index = ?",
                                               (self.task_year, formattered_index,))
                                connection.commit()
                            await send_update_notification(update, context, "change", formattered_index,
                                                           False)
                            return await TaskWasChanged().jump(update, context)
                        else:
                            self.task_item = await get_var_from_database(formattered_index, "item_name", False)
                            self.task_description = await get_var_from_database(formattered_index,
                                                                                "task_description", False)
                            self.group_number = await get_var_from_database(formattered_index,
                                                                            "group_number", False)
                            await go_to_alert([self.task_item, self.task_description, self.group_number,
                                               int(self.task_day), check_month, self.task_year],
                                              "change", formattered_index, update, context)
                    else:
                        self.description = "<strong>На какой месяц дано задание?</strong>"
                        return await ManageSchoolTasksAddDetails().jump(update, context)


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
                            Button("⬅Назад", self.go_to_task_screen,
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
                Button('⬅Назад', self.go_back,
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
                Button("⬅Назад", self.go_to_task_screen,
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
                Button("⬅Назад", self.go_to_task_screen,
                       source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
            ]
        ]
        return await CatchMedia().send(context, config=new_config, extra_data=None)

    @register_button_handler
    async def add_school_task(self, update, context):
        check = await check_task_validity(int(context.user_data["ADDING_TASK_TASK_DAY"]),
                                          context.user_data["ADDING_TASK_TASK_MONTH"],
                                          context.user_data["ADDING_TASK_TASK_YEAR"])
        context.user_data["ADD_TASK_ITEM_INDEX"] = str(await generate_id())
        if check:
            await add_task_school(update, context, context.user_data["ADDING_TASK_TASK_ITEM"],
                                  context.user_data["ADDING_TASK_TASK_DESCRIPTION"],
                                  context.user_data["ADDING_TASK_GROUP_NUMBER"],
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
                Button("⬅Назад", ManageSchoolTasksAdd,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]


class TaskWasAdded(BaseScreen):
    description = "✅<strong>Задание успешно добавлено!</strong>"

    async def add_default_keyboard(self, _update, _context):
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
                Button('⬅️ На главный экран', MainMenu,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ],
        ]


class ManageSchoolTasksRemove(BaseScreen):

    async def add_default_keyboard(self, _update, _context):
        database_length = await get_var_from_database(None, "database_length_SchoolTasker", True)
        cursor.execute('SELECT * FROM SchoolTasker')
        db_check = cursor.fetchall()
        try:
            db_check = await get_clean_var(db_check, "to_string", False, True)
        except IndexError:
            db_check = ""
        keyboard = []
        for task_index in range(database_length):
            with suppress(KeyError):
                button_name = await get_button_title(task_index)
                button_list = [
                    Button(
                        str(button_name), self.remove_task,
                        source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                        payload=dumps({'task_index': task_index,
                                       'db_check': db_check}),
                    )
                ]
                keyboard.append(button_list)
        exit_button = [Button('⬅️ Назад', ManageSchoolTasksMain,
                              source_type=SourcesTypes.GOTO_SOURCE_TYPE)]
        keyboard.append(exit_button)
        return keyboard

    async def get_description(self, _update, _context):
        await SchoolTasks().check_tasks(_update, _context, None)
        database_length = await get_var_from_database(None, "database_length_SchoolTasker", True)
        if database_length >= 1:
            return "<strong>Какое из этих заданий Вы хотите удалить?</strong>"
        else:
            return "<strong>На данный момент список заданий пуст!</strong>"

    @register_button_handler
    async def remove_task(self, update, context):
        await main_get_payload(self, update, context, 'delete_task', 'task_index')
        await main_get_payload(self, update, context, 'delete_task', 'db_check')
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
                Button("⬅Назад", ManageSchoolTasksRemove, source_type=SourcesTypes.GOTO_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def delete_school_task(self, _update, _context):
        check_task = await check_task_status(_context)
        if not check_task:
            return await TaskCantBeChanged().goto(_update, _context)
        else:
            Global.index_store -= 1
            task_index = _context.user_data['task_index']
            user = _update.effective_user
            formatted_index = await get_var_from_database(task_index, "item_index", True)
            name = await get_username(user.first_name, user.last_name, user.username)
            await logger_alert([name, user.id], "delete", formatted_index, False)
            cursor.execute('''DELETE FROM SchoolTasker WHERE item_index = ?''', (formatted_index,))
            connection.commit()
            if exists(str(MEDIA_ROOT) + '/' + formatted_index + '/'):
                rmtree(str(MEDIA_ROOT) + '/' + formatted_index)
            return await TaskWasRemoved().goto(_update, _context)

    async def get_description(self, _update, _context):
        return "<strong>Вы действительно хотите удалить данное задание?</strong>"


class TaskWasRemoved(BaseScreen):
    description = "✅<strong>Задание успешно удалено!</strong>"

    async def add_default_keyboard(self, _update, _context):
        database_length = await get_var_from_database(None, "database_length_SchoolTasker", True)
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
                    Button('⬅️ На главный экран', MainMenu,
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
                    Button('⬅️ На главный экран', MainMenu,
                           source_type=SourcesTypes.GOTO_SOURCE_TYPE)
                ],
            ]


class ManageSchoolTasksChangeBase(BaseScreen):
    description = "<strong>Что Вы хотите изменить в данном задании?</strong>"

    async def add_default_keyboard(self, _update, _context):
        check_index = _context.user_data["task_index"]
        check_item = await get_var_from_database(check_index, "item_name", True)
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
                Button("⬅Назад", ManageSchoolTasksChangeMain,
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
        await main_get_payload(self, update, context, 'change_task_item', 'task_index')
        return await ManageSchoolTasksChangeItem().goto(update, context)


class ManageSchoolTasksChangeMain(BaseScreen):

    async def add_default_keyboard(self, _update, _context):
        database_length = await get_var_from_database(None, "database_length_SchoolTasker", True)
        cursor.execute('SELECT * FROM SchoolTasker')
        db_check = cursor.fetchall()
        try:
            db_check = await get_clean_var(db_check, "to_string", False, True)
        except IndexError:
            db_check = ""
        keyboard = []
        for task_index in range(database_length):
            button_name = await get_button_title(task_index)
            new_button = [Button(button_name, self.change_task,
                                 source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
                                 payload=dumps({'task_index': task_index,
                                                'db_check': db_check}))]
            keyboard.append(new_button)
        exit_button = [Button('⬅️ Назад', ManageSchoolTasksMain,
                              source_type=SourcesTypes.GOTO_SOURCE_TYPE)]
        keyboard.append(exit_button)
        return keyboard

    async def get_description(self, _update, _context):
        await SchoolTasks().check_tasks(_update, _context, None)
        database_length = await get_var_from_database(None, "database_length_SchoolTasker", True)
        if database_length > 0:
            return "<strong>Какое из этих заданий Вы хотите изменить?</strong>"
        if database_length < 1:
            return "<strong>На данный момент список заданий пуст!</strong>"

    @register_button_handler
    async def change_task(self, update, context):
        await main_get_payload(self, update, context, 'change_task', 'task_index')
        await main_get_payload(self, update, context, 'change_task', 'db_check')
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
                Button('⬅️ Назад', ManageSchoolTasksChangeBase,
                       source_type=SourcesTypes.GOTO_SOURCE_TYPE),

            ]
        ]

    @register_button_handler
    async def change_item(self, update, context):
        check_task = await check_task_status(context)
        if not check_task:
            return await TaskCantBeChanged().goto(update, context)
        else:
            await main_get_payload(self, update, context, 'change_task_item', 'task_index')
            await main_get_payload(self, update, context, 'change_task_item', 'task_item')
            index = int(context.user_data["task_index"])
            new_index = await get_var_from_database(index, "item_index", True)
            cursor.execute("UPDATE SchoolTasker set item_name = ? WHERE item_index = ?",
                           (context.user_data['task_item'], new_index,))
            connection.commit()
            await send_update_notification(update, context, "change", new_index, False)
            return await TaskWasChanged().goto(update, context)


class ManageSchoolTasksChangeTask(BaseScreen):
    description = "<strong>Введите текст задания:</strong>"
    current_index = int()
    task_description = str()

    async def add_default_keyboard(self, _update, _context):
        Global.is_changing_task_description = True
        await main_get_payload(self, _update, _context, 'change_task_description', 'deletion_index')
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


class ManageSchoolTasksChangeDay(BaseScreen):
    description = "<strong>На какой день дано задание?</strong>"
    task_description = str()

    async def add_default_keyboard(self, _update, _context):
        Global.is_changing_day = True
        await main_get_payload(self, _update, _context, 'change_task_day', 'deletion_index')
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


class ManageSchoolTasksChangeMonth(BaseScreen):
    description = "<strong>На какой месяц дано задание?</strong>"
    task_description = str()

    async def add_default_keyboard(self, _update, _context):
        Global.is_changing_month = True
        await main_get_payload(self, _update, _context, 'change_task_month', 'deletion_index')
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


class ManageSchoolTasksChangeGroupNumber(BaseScreen):
    description = "<strong>Какой группе дано задание?</strong>"
    deletion_index = int()

    async def add_default_keyboard(self, _update, _context):
        self.deletion_index = _context.user_data['task_index']
        Global.is_changing_group_number = True
        check_item = await get_var_from_database(self.deletion_index, "item_name", True)
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
                    Button('⬅️ Назад', self.go_back,
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
                    Button('⬅️ Назад', self.go_back,
                           source_type=SourcesTypes.HANDLER_SOURCE_TYPE)
                ],
            ]

    @register_button_handler
    async def change_group_number(self, update, context):
        check_task = await check_task_status(context)
        if not check_task:
            return await TaskCantBeChanged().goto(update, context)
        else:
            await main_get_payload(self, update, context, 'change_task_group_number', 'group_number')
            formattered_index = await get_var_from_database(self.deletion_index, "item_index", True)
            cursor.execute("UPDATE SchoolTasker SET group_number = ? WHERE item_index = ?",
                           (context.user_data["group_number"], formattered_index,))
            connection.commit()
            await send_update_notification(update, context, "change", int(formattered_index), False)
            return await TaskWasChanged().goto(update, context)

    @register_button_handler
    async def go_back(self, update, context):
        Global.is_changing_group_number = False
        return await ManageSchoolTasksChangeBase().goto(update, context)
