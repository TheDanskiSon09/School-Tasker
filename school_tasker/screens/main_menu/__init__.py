from hammett.core.handlers import register_button_handler
from hammett.core.mixins import StartMixin
from mysql.connector import IntegrityError
from backend import *
from constants import FIRST_GREET, BUTTON_BACK_TO_MENU, ENTER_TO_TASKS, MAKE_CHANGES_IN_TASKS, COMMUNITIES, OPTIONS, \
    WHATS_NEW_TODAY, MORE_ABOUT_SCHOOL_TASKER, MAKE_CHANGES_IN_COMMUNITY
from school_tasker.screens.base import base_screen
from utils import get_username, get_greet, get_clean_var


LOGGER = getLogger('hammett')


class MainMenu(StartMixin, base_screen.BaseScreen):

    async def get_config(self, update, context, **_kwargs):
        from school_tasker.screens import communitites_main
        from school_tasker.screens import options
        from school_tasker.screens import social_media
        from school_tasker.screens import whats_new
        user_id = update.effective_user.id
        config = RenderConfig()
        user_name = get_username(update.effective_user.first_name, update.effective_user.last_name,
                                 update.effective_user.username)
        try:
            cursor.execute(
            #     # создать модуль например db_api.py и в нем создать функции-ручки (публичный интерфейс) (например, def create_user)
            #     # для разделения абстракции обращения к базе данных и логики отображения компонентов экрана
                'INSERT INTO Users (send_notification, id, name) '
                'VALUES'
                '(%s,%s,%s)',
                (1, str(user_id), user_name))
            connection.commit()
            config.description = FIRST_GREET[randint(0, 2)]
        except IntegrityError or AttributeError:
            connection.rollback()
            cursor.execute("UPDATE Users SET name = %s WHERE id = %s", (user_name, user_id,))
            connection.commit()
            config.description = get_greet(user_name)
        config.keyboard = []
        cursor.execute('SELECT COUNT(*) FROM UserCommunities WHERE user_id = %s', (update.effective_user.id,))
        db_length = cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            config.keyboard.append([Button(ENTER_TO_TASKS, self.check_class_name_watch,
                                           source_type=SourceTypes.HANDLER_SOURCE_TYPE), ])
        cursor.execute(
            "SELECT COUNT(*) FROM UserCommunities WHERE user_id = %s AND user_role_in_class IN ('ADMIN', 'HOST')",
            (update.effective_user.id,))
        db_length = cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            config.keyboard.append([
                Button(MAKE_CHANGES_IN_TASKS, self.check_class_name_tasks,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE)])
        cursor.execute("SELECT COUNT(*) FROM UserCommunities WHERE user_id = %s AND user_role_in_class = 'HOST'",
                       (update.effective_user.id,))
        db_length = cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            config.keyboard.append([
                Button(MAKE_CHANGES_IN_COMMUNITY, self.check_class_name_manage,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ])
        config.keyboard.append([Button(COMMUNITIES, communitites_main.CommunitiesMain,
                                       source_type=SourceTypes.MOVE_SOURCE_TYPE)])
        config.keyboard.append([Button(OPTIONS, options.Options,
                                       source_type=SourceTypes.MOVE_SOURCE_TYPE)])
        config.keyboard.append([Button(WHATS_NEW_TODAY, whats_new.WhatsNew,
                                       source_type=SourceTypes.MOVE_SOURCE_TYPE)])
        config.keyboard.append([Button(MORE_ABOUT_SCHOOL_TASKER, social_media.SocialMedia,
                                       source_type=SourceTypes.MOVE_SOURCE_TYPE)])
        return config

    @register_button_handler
    async def check_class_name_watch(self, update, context):
        from school_tasker.screens import community_selection_to_watch
        from school_tasker.screens import school_tasks
        cursor.execute("SELECT COUNT(*) FROM UserCommunities WHERE user_id = %s", (update.effective_user.id,))
        db_length = cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length == 1:
            cursor.execute('SELECT class_name FROM UserCommunities WHERE user_id = %s',
                           (update.effective_user.id,))
            context.user_data['CURRENT_CLASS_NAME'] = cursor.fetchall()
            context.user_data['CURRENT_CLASS_NAME'] = \
                get_clean_var(context.user_data['CURRENT_CLASS_NAME'], 'to_string', 0, True)
            st_screen = school_tasks.SchoolTasks()
            st_screen.back_button.caption = BUTTON_BACK_TO_MENU
            st_screen.back_button.source = MainMenu
            await st_screen.check_tasks(update, context, school_tasks.SchoolTasks)
        elif db_length > 1:
            return await community_selection_to_watch.CommunitySelectionToWatch().move(update, context)

    @register_button_handler
    async def check_class_name_tasks(self, update, context):
        from school_tasker.screens import community_selection_to_tasks
        from school_tasker.screens import school_task_management_main
        cursor.execute(
            "SELECT COUNT(*) FROM UserCommunities WHERE user_id = %s AND user_role_in_class IN ('ADMIN', 'HOST')",
            (update.effective_user.id,))
        db_length = cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length == 1:
            cursor.execute(
                "SELECT class_name FROM UserCommunities WHERE user_id = %s AND user_role_in_class IN ('ADMIN', 'HOST')",
                (update.effective_user.id,))
            context.user_data['CURRENT_CLASS_NAME'] = cursor.fetchall()
            context.user_data['CURRENT_CLASS_NAME'] = \
                get_clean_var(context.user_data['CURRENT_CLASS_NAME'], 'to_string', 0, True)
            return await school_task_management_main.SchoolTaskManagementMain().move(update, context)
        elif db_length > 1:
            return await community_selection_to_tasks.CommunitySelectionToTasks().move(update, context)

    @register_button_handler
    async def check_class_name_manage(self, update, context):
        from school_tasker.screens import community_management_main
        from school_tasker.screens import community_selection_to_manage
        cursor.execute("SELECT COUNT(*) FROM UserCommunities WHERE user_id = %s AND user_role_in_class = 'HOST'",
                       (update.effective_user.id,))
        db_length = cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length == 1:
            cursor.execute(
                "SELECT class_name FROM UserCommunities WHERE user_id = %s AND user_role_in_class  = 'HOST'",
                (update.effective_user.id,))
            context.user_data['CURRENT_CLASS_NAME'] = cursor.fetchall()
            context.user_data['CURRENT_CLASS_NAME'] = \
                get_clean_var(context.user_data['CURRENT_CLASS_NAME'], 'to_string', 0, True)
            return await community_management_main.CommunityManagementMain().move(update, context)
        elif db_length > 1:
            return await community_selection_to_manage.CommunitySelectionToManage().move(update, context)

    @register_button_handler
    async def school_tasks(self, update, context):
        from school_tasker.screens import school_tasks
        await school_tasks.SchoolTasks().check_tasks(update, context, school_tasks.SchoolTasks)

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
