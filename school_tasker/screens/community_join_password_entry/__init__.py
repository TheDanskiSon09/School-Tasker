from hammett.core import Button
from hammett.core.constants import SourceTypes, DEFAULT_STATE
from hammett.core.handlers import register_button_handler, register_typing_handler
from hammett.core.mixins import RouteMixin

import backend
from captions import BUTTON_BACK, ENTER_PASSWORD_OF_COMMUNITY, YOU_SUCCESSFULLY_JOINED_COMMUNITY, \
    JOIN_TO_MORE_COMMUNITIES, TO_THE_COMMUNITIES_SCREEN, BUTTON_BACK_TO_MENU
from school_tasker.screens import community_join, communitites_main, main_menu
from school_tasker.screens.base import base_screen
from states import WRITING_PASSWORD_TO_JOIN


class CommunityJoinPasswordEntry(base_screen.BaseScreen, RouteMixin):
    routes = (
        ({DEFAULT_STATE}, WRITING_PASSWORD_TO_JOIN),
    )
    description = ENTER_PASSWORD_OF_COMMUNITY

    async def add_default_keyboard(self, update, context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def go_back(self, update, context):
        from school_tasker.screens import community_join
        context.user_data['CURRENT_TYPING_ACTION'] = ''
        return await community_join.CommunityJoin().move(update, context)

    @register_typing_handler
    async def handle_message(self, update, context):
        print('hello!')
        if str(update.message.text) == str(context.user_data['ENTER_COMMUNITY_PASSWORD']):
            await backend.add_user_to_community(update, context)
            context.user_data['CURRENT_TYPING_ACTION'] = ''
            return await backend.show_notification_screen(update, context, 'send',
                                                          YOU_SUCCESSFULLY_JOINED_COMMUNITY, [
                                                              [
                                                                  Button(JOIN_TO_MORE_COMMUNITIES,
                                                                         community_join.CommunityJoin,
                                                                         source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                              ],
                                                              [
                                                                  Button(TO_THE_COMMUNITIES_SCREEN,
                                                                         communitites_main.CommunitiesMain,
                                                                         source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                              ],
                                                              [
                                                                  Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                         source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                              ],
                                                          ])
        else:
            return await CommunityJoinPasswordEntry().jump_along_route(update, context)
