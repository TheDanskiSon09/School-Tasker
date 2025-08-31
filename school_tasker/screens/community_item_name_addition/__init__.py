from hammett.core import Button
from hammett.core.constants import SourceTypes, DEFAULT_STATE
from hammett.core.handlers import register_button_handler, register_typing_handler
from hammett.core.mixins import RouteMixin

from captions import BUTTON_BACK, ENTER_ITEM_NAME
from school_tasker.screens import community_item_rod_name_addition
from school_tasker.screens.base import base_screen
from states import CREATING_ITEM_NAME


class CommunityItemNameAddition(base_screen.BaseScreen, RouteMixin):
    routes = (
        ({DEFAULT_STATE}, CREATING_ITEM_NAME),
    )
    description = ENTER_ITEM_NAME

    async def add_default_keyboard(self, update, context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def go_back(self, update, context):
        context.user_data['CURRENT_TYPING_ACTION'] = ''
        from school_tasker.screens import community_item_management
        return await community_item_management.CommunityItemManagement().move(update, context)

    @register_typing_handler
    async def handle_message(self, update, context):
        context.user_data['CREATING_ITEM_NAME'] = update.message.text
        context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_ITEM_ROD_NAME'
        return await community_item_rod_name_addition.CommunityItemRodNameAddition().jump_along_route(update, context)
