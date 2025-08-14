from json import dumps

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from constants import BUTTON_BACK_TO_MENU
from school_tasker.screens.base import base_screen
from utils import get_clean_var, get_payload_safe


class CurrentCommunityChange(base_screen.BaseScreen):
    description = '<strong>Выберите доступное Вам сообщество:</strong>'

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import main_menu
        keyboard = []
        backend.cursor.execute('SELECT class_name FROM UserCommunities WHERE user_id = %s', (update.effective_user.id,))
        name_list = backend.cursor.fetchall()
        backend.cursor.execute('SELECT COUNT(*) FROM UserCommunities WHERE user_id = %s', (update.effective_user.id,))
        db_length = backend.cursor.fetchone()
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        for i in range(db_length):
            new_name = get_clean_var(name_list, 'to_string', i - 1, True)
            new_community = [Button(new_name, self.change_class,
                                    source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                                    payload=dumps({"CURRENT_CLASS_NAME": new_name}))]
            keyboard.append(new_community)
        keyboard.append([Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                source_type=SourceTypes.MOVE_SOURCE_TYPE)])
        return keyboard

    @register_button_handler
    async def change_class(self, update, context):
        from school_tasker.screens import main_menu
        await get_payload_safe(self, update, context, "CHANGE_CURRENT_CLASS_NAME", 'CURRENT_CLASS_NAME')
        return await main_menu.MainMenu().move(update, context)