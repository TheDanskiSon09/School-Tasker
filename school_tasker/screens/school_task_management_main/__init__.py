from hammett.core import Button
from hammett.core.constants import SourceTypes

from constants import BUTTON_BACK_TO_MENU, WHICH_CHANGES_YOU_WANT_TO_DO, ADD_TASK, CHANGE_TASK, DELETE_TASK
from school_tasker.screens.base import base_screen


class SchoolTaskManagementMain(base_screen.BaseScreen):
    description = WHICH_CHANGES_YOU_WANT_TO_DO

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import main_menu
        from school_tasker.screens import school_task_change_main
        from school_tasker.screens import school_task_removal
        from school_tasker.screens.school_task_addition import SchoolTaskAddition
        return [
            [
                Button(ADD_TASK, SchoolTaskAddition,
                       source_type=SourceTypes.MOVE_SOURCE_TYPE),
            ],
            [
                Button(CHANGE_TASK, school_task_change_main.SchoolTaskChangeMain,
                       source_type=SourceTypes.MOVE_SOURCE_TYPE),
            ],
            [
                Button(DELETE_TASK, school_task_removal.SchoolTaskRemoval,
                       source_type=SourceTypes.MOVE_SOURCE_TYPE),
            ],
            [
                Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                       source_type=SourceTypes.MOVE_SOURCE_TYPE),
            ],
        ]