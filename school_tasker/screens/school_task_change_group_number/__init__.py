from json import dumps

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from constants import BUTTON_BACK, WHICH_GROUP_WILL_BE_TASK
from school_tasker.screens.base import base_screen
from utils import get_payload_safe, get_clean_var


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
        await backend.execute_query('UPDATE ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks SET group_number = %s WHERE item_index = %s',
            (context.user_data['ADDING_TASK_GROUP_NUMBER'], context.user_data['ADDING_TASK_INDEX'],))
        # backend.cursor.execute(
        #     'UPDATE ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks SET group_number = %s WHERE item_index = %s',
        #     (context.user_data['ADDING_TASK_GROUP_NUMBER'], context.user_data['ADDING_TASK_INDEX'],))
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

    @register_button_handler
    async def return_back(self, update, context):
        from school_tasker.screens import school_task_change_base
        return await school_task_change_base.SchoolTaskChangeBase().move(update, context)
