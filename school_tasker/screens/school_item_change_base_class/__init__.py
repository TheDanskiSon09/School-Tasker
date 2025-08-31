from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

from captions import BUTTON_BACK
from school_tasker.screens.base import base_screen


class SchoolItemChangeBaseClass(base_screen.BaseScreen):

    async def add_default_keyboard(self, update, context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def go_back(self, update, context):
        from school_tasker.screens import school_item_management
        context.user_data['CURRENT_TYPING_ACTION'] = ''
        return await school_item_management.SchoolItemManagement().move(update, context)
