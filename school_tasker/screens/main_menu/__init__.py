import logging
from random import randint

from hammett.core import Button
from hammett.core.constants import RenderConfig, SourceTypes
from hammett.core.handlers import register_button_handler
from hammett.core.mixins import StartMixin

import backend
from captions import (
    COMMUNITIES,
    ENTER_TO_TASKS,
    MAKE_CHANGES_IN_COMMUNITY,
    MAKE_CHANGES_IN_TASKS,
    MORE_ABOUT_SCHOOL_TASKER,
    OPTIONS,
    WHATS_NEW_TODAY,
)
from constants import FIRST_GREET
from school_tasker.screens.base import base_screen
from utils import get_clean_var, get_greet, get_username

LOGGER = logging.getLogger('hammett')


class MainMenu(StartMixin, base_screen.BaseScreen):

    async def get_config(self, update, context, **_kwargs):
        from school_tasker.screens import communitites_main, options, social_media, whats_new
        user_id = update.effective_user.id
        config = RenderConfig()
        user_name = get_username(update.effective_user.first_name, update.effective_user.last_name,
                                 update.effective_user.username)
        config.description = await backend.add_or_update_user(user_id, user_name, FIRST_GREET[randint(0, 2)],
                                                              get_greet(user_name))
        config.keyboard = []
        db_length = await backend.get_count_of_user_communities_by_user_id(update)
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            config.keyboard.append([Button(ENTER_TO_TASKS, self.check_class_name_watch,
                                           source_type=SourceTypes.HANDLER_SOURCE_TYPE) ])
        db_length = await backend.get_count_of_user_communities_where_user_is_host_or_admin(update)
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            config.keyboard.append([
                Button(MAKE_CHANGES_IN_TASKS, self.check_class_name_tasks,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE)])
        db_length = await backend.get_count_of_user_communities_where_user_is_host_or_admin(update)
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
        from school_tasker.screens import community_selection_to_watch, school_tasks
        db_length = await backend.get_count_of_user_communities_by_id(update)
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length == 1:
            context.user_data['CURRENT_CLASS_NAME'] = await backend.get_class_name_from_user_community_by_id(update)
            context.user_data['CURRENT_CLASS_NAME'] = \
                get_clean_var(context.user_data['CURRENT_CLASS_NAME'], 'to_string', 0, True)
            st_screen = school_tasks.SchoolTasks()
            await st_screen.check_tasks(update, context, school_tasks.SchoolTasks)
        elif db_length > 1:
            return await community_selection_to_watch.CommunitySelectionToWatch().move(update, context)

    @register_button_handler
    async def check_class_name_tasks(self, update, context):
        from school_tasker.screens import community_selection_to_tasks, school_task_management_main
        db_length = await backend.get_count_of_user_communities_where_user_is_host_or_admin(update)
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length == 1:
            context.user_data['CURRENT_CLASS_NAME'] = await backend.get_class_name_of_user_communities_where_user_is_host_or_admin(update)
            context.user_data['CURRENT_CLASS_NAME'] = \
                get_clean_var(context.user_data['CURRENT_CLASS_NAME'], 'to_string', 0, True)
            return await school_task_management_main.SchoolTaskManagementMain().move(update, context)
        elif db_length > 1:
            return await community_selection_to_tasks.CommunitySelectionToTasks().move(update, context)

    @register_button_handler
    async def check_class_name_manage(self, update, context):
        from school_tasker.screens import community_management_main, community_selection_to_manage
        db_length = await backend.get_count_of_user_communities_by_user_id_where_user_is_host(update)
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length == 1:
            context.user_data['CURRENT_CLASS_NAME'] = await backend.get_class_name_of_user_communities_by_user_id_where_user_is_host(update)
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
        """Replies to the /start command."""
        try:
            user = update.message.from_user
        except AttributeError:
            user = update.edited_message.from_user
        user_name = get_username(user.first_name, user.last_name, user.username)
        LOGGER.info('The user %s (%s) was entered to School Tasker', user_name, user.id)
        return await super().start(update, context)
