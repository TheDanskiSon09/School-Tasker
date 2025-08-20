from json import dumps

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from constants import BUTTON_BACK_TO_MENU, SELECT_OPTIONS
from school_tasker.screens.base import base_screen
from utils import get_clean_var, get_payload_safe


class Options(base_screen.BaseScreen):
    description = SELECT_OPTIONS

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import main_menu
        user_id = update.effective_user.id
        notification_button_title = str()
        notification_permission = await backend.execute_query("SELECT send_notification FROM Users WHERE id = %s", (user_id,))
        # backend.cursor.execute("SELECT send_notification FROM Users WHERE id = %s", (user_id,))
        # notification_permission = backend.cursor.fetchone()
        notification_permission = get_clean_var(notification_permission, "to_string", 0, True)
        if notification_permission == '0':
            notification_button_title = "Включить "
        if notification_permission == '1':
            notification_button_title = "Выключить "
        notification_button_title += "рассылки от бота"
        return [
            [
                Button(notification_button_title, self.edit_notification_permission,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                       payload=dumps({"index": notification_permission}))
            ],
            [
                Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                       source_type=SourceTypes.MOVE_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def edit_notification_permission(self, update, context):
        await get_payload_safe(self, update, context, "options", "index")
        notification_permission = context.user_data['index']
        if notification_permission == '1':
            notification_permission = 0
        else:
            notification_permission = '1'
        user = update.effective_user
        await backend.execute_query('UPDATE Users set send_notification = %s WHERE id = %s', (notification_permission, user.id))
        # backend.cursor.execute(
        #     'UPDATE Users set send_notification = %s WHERE id = %s', (notification_permission, user.id))
        # backend.connection.commit()
        return await self.move(update, context)