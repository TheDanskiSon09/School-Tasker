from json import dumps

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from constants import BUTTON_CREATE_ITEM, BUTTON_BACK, THERE_IS_NO_ITEMS_IN_COMMUNITY, SELECT_ACTION
from school_tasker.screens.base import base_screen
from utils import get_clean_var, get_payload_safe


class CommunityItemManagement(base_screen.BaseScreen):

    async def get_description(self, update, context):
        db_length = await backend.execute_query('SELECT COUNT(*) FROM ' + context.user_data['CURRENT_CLASS_NAME'] + "_Items")
        # backend.cursor.execute('SELECT COUNT(*) FROM ' + context.user_data['CURRENT_CLASS_NAME'] + "_Items")
        # db_length = backend.cursor.fetchall()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            return SELECT_ACTION
        else:
            return THERE_IS_NO_ITEMS_IN_COMMUNITY

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import community_management_main
        keyboard = []
        db_length = await backend.execute_query('SELECT COUNT(*) FROM ' + context.user_data['CURRENT_CLASS_NAME'] + "_Items")
        # backend.cursor.execute('SELECT COUNT(*) FROM ' + context.user_data['CURRENT_CLASS_NAME'] + "_Items")
        # db_length = backend.cursor.fetchall()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 0:
            main_name_list = await backend.execute_query('SELECT main_name FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items')
            emoji_list = await backend.execute_query('SELECT emoji FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items')
            # backend.cursor.execute('SELECT main_name FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items')
            rod_name_list = await backend.execute_query('SELECT rod_name FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items')
            groups_list = await backend.execute_query('SELECT groups_list FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items')
            index_list = await backend.execute_query('SELECT item_index FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items')
            # main_name_list = backend.cursor.fetchall()
            # backend.cursor.execute('SELECT emoji FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items')
            # emoji_list = backend.cursor.fetchall()
            # backend.cursor.execute('SELECT rod_name FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items')
            # rod_name_list = backend.cursor.fetchall()
            # backend.cursor.execute('SELECT groups_list FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items')
            # groups_list = backend.cursor.fetchall()
            # backend.cursor.execute('SELECT item_index FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items')
            # index_list = backend.cursor.fetchall()
            for i in range(db_length):
                main_name = get_clean_var(main_name_list, 'to_string', i - 1, True)
                emoji = get_clean_var(emoji_list, 'to_string', i - 1, True)
                rod_name = get_clean_var(rod_name_list, 'to_string', i - 1, True)
                groups = get_clean_var(groups_list, 'to_string', i - 1, True)
                index = get_clean_var(index_list, 'to_string', i - 1, True)
                keyboard.append(
                    [Button(emoji + main_name, self.manage_item, source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                            payload=dumps({'MANAGE_ITEM_INDEX': index,
                                           "MANAGE_ITEM_MAIN_NAME": main_name,
                                           'MANAGE_ITEM_ROD_NAME': rod_name,
                                           'MANAGE_ITEM_GROUPS': groups}))])
        keyboard.append([Button(BUTTON_CREATE_ITEM, self.go_create_item,
                                source_type=SourceTypes.HANDLER_SOURCE_TYPE)])
        keyboard.append([Button(BUTTON_BACK, community_management_main.CommunityManagementMain,
                                source_type=SourceTypes.MOVE_SOURCE_TYPE)])
        return keyboard

    @register_button_handler
    async def go_create_item(self, update, context):
        context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_ITEM_NAME'
        from school_tasker.screens import community_item_name_addition
        return await community_item_name_addition.CommunityItemNameAddition().move(update, context)

    @register_button_handler
    async def manage_item(self, update, context):
        from school_tasker.screens import school_item_management
        await get_payload_safe(self, update, context, 'MANAGE_ITEM', "MANAGE_ITEM_INDEX")
        await get_payload_safe(self, update, context, 'MANAGE_ITEM', "MANAGE_ITEM_MAIN_NAME")
        await get_payload_safe(self, update, context, 'MANAGE_ITEM', "MANAGE_ITEM_ROD_NAME")
        await get_payload_safe(self, update, context, 'MANAGE_ITEM', "MANAGE_ITEM_GROUPS")
        return await school_item_management.SchoolItemManagement().move(update, context)