from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from captions import ARE_YOU_SURE_YOU_WANT_TO_DELETE_THIS_ITEM, BUTTON_BACK, BUTTON_BACK_TO_MENU
from school_tasker.screens.base import base_screen


class SchoolItemDeletionConfirmation(base_screen.BaseScreen):
    description = ARE_YOU_SURE_YOU_WANT_TO_DELETE_THIS_ITEM

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import school_item_management
        return [
            [
                Button('Удалить🗑️', self.delete_item,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ],
            [
                Button(BUTTON_BACK, school_item_management.SchoolItemManagement,
                       source_type=SourceTypes.MOVE_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def delete_item(self, update, context):
        from school_tasker.screens import community_item_management, main_menu
        await backend.delete_item(context)
        await backend.delete_task_from_deleted_item(context)
        return await backend.show_notification_screen(update, context, 'render',
                                                      '<strong>Предмет был успешно удалён!</strong>',
                                                      [
                                                          [Button('⬅ Вернуться в экран управления сообществом',
                                                                  community_item_management.CommunityItemManagement,
                                                                  source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                           ],
                                                          [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                  source_type=SourceTypes.MOVE_SOURCE_TYPE),
                                                           ]])
