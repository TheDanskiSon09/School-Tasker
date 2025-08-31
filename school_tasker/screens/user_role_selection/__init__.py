from json import dumps

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from captions import (
    BUTTON_BACK,
    BUTTON_BACK_TO_MENU,
    CONTINUE_CHANGE_ROLES,
    TO_SCREEN_OF_MANAGING_COMMUNITY,
    USER_ROLE_WAS_SUCCESSFULLY_CHANGED,
)
from school_tasker.screens.base import base_screen
from utils import get_clean_var, get_payload_safe


class UserRoleSelection(base_screen.BaseScreen):

    async def get_description(self, update, context):
        name = await backend.get_name_from_users_by_index(context)
        name = get_clean_var(name, 'to_string', 0, True)
        return '<strong>Выберите новую роль для ' + name + ':</strong>'

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import community_user_change
        keyboard = []
        if context.user_data['CHANGE_USER_ROLE_ROLE'] == 'ANONIM':
            new_role = 'Администратор'
        else:
            new_role = 'Обычный пользователь'
        keyboard.append([Button(new_role, self.change_role,
                                source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                                payload=dumps({'NEW_USER_ROLE': new_role}))])
        keyboard.append([Button(BUTTON_BACK, community_user_change.CommunityUserChange,
                                source_type=SourceTypes.MOVE_SOURCE_TYPE)])
        return keyboard

    @register_button_handler
    async def change_role(self, update, context):
        from school_tasker.screens import (
            community_management_main,
            community_user_change,
            main_menu,
        )
        await get_payload_safe(self, update, context, 'NEW_USER_ROLE_STATS', 'NEW_USER_ROLE')
        if context.user_data['NEW_USER_ROLE'] == 'Администратор':
            new_role = 'ADMIN'
        else:
            new_role = 'ANONIM'
        await backend.update_user_communities_set_user_role_by_user_id_and_class_name(new_role, context)
        return await backend.show_notification_screen(update, context, 'render',
                                                      USER_ROLE_WAS_SUCCESSFULLY_CHANGED,
                                                      [
                                                          [
                                                              Button(CONTINUE_CHANGE_ROLES,
                                                                     community_user_change.CommunityUserChange,
                                                                     source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                          ],
                                                          [
                                                              Button(TO_SCREEN_OF_MANAGING_COMMUNITY,
                                                                     community_management_main.CommunityManagementMain,
                                                                     source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                          ],
                                                          [
                                                              Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                     source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                          ],
                                                      ])
