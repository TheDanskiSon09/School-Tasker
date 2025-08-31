from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

from captions import BUTTON_BACK, WHAT_DO_YOU_WANT_TO_DO_WITH_THIS_ITEM
from school_tasker.screens.base import base_screen


class SchoolItemManagement(base_screen.BaseScreen):
    description = WHAT_DO_YOU_WANT_TO_DO_WITH_THIS_ITEM

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import (
            community_item_management,
            school_item_deletion_confirmation,
        )
        return [
            [
                Button('Изменить название предмета', self.change_name,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ],
            [
                Button('Изменить название предмета в дательном падеже', self.change_rod_name,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ],
            [
                Button('Изменить количество групп предмета', self.change_group_number,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ],
            [
                Button('Изменить эмодзи предмета', self.change_emoji,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ],
            [
                Button('Удалить предмет', school_item_deletion_confirmation.SchoolItemDeletionConfirmation,
                       source_type=SourceTypes.MOVE_SOURCE_TYPE),
            ],
            [
                Button(BUTTON_BACK, community_item_management.CommunityItemManagement,
                       source_type=SourceTypes.MOVE_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def change_name(self, update, context):
        from school_tasker.screens import school_item_name_change
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_ITEM_NAME'
        return await school_item_name_change.SchoolItemNameChange().move_along_route(update, context)

    @register_button_handler
    async def change_rod_name(self, update, context):
        from school_tasker.screens import school_item_rod_name_change
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_ITEM_ROD_NAME'
        return await school_item_rod_name_change.SchoolItemRodNameChange().move_along_route(update, context)

    @register_button_handler
    async def change_group_number(self, update, context):
        from school_tasker.screens import school_item_groups_change
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_ITEM_GROUPS'
        return await school_item_groups_change.SchoolItemGroupsChange().move_along_route(update, context)

    @register_button_handler
    async def change_emoji(self, update, context):
        from school_tasker.screens import school_item_emoji_change
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_ITEM_EMOJI'
        return await school_item_emoji_change.SchoolItemEmojiChange().move_along_route(update, context)
