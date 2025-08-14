from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

from constants import BUTTON_BACK, ENTER_EMOJI_THAT_ASSOCIATES_WITH_ITEM
from school_tasker.screens.base import base_screen


class CommunityItemEmojiAddition(base_screen.BaseScreen):
    description = ENTER_EMOJI_THAT_ASSOCIATES_WITH_ITEM

    async def add_default_keyboard(self, update, context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, update, context):
        context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_ITEM_GROUP'
        from school_tasker.screens import community_item_group_addition
        return await community_item_group_addition.CommunityItemGroupAddition().move(update, context)