from json import dumps

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

from constants import BUTTON_BACK, WHICH_GROUP_WILL_BE_TASK
from school_tasker.screens.base import base_screen
from utils import get_payload_safe


class SchoolTaskAdditionGroupNumber(base_screen.BaseScreen):
    description = WHICH_GROUP_WILL_BE_TASK

    async def add_default_keyboard(self, update, _context):
        from school_tasker.screens import school_task_addition
        keyboard = []
        for i in range(int(_context.user_data['ADDING_TASK_GROUPS'])):
            keyboard.append([Button('Группа ' + str(i + 1), self.get_group_number,
                                    source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                                    payload=dumps({'ADDING_TASK_GROUP_NUMBER': str(i + 1)}))])
        keyboard.append(
            [Button(BUTTON_BACK, school_task_addition.SchoolTaskAddition, source_type=SourceTypes.MOVE_SOURCE_TYPE)])
        return keyboard

    @register_button_handler
    async def get_group_number(self, update, _context):
        from school_tasker.screens import school_task_addition_details
        await get_payload_safe(self, update, _context, 'add_task_group_number', 'ADDING_TASK_GROUP_NUMBER')
        _context.user_data['CURRENT_TYPING_ACTION'] = 'ADDING_TASK'
        return await school_task_addition_details.SchoolTaskAdditionDetails().move(update, _context)

    @register_button_handler
    async def return_back(self, update, _context):
        from school_tasker.screens import school_task_addition
        return await school_task_addition.SchoolTaskAddition().move(update, _context)
