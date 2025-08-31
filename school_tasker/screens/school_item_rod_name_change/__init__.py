from hammett.core import Button
from hammett.core.constants import DEFAULT_STATE, SourceTypes
from hammett.core.handlers import register_typing_handler, register_button_handler
from hammett.core.mixins import RouteMixin

import backend
from captions import ENTER_NEW_ITEM_ROD_NAME, ITEM_ROD_NAME_WAS_SUCCESSFULLY_CHANGED, CHANGE_ITEM_ROD_NAME_AGAIN, \
    TO_THE_ITEM_SCREEN, TO_SCREEN_OF_MANAGING_COMMUNITY, BUTTON_BACK_TO_MENU
from school_tasker.screens import school_item_change_base_class, school_item_management, community_management_main, \
    main_menu
from states import CHANGING_ITEM_ROD_NAME


class SchoolItemRodNameChange(school_item_change_base_class.SchoolItemChangeBaseClass, RouteMixin):
    routes = (
        ({DEFAULT_STATE}, CHANGING_ITEM_ROD_NAME),
    )
    description = ENTER_NEW_ITEM_ROD_NAME

    @register_typing_handler
    async def handle_message(self, update, context):
        await backend.update_items_set_rod_name_by_item_index(context, update)
        return await backend.show_notification_screen(update, context, 'send',
                                                      ITEM_ROD_NAME_WAS_SUCCESSFULLY_CHANGED,
                                                      [
                                                          [Button(
                                                              CHANGE_ITEM_ROD_NAME_AGAIN,
                                                              self.go_change_rod_name,
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
                                                           ]])

    @register_button_handler
    async def go_change_rod_name(self, update, context):
        return await SchoolItemRodNameChange().move_along_route(update, context)
