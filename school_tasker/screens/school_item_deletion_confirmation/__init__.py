from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from constants import BUTTON_BACK, BUTTON_BACK_TO_MENU
from school_tasker.screens.base import base_screen


class SchoolItemDeletionConfirmation(base_screen.BaseScreen):
    description = '<strong>Вы точно уверены, что хотите удалить данный предмет?</strong>'

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import school_item_management
        return [
            [
                Button('Удалить🗑️', self.delete_item,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button(BUTTON_BACK, school_item_management.SchoolItemManagement,
                       source_type=SourceTypes.MOVE_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def delete_item(self, update, context):
        from school_tasker.screens import community_item_management, main_menu
        backend.cursor.execute(
            'DELETE FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items WHERE item_index = %s',
            (context.user_data['MANAGE_ITEM_INDEX'],))
        backend.cursor.execute('DELETE FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_name = %s',
                               (context.user_data['MANAGE_ITEM_MAIN_NAME'],))
        backend.connection.commit()
        return await backend.show_notification_screen(update, context, 'send',
                                                      '<strong>Предмет был успешно удалён!</strong>',
                                                      [
                                                          [Button('Вернуться в панель',
                                                                  community_item_management.CommunityItemManagement,
                                                                  source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                           ],
                                                          [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                  source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                           ]])
