from json import dumps

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from constants import BUTTON_BACK, BUTTON_BACK_TO_MENU, USER_ROLE_WAS_SUCCESSFULLY_CHANGED, CONTINUE_CHANGE_ROLES, \
    TO_SCREEN_OF_MANAGING_COMMUNITY
from school_tasker.screens.base import base_screen
from utils import get_clean_var, get_payload_safe


class UserRoleSelection(base_screen.BaseScreen):

    async def get_description(self, update, context):
        name = await backend.execute_query('SELECT name FROM Users WHERE id = %s', (context.user_data['CHANGE_USER_ROLE_ID'],))
        # backend.cursor.execute('SELECT name FROM Users WHERE id = %s', (context.user_data['CHANGE_USER_ROLE_ID'],))
        # name = backend.cursor.fetchall()
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
        from school_tasker.screens import community_management_main
        from school_tasker.screens import community_user_change
        from school_tasker.screens import main_menu
        await get_payload_safe(self, update, context, 'NEW_USER_ROLE_STATS', 'NEW_USER_ROLE')
        if context.user_data['NEW_USER_ROLE'] == 'Администратор':
            new_role = 'ADMIN'
        else:
            new_role = 'ANONIM'
        await backend.execute_query('UPDATE UserCommunities SET user_role_in_class = %s WHERE user_id = %s AND class_name = %s',
            (new_role, context.user_data['CHANGE_USER_ROLE_ID'], context.user_data['CURRENT_CLASS_NAME'],))
        # backend.cursor.execute(
        #     'UPDATE UserCommunities SET user_role_in_class = %s WHERE user_id = %s AND class_name = %s',
        #     (new_role, context.user_data['CHANGE_USER_ROLE_ID'], context.user_data['CURRENT_CLASS_NAME'],))
        # backend.connection.commit()
        return await backend.show_notification_screen(update, context, 'render',
                                                      USER_ROLE_WAS_SUCCESSFULLY_CHANGED,
                                                      [
                                                          [
                                                              Button(CONTINUE_CHANGE_ROLES,
                                                                     community_user_change.CommunityUserChange,
                                                                     source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                          ],
                                                          [
                                                              Button(TO_SCREEN_OF_MANAGING_COMMUNITY,
                                                                     community_management_main.CommunityManagementMain,
                                                                     source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                          ],
                                                          [
                                                              Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                     source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                          ]
                                                      ])
