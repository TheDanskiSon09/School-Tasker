from emoji import is_emoji
from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler, register_typing_handler
from hammett.core.mixins import RouteMixin

import backend
from captions import BUTTON_BACK, ENTER_EMOJI_THAT_ASSOCIATES_WITH_ITEM, YOUR_ITEM_WAS_SUCCESSFULLY_CREATED, \
    CREATE_MORE_ITEM, TO_THE_ITEM_SCREEN, BUTTON_BACK_TO_MENU
from school_tasker.screens import community_item_management, main_menu, community_item_name_addition
from school_tasker.screens.base import base_screen
from states import CREATING_ITEM_EMOJI, CREATING_ITEM_GROUP


class CommunityItemEmojiAddition(base_screen.BaseScreen, RouteMixin):
    routes = (
        ({CREATING_ITEM_GROUP}, CREATING_ITEM_EMOJI),
    )
    description = ENTER_EMOJI_THAT_ASSOCIATES_WITH_ITEM

    async def add_default_keyboard(self, update, context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def go_back(self, update, context):
        context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_ITEM_GROUP'
        from school_tasker.screens import community_item_group_addition
        return await community_item_group_addition.CommunityItemGroupAddition().move_along_route(update, context)

    @register_typing_handler
    async def handle_message(self, update, context):
        if len(update.message.text) - 1 == 1 and is_emoji(update.message.text):
            context.user_data['CURRENT_TYPING_ACTION'] = ''
            context.user_data['CREATING_ITEM_EMOJI'] = update.message.text
            await backend.create_new_school_item(context)
            return await backend.show_notification_screen(update, context, 'send',
                                                          YOUR_ITEM_WAS_SUCCESSFULLY_CREATED,
                                                          [
                                                              [Button(CREATE_MORE_ITEM,
                                                                      self.go_create_more_items,
                                                                      source_type=SourceTypes.HANDLER_SOURCE_TYPE),
                                                               ],
                                                              [Button(TO_THE_ITEM_SCREEN,
                                                                      community_item_management.CommunityItemManagement,
                                                                      source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                               ],
                                                              [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                      source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                               ]])
        else:
            return await CommunityItemEmojiAddition().jump_along_route(update, context)

    @register_button_handler
    async def go_create_more_items(self, update, context):
        return await community_item_name_addition.CommunityItemNameAddition().move_along_route(update, context)
