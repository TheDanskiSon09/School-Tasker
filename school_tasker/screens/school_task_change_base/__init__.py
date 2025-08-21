from json import dumps

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from constants import BUTTON_BACK, WHAT_YOU_WANT_TO_CHANGE_IN_THIS_TASK
from school_tasker.screens.base import base_screen
from utils import get_clean_var, get_payload_safe


class SchoolTaskChangeBase(base_screen.BaseScreen):
    description = WHAT_YOU_WANT_TO_CHANGE_IN_THIS_TASK

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import school_task_change_group_number
        from school_tasker.screens import school_task_change_main
        check_index = context.user_data["task_index"]
        check_item = await backend.get_var_from_database(check_index, "item_name", True, context)
        keyboard = [
            [
                Button("Предмет", self.change_school_item,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"task_index": context.user_data['task_index']}))
            ],
            [
                Button("Задание", self.change_school_task,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"deletion_index": context.user_data['task_index']}))
            ],
            [
                Button("День", self.change_task_day,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"deletion_index": context.user_data['task_index']}))
            ],
            [
                Button("Месяц", self.change_task_month,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"deletion_index": context.user_data['task_index']}))
            ],
            [
                Button(BUTTON_BACK, school_task_change_main.SchoolTaskChangeMain,
                       source_type=SourceTypes.MOVE_SOURCE_TYPE)
            ]
        ]
        groups = await backend.execute_query('SELECT groups_list FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
            (check_item,))
        # backend.cursor.execute(
        #     'SELECT groups_list FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
        #     (check_item,))
        # groups = backend.cursor.fetchall()
        groups = get_clean_var(groups, 'to_string', 0, True)
        if int(groups) > 1:
            keyboard.insert(2, [
                Button("Группу", school_task_change_group_number.SchoolTaskChangeGroupNumber,
                       source_type=SourceTypes.MOVE_SOURCE_TYPE)
            ])
        return keyboard

    @register_button_handler
    async def change_task_month(self, update, context):
        from school_tasker.screens import school_task_month_change
        return await school_task_month_change.SchoolTaskMonthChange().move(update, context)

    @register_button_handler
    async def change_task_day(self, update, context):
        from school_tasker.screens import school_task_change_day
        return await school_task_change_day.SchoolTaskChangeDay().move(update, context)

    @register_button_handler
    async def change_school_task(self, update, context):
        from school_tasker.screens import school_task_change_task
        return await school_task_change_task.SchoolTaskChangeTask().move(update, context)

    @register_button_handler
    async def change_school_item(self, update, context):
        from school_tasker.screens import school_task_change_item
        await get_payload_safe(self, update, context, 'change_task_item', 'task_index')
        return await school_task_change_item.SchoolTaskChangeItem().move(update, context)