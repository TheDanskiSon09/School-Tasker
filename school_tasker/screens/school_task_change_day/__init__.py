from calendar import monthrange
from datetime import datetime
from json import dumps
from time import strftime, gmtime

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from constants import BUTTON_BACK, ON_WHICH_DAY_WILL_BE_TASK
from school_tasker.screens.base import base_screen
from utils import get_payload_safe, get_clean_var


class SchoolTaskChangeDay(base_screen.BaseScreen):
    description = ON_WHICH_DAY_WILL_BE_TASK

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import school_task_addition_details_month
        keyboard = []
        for day in range(
                int(monthrange(int(strftime("%Y", gmtime())), int(context.user_data["ADDING_TASK_TASK_MONTH"]))[1])):
            real_day = day + 1
            if int(context.user_data["ADDING_TASK_TASK_MONTH"]) == datetime.now().month:
                if real_day > datetime.now().day:
                    keyboard.append([Button(str(real_day), self.get_day,
                                            source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                                            payload=dumps({'ADDING_TASK_TASK_DAY': real_day}))])
            else:
                keyboard.append([Button(str(real_day), self.get_day,
                                        source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                                        payload=dumps({'ADDING_TASK_TASK_DAY': real_day}))])
        keyboard.append([Button(BUTTON_BACK, school_task_addition_details_month.SchoolTaskAdditionDetailsMonth,
                                source_type=SourceTypes.MOVE_SOURCE_TYPE)])
        return keyboard

    @register_button_handler
    async def get_day(self, update, context):
        await get_payload_safe(self, update, context, 'get_day_add_task', 'ADDING_TASK_TASK_DAY')
        backend.cursor.execute(
            'UPDATE ' + context.user_data[
                'CURRENT_CLASS_NAME'] + '_Tasks SET task_day = %s WHERE item_index = %s',
            (context.user_data['ADDING_TASK_TASK_DAY'], context.user_data['ADDING_TASK_INDEX'],))
        backend.connection.commit()
        backend.cursor.execute(
            'SELECT item_name FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
            (context.user_data['ADDING_TASK_INDEX'],))
        item_name = backend.cursor.fetchall()
        item_name = get_clean_var(item_name, 'to_string', 0, True)
        backend.cursor.execute(
            'SELECT item_index FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
            (item_name,))
        context.user_data['ADDING_TASK_INDEX'] = backend.cursor.fetchall()
        context.user_data['ADDING_TASK_INDEX'] = get_clean_var(context.user_data['ADDING_TASK_INDEX'],
                                                                'to_string', 0, True)
        return await backend.send_update_notification(update, context, 'change',
                                              context.user_data['ADDING_TASK_INDEX'],
                                              True)