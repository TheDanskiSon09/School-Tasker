from hammett.core import Button
from hammett.core.constants import SourceTypes, DEFAULT_STATE
from hammett.core.handlers import register_button_handler, register_typing_handler
from hammett.core.mixins import RouteMixin

from captions import BUTTON_BACK, ENTER_GROUP_NUMBER_OF_THIS_ITEM
from school_tasker.screens import community_item_emoji_addition
from school_tasker.screens.base import base_screen
from states import CREATING_ITEM_GROUP, CREATING_ITEM_ROD_NAME


class CommunityItemGroupAddition(base_screen.BaseScreen, RouteMixin):
    routes = (
        ({CREATING_ITEM_ROD_NAME}, CREATING_ITEM_GROUP),
    )
    description = ENTER_GROUP_NUMBER_OF_THIS_ITEM

    async def add_default_keyboard(self, update, context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def go_back(self, update, context):
        context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_ITEM_ROD_NAME'
        from school_tasker.screens import community_item_rod_name_addition
        return await community_item_rod_name_addition.CommunityItemRodNameAddition().move_along_route(update, context)

    @register_typing_handler
    async def handle_message(self, update, context):
        try:
            if 0 < int(update.message.text) <= 98:
                context.user_data['CREATING_ITEM_GROUPS'] = update.message.text
                context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_ITEM_EMOJI'
                return await community_item_emoji_addition.CommunityItemEmojiAddition().jump_along_route(update, context)
            return await CommunityItemGroupAddition().jump_along_route(update, context)
        except ValueError:
            return await CommunityItemGroupAddition().jump_along_route(update, context)
