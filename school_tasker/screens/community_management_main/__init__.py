from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from captions import BUTTON_BACK
from school_tasker.screens.base import base_screen
from utils import get_clean_var


class CommunityManagementMain(base_screen.BaseScreen):

    async def get_description(self, update, context):
        context.user_data['CURRENT_CLASS_PASSWORD'] = await backend.get_password_of_community_by_name(context)
        context.user_data['CURRENT_CLASS_PASSWORD'] = \
            get_clean_var(context.user_data['CURRENT_CLASS_PASSWORD'], 'to_string', 0, True)
        return '<strong>Название сообщества: ' + context.user_data['CURRENT_CLASS_NAME'] + (
                '\nПароль: ' + '<tg-spoiler>' + context.user_data['CURRENT_CLASS_PASSWORD'] + '</tg-spoiler>' + '</strong>')

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import community_item_management, community_user_change
        keyboard = [
            [
                Button('Изменить название сообщества', self.change_community_name,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ],
            [
                Button('Изменить пароль', self.change_community_password,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ]]
        db_length = await backend.get_count_of_user_communities_by_name(context)
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 1:
            keyboard.append([
                Button('Изменить права пользователей сообщества', community_user_change.CommunityUserChange,
                       source_type=SourceTypes.MOVE_SOURCE_TYPE),
            ])
        keyboard.append([
            Button('Добавить/изменить/удалить предметы', community_item_management.CommunityItemManagement,
                   source_type=SourceTypes.MOVE_SOURCE_TYPE)])
        keyboard.append([
            Button(BUTTON_BACK, self.go_back,
                   source_type=SourceTypes.HANDLER_SOURCE_TYPE),
        ])
        return keyboard

    @register_button_handler
    async def change_community_name(self, update, context):
        from school_tasker.screens import community_name_change
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_CLASS_NAME'
        return await community_name_change.CommunityNameChange().move_along_route(update, context)

    @register_button_handler
    async def change_community_password(self, update, context):
        from school_tasker.screens import community_password_change
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_CLASS_PASSWORD'
        return await community_password_change.CommunityPasswordChange().move_along_route(update, context)

    @register_button_handler
    async def go_back(self, update, context):
        from school_tasker.screens import community_selection_to_manage, main_menu
        db_length = await backend.get_count_of_user_communities_where_user_is_host(update)
        db_length = get_clean_var(db_length, 'to_int', 0, True)
        if db_length > 1:
            return await community_selection_to_manage.CommunitySelectionToManage().move(update, context)
        else:
            return await main_menu.MainMenu().move(update, context)
