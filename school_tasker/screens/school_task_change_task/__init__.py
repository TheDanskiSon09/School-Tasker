from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

from constants import BUTTON_BACK, ENTER_NEW_TASK_TEXT
from school_tasker.screens.base import base_screen
from utils import get_payload_safe


class SchoolTaskChangeTask(base_screen.BaseScreen):
    description = ENTER_NEW_TASK_TEXT
    current_index = int()
    task_description = str()

    async def add_default_keyboard(self, update, context):
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_TASK_DESCRIPTION'
        await get_payload_safe(self, update, context, 'change_task_description', 'deletion_index')
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, update, context):
        from school_tasker.screens import school_task_change_base
        context.user_data['CURRENT_TYPING_ACTION'] = ''
        return await school_task_change_base.SchoolTaskChangeBase().move(update, context)