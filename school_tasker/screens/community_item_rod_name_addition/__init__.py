from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler, register_typing_handler
from hammett.core.mixins import RouteMixin

from captions import BUTTON_BACK, ENTER_ITEM_ROD_NAME
from school_tasker.screens import community_item_group_addition
from school_tasker.screens.base import base_screen
from states import CREATING_ITEM_ROD_NAME, CREATING_ITEM_NAME


class CommunityItemRodNameAddition(base_screen.BaseScreen, RouteMixin):
    routes = (
        ({CREATING_ITEM_NAME}, CREATING_ITEM_ROD_NAME),
    )
    description = ENTER_ITEM_ROD_NAME

    async def add_default_keyboard(self, update, context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def go_back(self, update, context):
        from school_tasker.screens import community_item_name_addition
        context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_ITEM_NAME'
        return await community_item_name_addition.CommunityItemNameAddition().move_along_route(update, context)

    @register_typing_handler
    async def handle_message(self, update, context):
        context.user_data['CREATING_ITEM_ROD_NAME'] = update.message.text
        context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_ITEM_GROUP'
        return await community_item_group_addition.CommunityItemGroupAddition().jump_along_route(update, context)
