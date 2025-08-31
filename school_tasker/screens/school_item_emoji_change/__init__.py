from emoji import is_emoji
from hammett.core import Button
from hammett.core.constants import DEFAULT_STATE, SourceTypes
from hammett.core.handlers import register_typing_handler, register_button_handler
from hammett.core.mixins import RouteMixin

import backend
from captions import ENTER_EMOJI_FOR_ITEM, \
    TO_THE_ITEM_SCREEN, TO_SCREEN_OF_MANAGING_COMMUNITY, BUTTON_BACK_TO_MENU, ITEM_EMOJI_WAS_SUCCESSFULLY_CHANGED, \
    CHANGE_ITEM_EMOJI_AGAIN
from school_tasker.screens import school_item_change_base_class, school_item_management, community_management_main, \
    main_menu
from states import CHANGING_ITEM_EMOJI


class SchoolItemEmojiChange(school_item_change_base_class.SchoolItemChangeBaseClass, RouteMixin):
    routes = (
        ({DEFAULT_STATE}, CHANGING_ITEM_EMOJI),
    )
    description = ENTER_EMOJI_FOR_ITEM

    @register_typing_handler
    async def handle_message(self, update, context):
        if len(update.message.text) - 1 == 1 and is_emoji(update.message.text):
            context.user_data['CURRENT_TYPING_ACTION'] = ''
            await backend.update_items_set_emoji_by_main_name(context, update)
            return await backend.show_notification_screen(update, context, 'send',
                                                          ITEM_EMOJI_WAS_SUCCESSFULLY_CHANGED, [
                                                              [Button(CHANGE_ITEM_EMOJI_AGAIN,
                                                                      self.go_change_emoji,
                                                                      source_type=SourceTypes.HANDLER_SOURCE_TYPE),
                                                               ],
                                                              [Button(TO_THE_ITEM_SCREEN,
                                                                      school_item_management.SchoolItemManagement,
                                                                      source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                               ],
                                                              [Button(TO_SCREEN_OF_MANAGING_COMMUNITY,
                                                                      community_management_main.CommunityManagementMain,
                                                                      source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                               ],
                                                              [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                      source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                               ],
                                                          ])
        else:
            return await SchoolItemEmojiChange().jump(update, context)

    @register_button_handler
    async def go_change_emoji(self, update, context):
        return await SchoolItemEmojiChange().move_along_route(update, context)
