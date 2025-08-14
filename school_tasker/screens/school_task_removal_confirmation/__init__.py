from os.path import exists
from shutil import rmtree

from hammett.conf import settings
from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from constants import BUTTON_BACK, ARE_YOU_SURE_YOU_WANT_TO_DELETE_THIS_TASK, I_CANT_MAKE_YOUR_REQUEST, \
    MAKE_ANOTHER_TRY, TO_THE_REDACTOR_MENU, DELETE_MORE_TASKS, BUTTON_BACK_TO_MENU, TASK_WAS_SUCCESSFULLY_DELETED
from school_tasker.screens.base import base_screen
from utils import get_username


class SchoolTaskRemovalConfirmation(base_screen.BaseScreen):
    deletion_index = 0

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import school_task_removal
        return [
            [
                Button("Удалить🗑️", self.delete_school_task, source_type=SourceTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button(BUTTON_BACK, school_task_removal.SchoolTaskRemoval, source_type=SourceTypes.MOVE_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def delete_school_task(self, update, context):
        from school_tasker.screens import main_menu
        from school_tasker.screens import school_task_management_main
        from school_tasker.screens import school_task_removal
        check_task = await backend.check_task_status(context)
        if not check_task:
            return await backend.show_notification_screen(update, context, 'render',
                                                  I_CANT_MAKE_YOUR_REQUEST,
                                                  [
                                                      [Button(MAKE_ANOTHER_TRY, school_task_management_main.SchoolTaskManagementMain,
                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                       ],
                                                      [Button(BUTTON_BACK, school_task_management_main.SchoolTaskManagementMain,
                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                       ]])
        else:
            task_index = context.user_data['task_index']
            user = update.effective_user
            formatted_index = await backend.get_var_from_database(task_index, "item_index", True, context)
            name = get_username(user.first_name, user.last_name, user.username)
            await backend.logger_alert([name, user.id], "delete", formatted_index, False, context)
            backend.cursor.execute(
                '''DELETE FROM ''' + context.user_data['CURRENT_CLASS_NAME'] + '''_Tasks WHERE item_index = %s''',
                (formatted_index,))
            backend.connection.commit()
            if exists(str(settings.MEDIA_ROOT) + '/' + formatted_index):
                rmtree(str(settings.MEDIA_ROOT) + '/' + formatted_index)
            database_length = await backend.get_var_from_database(None, "database_length_SchoolTasker", True, context)
            if database_length > 0:
                keyboard = [
                    [
                        Button(TO_THE_REDACTOR_MENU, school_task_management_main.SchoolTaskManagementMain,
                               source_type=SourceTypes.MOVE_SOURCE_TYPE),
                    ],
                    [
                        Button(DELETE_MORE_TASKS, school_task_removal.SchoolTaskRemoval,
                               source_type=SourceTypes.MOVE_SOURCE_TYPE),
                    ],
                    [
                        Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                               source_type=SourceTypes.MOVE_SOURCE_TYPE)
                    ],
                ]
            else:
                keyboard = [
                    [
                        Button(TO_THE_REDACTOR_MENU, school_task_management_main.SchoolTaskManagementMain,
                               source_type=SourceTypes.MOVE_SOURCE_TYPE),
                    ],
                    [
                        Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                               source_type=SourceTypes.MOVE_SOURCE_TYPE)
                    ],
                ]
            return await backend.show_notification_screen(update, context, 'render', TASK_WAS_SUCCESSFULLY_DELETED, keyboard)

    async def get_description(self, update, context):
        return ARE_YOU_SURE_YOU_WANT_TO_DELETE_THIS_TASK
