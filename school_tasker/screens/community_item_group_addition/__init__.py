from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

from constants import BUTTON_BACK, ENTER_GROUP_NUMBER_OF_THIS_ITEM
from school_tasker.screens.base import base_screen


class CommunityItemGroupAddition(base_screen.BaseScreen):
    description = ENTER_GROUP_NUMBER_OF_THIS_ITEM

    async def add_default_keyboard(self, update, context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_back(self, update, context):
        context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_ITEM_ROD_NAME'
        from school_tasker.screens import community_item_rod_name_addition
        return await community_item_rod_name_addition.CommunityItemRodNameAddition().move(update, context)