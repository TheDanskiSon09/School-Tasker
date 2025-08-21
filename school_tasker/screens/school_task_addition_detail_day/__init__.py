from calendar import monthrange
from datetime import datetime
from json import dumps
from time import strftime, gmtime

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

from constants import BUTTON_BACK, ON_WHICH_DAY_WILL_BE_TASK
from school_tasker.screens.base import base_screen
from utils import get_payload_safe


class SchoolTaskAdditionDetailsDay(base_screen.BaseScreen):
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
        from school_tasker.screens import media_capture
        await get_payload_safe(self, update, context, 'get_day_add_task', 'ADDING_TASK_TASK_DAY')
        context.user_data["IS_IN_MEDIA_SCREEN"] = True
        context.user_data['ADDING_TASK_TASK_YEAR'] = datetime.now().year
        return await media_capture.MediaCapture().move(update, context)