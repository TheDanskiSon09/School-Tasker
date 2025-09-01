from json import dumps

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from captions import BUTTON_BACK, SELECT_INTERESTING_COMMUNITY, THERE_IS_EMPTY_FOR_A_WHILE
from school_tasker.screens.base import base_screen
from utils import get_clean_var, get_payload_safe


class CommunityJoin(base_screen.BaseScreen):

    async def get_description(self, update, context):
        community_count = await backend.get_count_of_community()
        community_count = get_clean_var(community_count, 'to_int', 0, True)
        if community_count > 0:
            return SELECT_INTERESTING_COMMUNITY
        else:
            return THERE_IS_EMPTY_FOR_A_WHILE

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import communitites_main
        keyboard = []
        check_length = await backend.get_count_of_community()
        check_length = get_clean_var(check_length, 'to_int', 0, True)
        if check_length > 0:
            community_list = await backend.get_name_of_community()
            community_password_list = await backend.get_community_passwords()
            for community in range(check_length):
                new_community = get_clean_var(community_list, 'to_string', community - 1, True)
                new_community_password = get_clean_var(community_password_list, 'to_string', community - 1, True)
                keyboard.append([Button(new_community, self.go_enter_password,
                                        source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                                        payload=dumps({'ENTER_COMMUNITY_NAME': new_community,
                                                       'ENTER_COMMUNITY_PASSWORD': new_community_password}))])
        keyboard.append([Button(BUTTON_BACK, communitites_main.CommunitiesMain,
                                source_type=SourceTypes.MOVE_SOURCE_TYPE)])
        return keyboard

    @register_button_handler
    async def go_enter_password(self, update, context):
        from school_tasker.screens import community_join_password_entry
        await get_payload_safe(self, update, context, 'GET_ENTER_COMMUNITY_NAME', 'ENTER_COMMUNITY_NAME')
        await get_payload_safe(self, update, context, 'GET_ENTER_COMMUNITY_NAME', 'ENTER_COMMUNITY_PASSWORD')
        check_length = await backend.get_count_of_classes_with_class_name_and_user_id(context, update)
        check_length = get_clean_var(check_length, 'to_int', 0, True)
        if check_length < 1:
            return await community_join_password_entry.CommunityJoinPasswordEntry().move_along_route(update, context)
