from hammett.core import Button
from hammett.core.constants import SourceTypes, DEFAULT_STATE
from hammett.core.handlers import register_button_handler, register_typing_handler
from hammett.core.mixins import RouteMixin
from mysql.connector import IntegrityError, ProgrammingError

import backend
from captions import BUTTON_BACK, ENTER_PASSWORD_OF_YOUR_COMMUNITY, YOUR_COMMUNITY_WAS_SUCCESSFULLY_CREATED, \
    BUTTON_BACK_TO_MENU
from school_tasker.screens import main_menu, community_name_creation
from school_tasker.screens.base import base_screen
from states import ADDING_PASSWORD_TO_CLASS, CREATING_CLASS


class CommunityPasswordCreation(base_screen.BaseScreen, RouteMixin):
    routes = (
        ({CREATING_CLASS}, ADDING_PASSWORD_TO_CLASS),
    )
    description = ENTER_PASSWORD_OF_YOUR_COMMUNITY

    async def add_default_keyboard(self, update, context):
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def go_back(self, update, context):
        from school_tasker.screens import community_name_creation
        context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_CLASS'
        return await community_name_creation.CommunityNameCreation().move_along_route(update, context)

    @register_typing_handler
    async def handle_message(self, update, context):
        try:
            context.user_data['CURRENT_CLASS_PASSWORD'] = update.message.text
            context.user_data['CURRENT_TYPING_ACTION'] = ''
            await backend.create_community_table(context)
            await backend.create_tasks_table(context)
            await backend.create_items_table(context)
            await backend.add_new_community(update, context)
            return await backend.show_notification_screen(update, context, 'send',
                                                          YOUR_COMMUNITY_WAS_SUCCESSFULLY_CREATED,
                                                          [
                                                              [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                      source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                               ]])
        except IntegrityError:
            context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_CLASS'
            return await community_name_creation.CommunityNameCreation().jump(update, context)
        except ProgrammingError:
            return await backend.show_notification_screen(update, context, 'send',
                                                          YOUR_COMMUNITY_WAS_SUCCESSFULLY_CREATED,
                                                          [
                                                              [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                      source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                               ]])
