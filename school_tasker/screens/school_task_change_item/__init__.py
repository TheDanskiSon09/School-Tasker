from json import dumps

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from captions import (
    BUTTON_BACK,
    BUTTON_BACK_TO_MENU,
    CHANGE_MORE_TASKS,
    I_CANT_MAKE_YOUR_REQUEST,
    MAKE_ANOTHER_TRY,
    TASK_WAS_SUCCESSFULLY_CHANGED,
    THERE_IS_NO_ITEMS_IN_COMMUNITY,
    TO_THE_REDACTOR_MENU,
    WHICH_ITEM_WILL_BE_TASK,
)
from school_tasker.screens.base import base_screen
from utils import get_clean_var, get_payload_safe


class SchoolTaskChangeItem(base_screen.BaseScreen):

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
            for i in range(db_length):
                main_name = get_clean_var(main_name_list, 'to_string', i, True)
                emoji = await backend.get_emoji_of_class_item(context, main_name)
                emoji = get_clean_var(emoji, 'to_string', 0, True)
                keyboard.append([Button(emoji + main_name, self.change_item,
                                        source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                                        payload=dumps({'task_item': main_name}))])
        keyboard.append([Button(BUTTON_BACK, school_task_management_main.SchoolTaskManagementMain,
                                source_type=SourceTypes.MOVE_SOURCE_TYPE)])
        return keyboard

    @register_button_handler
    async def change_item(self, update, context):
        from school_tasker.screens import school_task_change_main, school_task_management_main
        check_task = await backend.check_task_status(context)
        if not check_task:
            return await backend.show_notification_screen(update, context, 'render',
                                                  I_CANT_MAKE_YOUR_REQUEST,
                                                  [
                                                      [Button(MAKE_ANOTHER_TRY, school_task_management_main.SchoolTaskManagementMain,
                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                       ],
                                                      [Button(BUTTON_BACK, school_task_management_main.SchoolTaskManagementMain,
                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                       ]])
        else:
            from school_tasker.screens import main_menu
            await get_payload_safe(self, update, context, 'change_task_item', 'task_item')
            await backend.update_item_name_of_task(context)
            await backend.send_update_notification(update, context, 'change', context.user_data['task_index'], False, 'change')
            return await backend.show_notification_screen(update, context, 'render',
                                                  TASK_WAS_SUCCESSFULLY_CHANGED, [
                                                      [Button(TO_THE_REDACTOR_MENU, school_task_management_main.SchoolTaskManagementMain,
                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE)],
                                                      [Button(CHANGE_MORE_TASKS, school_task_change_main.SchoolTaskChangeMain,
                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE)],
                                                      [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE)]])
