from json import dumps

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from constants import BUTTON_BACK_TO_MENU, SELECT_ONE_OF_COMMUNITIES, YOU_IN_NO_COMMUNITY_FOR_NOW
from school_tasker.screens.base import base_screen
from utils import get_clean_var, get_payload_safe


class CommunitySelectionToTasks(base_screen.BaseScreen):
    async def get_description(self, update, context):
        backend.cursor.execute(
            "SELECT COUNT(*) FROM UserCommunities WHERE user_id = %s AND user_role_in_class IN ('ADMIN', 'HOST')",
            (update.effective_user.id,))
        db_length = backend.cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            return SELECT_ONE_OF_COMMUNITIES
        else:
            return YOU_IN_NO_COMMUNITY_FOR_NOW

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import main_menu
        keyboard = []
        backend.cursor.execute(
            'SELECT class_name FROM UserCommunities WHERE user_id = %s AND user_role_in_class IN ("ADMIN", "HOST")',
            (update.effective_user.id,))
        class_name_list = backend.cursor.fetchall()
        backend.cursor.execute(
            'SELECT COUNT(*) FROM UserCommunities WHERE user_id = %s AND user_role_in_class IN ("ADMIN", "HOST")',
            (update.effective_user.id,))
        db_length = backend.cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            for i in range(db_length):
                new_name = get_clean_var(class_name_list, 'to_string', i - 1, True)
                new_button = [Button(new_name, self.press_button,
                                     source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                                     payload=dumps({"CURRENT_CLASS_NAME": new_name}))]
                keyboard.append(new_button)
        keyboard.append([Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                source_type=SourceTypes.MOVE_SOURCE_TYPE)])
        return keyboard

    @register_button_handler
    async def press_button(self, update, context):
        from school_tasker.screens import school_task_management_main
        await get_payload_safe(self, update, context, 'MANAGE_TASKS_FOR_CURRENT_CLASS_NAME', 'CURRENT_CLASS_NAME')
        return await school_task_management_main.SchoolTaskManagementMain().move(update, context)