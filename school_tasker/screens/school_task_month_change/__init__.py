from datetime import datetime
from json import dumps

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from constants import MONTHS_DICT, BUTTON_BACK, ON_WHICH_MONTH_WILL_BE_TASK, I_CANT_MAKE_YOUR_REQUEST, MAKE_ANOTHER_TRY
from school_tasker.screens.base import base_screen
from utils import get_payload_safe, get_clean_var


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
                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                       ],
                                                      [Button(BUTTON_BACK, school_task_management_main.SchoolTaskManagementMain,
                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                       ]])
        else:
            await backend.execute_query('UPDATE ' + context.user_data[
                    'CURRENT_CLASS_NAME'] + '_Tasks SET task_month = %s WHERE item_index = %s',
                (context.user_data['ADDING_TASK_TASK_MONTH'], context.user_data['ADDING_TASK_INDEX'],))
            # backend.cursor.execute(
            #     'UPDATE ' + context.user_data[
            #         'CURRENT_CLASS_NAME'] + '_Tasks SET task_month = %s WHERE item_index = %s',
            #     (context.user_data['ADDING_TASK_TASK_MONTH'], context.user_data['ADDING_TASK_INDEX'],))
            # backend.connection.commit()
            item_name = await backend.execute_query('SELECT item_name FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
                (context.user_data['ADDING_TASK_INDEX'],))
            # backend.cursor.execute(
            #     'SELECT item_name FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
            #     (context.user_data['ADDING_TASK_INDEX'],))
            # item_name = backend.cursor.fetchall()
            item_name = get_clean_var(item_name, 'to_string', 0, True)
            context.user_data['ADDING_TASK_INDEX'] = await backend.execute_query('SELECT item_index FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
                (item_name,))
            # backend.cursor.execute(
            #     'SELECT item_index FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
            #     (item_name,))
            # context.user_data['ADDING_TASK_INDEX'] = backend.cursor.fetchall()
            context.user_data['ADDING_TASK_INDEX'] = get_clean_var(context.user_data['ADDING_TASK_INDEX'],
                                                                    'to_string', 0, True)
            return await backend.send_update_notification(update, context, 'change', context.user_data['ADDING_TASK_INDEX'],
                                                  True)
