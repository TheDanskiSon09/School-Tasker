from json import dumps

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from captions import BUTTON_BACK, SELECT_USER
from school_tasker.screens.base import base_screen
from utils import get_clean_var, get_payload_safe


class CommunityUserChange(base_screen.BaseScreen):
    description = SELECT_USER

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import community_management_main
        keyboard = []
        list_length = await backend.get_count_of_classes_with_class_name_and_user_id(context, update)
        list_length = get_clean_var(list_length, 'to_int', 0, True)
        id_list = await backend.get_user_id_from_user_communities_by_class_name_and_user_id(context, update)
        for new_id in range(list_length):
            user_id = get_clean_var(id_list, 'to_string', new_id, True)
            user_name = await backend.get_name_from_users_by_id(user_id)
            user_name = get_clean_var(user_name, 'to_string', 0, True)
            keyboard.append([Button(user_name, self.checkout_user,
                                    source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                                    payload=dumps({'CHANGE_USER_ROLE_ID': user_id}))])
        keyboard.append(
            [
                Button(BUTTON_BACK, community_management_main.CommunityManagementMain,
                       source_type=SourceTypes.MOVE_SOURCE_TYPE),
            ])
        return keyboard

    @register_button_handler
    async def checkout_user(self, update, context):
        from school_tasker.screens import user_role_selection
        await get_payload_safe(self, update, context, 'USER_STATS', 'CHANGE_USER_ROLE_ID')
        user_role = await backend.get_role_from_user_community_by_id_and_class_name(context)
        user_role = get_clean_var(user_role, 'to_string', 0, True)
        context.user_data['CHANGE_USER_ROLE_ROLE'] = user_role
        return await user_role_selection.UserRoleSelection().move(update, context)
