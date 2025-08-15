from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

from constants import BUTTON_BACK, WHAT_DO_YOU_WANT_TO_DO
from school_tasker.screens.base import base_screen


class CommunitiesMain(base_screen.BaseScreen):
    description = WHAT_DO_YOU_WANT_TO_DO

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import community_join, main_menu
        return [
            [
                Button('Создать своё сообщество ➕', self.go_create_community,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button('Зайти в существующее сообщество 🔎', community_join.CommunityJoin,
                       source_type=SourceTypes.MOVE_SOURCE_TYPE)
            ],
            [
                Button(BUTTON_BACK, main_menu.MainMenu,
                       source_type=SourceTypes.MOVE_SOURCE_TYPE)
            ]
        ]

    @register_button_handler
    async def go_create_community(self, update, context):
        context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_CLASS'
        from school_tasker.screens import community_name_creation
        return await community_name_creation.CommunityNameCreation().move(update, context)