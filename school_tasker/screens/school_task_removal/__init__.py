from contextlib import suppress
from json import dumps

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from captions import (
    BUTTON_BACK,
    THERE_IS_NO_SCHOOL_TASKS_FOR_NOW,
    WHICH_FROM_THIS_TASKS_YOU_WANT_TO_DELETE,
)
from school_tasker.screens.base import base_screen
from utils import get_clean_var, get_payload_safe


class SchoolTaskRemoval(base_screen.BaseScreen):

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import school_task_management_main
        db_check = await backend.get_all_from_community_task(context)
        try:
            db_check = get_clean_var(db_check, 'to_string', False, True)
        except IndexError:
            db_check = ''
        db_length = await backend.get_count_of_community_tasks(context)
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        keyboard = []
        for task_index in range(db_length):
            with suppress(KeyError):
                button_name = await backend.get_button_title(task_index, context)
                button_list = [
                    Button(
                        str(button_name), self.remove_task,
                        source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                        payload=dumps({'task_index': task_index,
                                       'db_check': db_check}),
                    ),
                ]
                keyboard.append(button_list)
        exit_button = [Button(BUTTON_BACK, school_task_management_main.SchoolTaskManagementMain,
                              source_type=SourceTypes.MOVE_SOURCE_TYPE)]
        keyboard.append(exit_button)
        return keyboard

    async def get_description(self, update, context):
        from school_tasker.screens import school_tasks
        await school_tasks.SchoolTasks().check_tasks(update, context, None)
        database_length = await backend.get_var_from_database(None, 'database_length_SchoolTasker', True, context)
        if database_length >= 1:
            return WHICH_FROM_THIS_TASKS_YOU_WANT_TO_DELETE
        else:
            return THERE_IS_NO_SCHOOL_TASKS_FOR_NOW

    @register_button_handler
    async def remove_task(self, update, context):
        from school_tasker.screens import school_task_removal_confirmation
        await get_payload_safe(self, update, context, 'delete_task', 'task_index')
        await get_payload_safe(self, update, context, 'delete_task', 'db_check')
        return await school_task_removal_confirmation.SchoolTaskRemovalConfirmation().move(update, context)
