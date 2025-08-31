from hammett.core import Button
from hammett.core.constants import SourceTypes, DEFAULT_STATE
from hammett.core.handlers import register_button_handler, register_typing_handler
from hammett.core.mixins import RouteMixin

import backend
from captions import BUTTON_BACK, ENTER_NEW_PASSWORD_FOR_COMMUNITY, PASSWORD_OF_YOUR_COMMUNITY_WAS_SUCCESSFULLY_CHANGED, \
    CHANGE_COMMUNITY_PASSWORD_AGAIN, TO_SCREEN_OF_MANAGING_COMMUNITY, BUTTON_BACK_TO_MENU
from school_tasker.screens import community_management_main, main_menu
from school_tasker.screens.base import base_screen
from states import CHANGING_CLASS_PASSWORD


class CommunityPasswordChange(base_screen.BaseScreen, RouteMixin):
    routes = (
        ({DEFAULT_STATE}, CHANGING_CLASS_PASSWORD),
    )
    description = ENTER_NEW_PASSWORD_FOR_COMMUNITY

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
        context.user_data['CURRENT_TYPING_ACTION'] = ''
        return await community_management_main.CommunityManagementMain().move(update, context)

    @register_typing_handler
    async def handle_message(self, update, context):
        await backend.update_community_password_by_name(update, context)
        return await backend.show_notification_screen(update, context, 'send',
                                                          PASSWORD_OF_YOUR_COMMUNITY_WAS_SUCCESSFULLY_CHANGED,
                                                          [
                                                              [Button(CHANGE_COMMUNITY_PASSWORD_AGAIN,
                                                                      self.go_change_password,
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
    async def go_change_password(self, update, context):
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_CLASS_PASSWORD'
        return await CommunityPasswordChange().move_along_route(update, context)