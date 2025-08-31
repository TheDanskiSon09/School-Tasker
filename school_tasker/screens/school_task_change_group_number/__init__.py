from json import dumps

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from captions import BUTTON_BACK, WHICH_GROUP_WILL_BE_TASK
from school_tasker.screens.base import base_screen
from utils import get_clean_var, get_payload_safe


class SchoolTaskChangeGroupNumber(base_screen.BaseScreen):
    description = WHICH_GROUP_WILL_BE_TASK

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import school_task_addition
        keyboard = []
        for i in range(int(context.user_data['ADDING_TASK_GROUPS'])):
            keyboard.append([Button('Группа ' + str(i + 1), self.get_group_number,
                                    source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                                    payload=dumps({'ADDING_TASK_GROUP_NUMBER': str(i + 1)}))])
        keyboard.append([Button(BUTTON_BACK, school_task_addition.SchoolTaskAddition,
                                source_type=SourceTypes.MOVE_SOURCE_TYPE)])
        return keyboard

    @register_button_handler
    async def get_group_number(self, update, context):
        await get_payload_safe(self, update, context, 'add_task_group_number', 'ADDING_TASK_GROUP_NUMBER')
        await backend.update_community_task_set_group_number_by_index(context)
        item_name = await backend.get_item_name_from_community_tasks_by_index(context, context.user_data['ADDING_TASK_INDEX'])
        item_name = get_clean_var(item_name, 'to_string', 0, True)
        context.user_data['ADDING_TASK_NAME'] = item_name
        context.user_data['ADDING_TASK_INDEX'] = await backend.get_item_index_from_community_items_by_main_name(context, item_name)
        context.user_data['ADDING_TASK_INDEX'] = get_clean_var(context.user_data['ADDING_TASK_INDEX'],
                                                               'to_string', 0, True)
        return await backend.send_update_notification(update, context, 'change', context.user_data['ADDING_TASK_INDEX'],
                                                      True, 'change')

    @register_button_handler
    async def return_back(self, update, context):
        from school_tasker.screens import school_task_change_base
        return await school_task_change_base.SchoolTaskChangeBase().move(update, context)
