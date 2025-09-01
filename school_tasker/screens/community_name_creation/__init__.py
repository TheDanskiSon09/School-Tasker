from hammett.core import Button
from hammett.core.constants import SourceTypes, DEFAULT_STATE
from hammett.core.handlers import register_button_handler, register_typing_handler
from hammett.core.mixins import RouteMixin

from captions import BUTTON_BACK, ENTER_NAME_OF_YOUR_COMMUNITY
from school_tasker.screens import community_password_creation
from school_tasker.screens.base import base_screen
from states import CREATING_CLASS


class CommunityNameCreation(base_screen.BaseScreen, RouteMixin):
    routes = (
        ({DEFAULT_STATE}, CREATING_CLASS),
    )

    description = ENTER_NAME_OF_YOUR_COMMUNITY

    async def add_default_keyboard(self, update, context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def go_back(self, update, context):
        from school_tasker.screens import communitites_main
        return await communitites_main.CommunitiesMain().move(update, context)


    @register_typing_handler
    async def handle_message(self, update, context):
        context.user_data['CURRENT_CLASS_NAME'] = update.message.text
        context.user_data['CURRENT_CLASS_NAME'] = context.user_data['CURRENT_CLASS_NAME'].replace(' ', '')
        return await community_password_creation.CommunityPasswordCreation().jump_along_route(update, context)
