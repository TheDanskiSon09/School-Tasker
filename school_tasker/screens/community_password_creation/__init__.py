from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

from constants import BUTTON_BACK, ENTER_PASSWORD_OF_YOUR_COMMUNITY
from school_tasker.screens.base import base_screen


class CommunityPasswordCreation(base_screen.BaseScreen):
    description = ENTER_PASSWORD_OF_YOUR_COMMUNITY

    async def add_default_keyboard(self, update, context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, update, context):
        from school_tasker.screens import community_name_creation
        context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_CLASS'
        return await community_name_creation.CommunityNameCreation().move(update, context)