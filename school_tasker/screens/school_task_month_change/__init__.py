from datetime import datetime
from json import dumps

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from captions import (
    BUTTON_BACK,
    I_CANT_MAKE_YOUR_REQUEST,
    MAKE_ANOTHER_TRY,
    ON_WHICH_MONTH_WILL_BE_TASK,
)
from constants import MONTHS_DICT
from school_tasker.screens.base import base_screen
from utils import get_clean_var, get_payload_safe


class SchoolTaskMonthChange(base_screen.BaseScreen):
    description = ON_WHICH_MONTH_WILL_BE_TASK

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import school_task_addition_details
        keyboard = []
        for month in range(12):
            real_month = month + 1
            if real_month >= datetime.now().month:
                keyboard.append([Button(MONTHS_DICT[real_month], self.get_month,
                                        source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                                        payload=dumps({'ADDING_TASK_TASK_MONTH': int(real_month)}))])
        keyboard.append([Button(BUTTON_BACK, school_task_addition_details.SchoolTaskAdditionDetails,
                                source_type=SourceTypes.MOVE_SOURCE_TYPE)])
        return keyboard

    @register_button_handler
    async def get_month(self, update, context):
        from school_tasker.screens import school_task_management_main
        await get_payload_safe(self, update, context, 'get_month_add_task', 'ADDING_TASK_TASK_MONTH')
        check_task = await backend.check_task_status(context)
        if not check_task:
            return await backend.show_notification_screen(update, context, 'send',
                                                  I_CANT_MAKE_YOUR_REQUEST,
                                                  [
                                                      [Button(MAKE_ANOTHER_TRY, school_task_management_main.SchoolTaskManagementMain,
                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                       ],
                                                      [Button(BUTTON_BACK, school_task_management_main.SchoolTaskManagementMain,
                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                       ]])
        else:
            await backend.update_community_tasks_set_task_month_by_index(context)
            item_name = await backend.get_item_name_from_community_task_by_index(context)
            item_name = get_clean_var(item_name, 'to_string', 0, True)
            context.user_data['ADDING_TASK_NAME'] = item_name
            context.user_data['ADDING_TASK_INDEX'] = await backend.get_item_index_from_community_items_by_index(context, item_name)
            context.user_data['ADDING_TASK_INDEX'] = get_clean_var(context.user_data['ADDING_TASK_INDEX'],
                                                                    'to_string', 0, True)
            return await backend.send_update_notification(update, context, 'change', context.user_data['ADDING_TASK_INDEX'],
                                                  True, 'change')
