from datetime import datetime
from json import dumps

from hammett.core import Button
from hammett.core.constants import SourceTypes, DEFAULT_STATE
from hammett.core.handlers import register_button_handler
from hammett.core.mixins import RouteMixin

from captions import BUTTON_BACK, ON_WHICH_MONTH_WILL_BE_TASK
from constants import MONTHS_DICT
from school_tasker.screens.base import base_screen
from states import ADDING_TASK
from utils import get_payload_safe


class SchoolTaskAdditionDetailsMonth(base_screen.BaseScreen, RouteMixin):
    routes = (
        ({ADDING_TASK}, DEFAULT_STATE),
    )
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
        from school_tasker.screens import school_task_addition_detail_day
        await get_payload_safe(self, update, context, 'get_month_add_task', 'ADDING_TASK_TASK_MONTH')
        return await school_task_addition_detail_day.SchoolTaskAdditionDetailsDay().move(update, context)
