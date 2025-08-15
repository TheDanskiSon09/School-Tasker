from json import dumps

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from constants import BUTTON_BACK, SELECT_INTERESTING_COMMUNITY, THERE_IS_EMPTY_FOR_A_WHILE
from school_tasker.screens.base import base_screen
from utils import get_clean_var, get_payload_safe


class CommunityJoin(base_screen.BaseScreen):

    async def get_description(self, update, context):
        backend.cursor.execute('SELECT COUNT(*) FROM Community')
        community_count = backend.cursor.fetchall()
        community_count = get_clean_var(community_count, 'to_int', 0, True)
        if community_count > 0:
            return SELECT_INTERESTING_COMMUNITY
        else:
            return THERE_IS_EMPTY_FOR_A_WHILE

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import communitites_main
        keyboard = []
        backend.cursor.execute('SELECT COUNT(*) FROM Community')
        check_length = backend.cursor.fetchall()
        check_length = get_clean_var(check_length, 'to_int', 0, True)
        if check_length > 0:
            backend.cursor.execute('SELECT name FROM Community')
            community_list = backend.cursor.fetchall()
            for community in range(check_length):
                new_community = get_clean_var(community_list, 'to_string', community - 1, True)
                keyboard.append([Button(new_community, self.go_enter_password,
                                        source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                                        payload=dumps({'ENTER_COMMUNITY_NAME': new_community}))])
        keyboard.append([Button(BUTTON_BACK, communitites_main.CommunitiesMain,
                                source_type=SourceTypes.MOVE_SOURCE_TYPE)])
        return keyboard

    @register_button_handler
    async def go_enter_password(self, update, context):
        from school_tasker.screens import community_join_password_entry
        await get_payload_safe(self, update, context, 'GET_ENTER_COMMUNITY_NAME', 'ENTER_COMMUNITY_NAME')
        backend.cursor.execute('SELECT COUNT(*) FROM UserCommunities WHERE class_name = %s AND user_id = %s',
                               (context.user_data['ENTER_COMMUNITY_NAME'], update.effective_user.id,))
        check_length = backend.cursor.fetchall()
        check_length = get_clean_var(check_length, 'to_int', 0, True)
        if check_length < 1:
            backend.cursor.execute('SELECT password FROM Community WHERE name = %s',
                                   (context.user_data['ENTER_COMMUNITY_NAME'],))
            context.user_data['ENTER_COMMUNITY_PASSWORD'] = backend.cursor.fetchall()
            context.user_data['ENTER_COMMUNITY_PASSWORD'] = get_clean_var(
                context.user_data['ENTER_COMMUNITY_PASSWORD'], 'to_string', 0, True)
            context.user_data['CURRENT_TYPING_ACTION'] = 'WRITING_PASSWORD_TO_JOIN'
            return await community_join_password_entry.CommunityJoinPasswordEntry().move(update, context)
