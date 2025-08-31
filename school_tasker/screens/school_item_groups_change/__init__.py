from hammett.core import Button
from hammett.core.constants import DEFAULT_STATE, SourceTypes
from hammett.core.handlers import register_typing_handler, register_button_handler
from hammett.core.mixins import RouteMixin

import backend
from captions import ENTER_GROUP_NUMBER, ITEM_GROUP_NUMBER_WAS_SUCCESSFULLY_CHANGED, CHANGE_ITEM_GROUP_NUMBER_AGAIN, \
    TO_THE_ITEM_SCREEN, TO_SCREEN_OF_MANAGING_COMMUNITY, BUTTON_BACK_TO_MENU
from school_tasker.screens import school_item_change_base_class, school_item_management, community_management_main, \
    main_menu
from states import CHANGING_ITEM_GROUPS


class SchoolItemGroupsChange(school_item_change_base_class.SchoolItemChangeBaseClass, RouteMixin):
    routes = (
        ({DEFAULT_STATE}, CHANGING_ITEM_GROUPS),
    )
    description = ENTER_GROUP_NUMBER

    @register_typing_handler
    async def handle_message(self, update, context):
        try:
            if 0 < int(update.message.text) <= 98:
                await backend.update_items_set_groups_list_by_main_name(context, update)
                context.user_data['CURRENT_TYPING_ACTION'] = ''
                return await backend.show_notification_screen(update, context, 'send',
                                                              ITEM_GROUP_NUMBER_WAS_SUCCESSFULLY_CHANGED,
                                                              [
                                                                  [Button(
                                                                      CHANGE_ITEM_GROUP_NUMBER_AGAIN,
                                                                      self.go_change_groups,
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
                return await SchoolItemGroupsChange().jump_along_route(update, context)
        except ValueError:
            return await SchoolItemGroupsChange().jump_along_route(update, context)

    @register_button_handler
    async def go_change_groups(self, update, context):
        return await SchoolItemGroupsChange().move_along_route(update, context)
