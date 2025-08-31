from json import dumps

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from captions import BUTTON_BACK, THERE_IS_NO_ITEMS_IN_COMMUNITY, WHICH_ITEM_WILL_BE_TASK
from school_tasker.screens.base import base_screen
from utils import get_clean_var, get_payload_safe


class SchoolTaskAddition(base_screen.BaseScreen):

    async def get_description(self, update, context):
        db_length = await backend.get_count_of_class_items(context)
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            return WHICH_ITEM_WILL_BE_TASK
        else:
            return THERE_IS_NO_ITEMS_IN_COMMUNITY

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import school_task_management_main
        keyboard = []
        db_length = await backend.get_count_of_class_items(context)
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            main_name_list = await backend.get_main_name_of_class_item(context)

            item_index_list = await backend.get_item_index_of_class_item(context)
            groups_list = await backend.get_group_of_class_item(context)
            emoji_list = await backend.get_emoji_of_class_item(context)
            for i in range(db_length):
                main_name = get_clean_var(main_name_list, 'to_string', i - 1, True)
                item_index = get_clean_var(item_index_list, 'to_string', i - 1, True)
                groups = get_clean_var(groups_list, 'to_string', i - 1, True)
                emoji = get_clean_var(emoji_list, 'to_string', i - 1, True)
                keyboard.append([Button(emoji + main_name, self.get_school_item,
                                        source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                                        payload=dumps({'ADDING_TASK_NAME': main_name,
                                                       'ADDING_TASK_INDEX': item_index,
                                                       'ADDING_TASK_GROUPS': groups}))])
        keyboard.append([Button(BUTTON_BACK, school_task_management_main.SchoolTaskManagementMain,
                                source_type=SourceTypes.MOVE_SOURCE_TYPE)])
        return keyboard

    @register_button_handler
    async def get_school_item(self, update, context):
        from school_tasker.screens import (
            school_task_addition_details,
            school_task_addition_group_number,
        )
        await get_payload_safe(self, update, context, 'add_task_item', 'ADDING_TASK_NAME')
        await get_payload_safe(self, update, context, 'add_task_item', 'ADDING_TASK_GROUPS')
        await get_payload_safe(self, update, context, 'add_task_item', 'ADDING_TASK_INDEX')
        if int(context.user_data['ADDING_TASK_GROUPS']) > 1:
            return await school_task_addition_group_number.SchoolTaskAdditionGroupNumber().move(update, context)
        else:
            # context.user_data['CURRENT_TYPING_ACTION'] = 'ADDING_TASK'
            return await school_task_addition_details.SchoolTaskAdditionDetails().move_along_route(update, context)
