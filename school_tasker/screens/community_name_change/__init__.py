from contextlib import suppress

from hammett.core import Button
from hammett.core.constants import SourceTypes, DEFAULT_STATE
from hammett.core.handlers import register_button_handler, register_typing_handler
from hammett.core.mixins import RouteMixin
from mysql.connector import OperationalError

import backend
from captions import BUTTON_BACK, ENTER_NEW_NAME_FOR_COMMUNITY, NAME_OF_YOUR_COMMUNITY_WAS_SUCCESSFULLY_CHANGED, \
    CHANGE_COMMUNITY_NAME_AGAIN, TO_SCREEN_OF_MANAGING_COMMUNITY, BUTTON_BACK_TO_MENU
from school_tasker.screens import community_management_main, main_menu
from school_tasker.screens.base import base_screen
from states import CHANGING_CLASS_NAME


class CommunityNameChange(base_screen.BaseScreen, RouteMixin):
    routes = (
        ({DEFAULT_STATE}, CHANGING_CLASS_NAME),
    )
    description = ENTER_NEW_NAME_FOR_COMMUNITY

    async def add_default_keyboard(self, update, context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def go_back(self, update, context):
        from school_tasker.screens import community_management_main
        return await community_management_main.CommunityManagementMain().move(update, context)

    @register_typing_handler
    async def handle_message(self, update, context):
        new_community_name = update.message.text.replace(' ', '')
        await backend.update_community_set_name_by_name(new_community_name, context)
        await backend.update_user_community_set_class_name_by_class_name(new_community_name, context)
        with suppress(OperationalError):
            await backend.rename_items_table(context, new_community_name)
            await backend.rename_tasks_table(context, new_community_name)
        context.user_data['CURRENT_CLASS_NAME'] = new_community_name
        return await backend.show_notification_screen(update, context, 'send',
                                                      NAME_OF_YOUR_COMMUNITY_WAS_SUCCESSFULLY_CHANGED,
                                                      [
                                                          [Button(CHANGE_COMMUNITY_NAME_AGAIN,
                                                                  self.go_change_name,
                                                                  source_type=SourceTypes.HANDLER_SOURCE_TYPE),
                                                           ],
                                                          [Button(TO_SCREEN_OF_MANAGING_COMMUNITY,
                                                                  community_management_main.CommunityManagementMain,
                                                                  source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                           ],
                                                          [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                  source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                           ]])

    @register_button_handler
    async def go_change_name(self, update, context):
        return await CommunityNameChange().move_along_route(update, context)
