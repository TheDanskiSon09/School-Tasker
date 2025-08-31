from contextlib import suppress

from emoji import is_emoji
from hammett.core import Button
from hammett.core.constants import SourceTypes, DEFAULT_STATE
from hammett.core.handlers import register_button_handler, register_typing_handler
from hammett.core.mixins import RouteMixin
from mysql.connector import IntegrityError, OperationalError, ProgrammingError

import backend
from captions import (
    BUTTON_BACK,
    BUTTON_BACK_TO_MENU,
    CHANGE_COMMUNITY_NAME_AGAIN,
    CHANGE_COMMUNITY_PASSWORD_AGAIN,
    CHANGE_ITEM_EMOJI_AGAIN,
    CHANGE_ITEM_GROUP_NUMBER_AGAIN,
    CHANGE_ITEM_NAME_AGAIN,
    CHANGE_ITEM_ROD_NAME_AGAIN,
    CREATE_MORE_ITEM,
    ENTER_TEXT_OF_TASK,
    I_CANT_MAKE_YOUR_REQUEST,
    ITEM_EMOJI_WAS_SUCCESSFULLY_CHANGED,
    ITEM_GROUP_NUMBER_WAS_SUCCESSFULLY_CHANGED,
    ITEM_NAME_WAS_SUCCESSFULLY_CHANGED,
    ITEM_ROD_NAME_WAS_SUCCESSFULLY_CHANGED,
    JOIN_TO_MORE_COMMUNITIES,
    MAKE_ANOTHER_TRY,
    NAME_OF_YOUR_COMMUNITY_WAS_SUCCESSFULLY_CHANGED,
    PASSWORD_OF_YOUR_COMMUNITY_WAS_SUCCESSFULLY_CHANGED,
    TO_SCREEN_OF_MANAGING_COMMUNITY,
    TO_THE_COMMUNITIES_SCREEN,
    TO_THE_ITEM_SCREEN,
    YOU_SUCCESSFULLY_JOINED_COMMUNITY,
    YOUR_COMMUNITY_WAS_SUCCESSFULLY_CREATED,
    YOUR_ITEM_WAS_SUCCESSFULLY_CREATED,
)
from school_tasker.screens.base import base_screen
from states import ADDING_TASK, CHANGING_TASK_DESCRIPTION
from utils import get_clean_var


class SchoolTaskAdditionDetails(base_screen.BaseScreen, RouteMixin):
    routes = (
        ({DEFAULT_STATE}, ADDING_TASK),
    )
    description = ENTER_TEXT_OF_TASK

    async def add_default_keyboard(self, update, context):
        context.user_data['CURRENT_TYPING_ACTION'] = 'ADDING_TASK'
        return [
            [
                Button(BUTTON_BACK, self.return_back,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def return_back(self, update, context):
        from school_tasker.screens import school_task_addition, school_task_change_base
        if context.user_data['CURRENT_TYPING_ACTION'] == 'CHANGING_MONTH' or context.user_data[
            'CURRENT_TYPING_ACTION'] == 'CHANGING_TASK_DESCRIPTION' or context.user_data[
            'CURRENT_TYPING_ACTION'] == 'CHANGING_GROUP_NUMBER' or context.user_data[
            'CURRENT_TYPING_ACTION'] == 'CHANGING_DAY':
            context.user_data['CURRENT_TYPING_ACTION'] = ''
            return await school_task_change_base.SchoolTaskChangeBase().move(update, context)
        else:
            context.user_data['CURRENT_TYPING_ACTION'] = ''
            return await school_task_addition.SchoolTaskAddition().move(update, context)

    @register_typing_handler
    async def handle_message(self, update, context):
        from school_tasker.screens import school_task_addition_details_month
        try:
            if context.user_data['ADDING_TASK_TASK_DESCRIPTION']:
                context.user_data['ADDING_TASK_TASK_DESCRIPTION'] += update.message.text
        except KeyError:
            context.user_data['ADDING_TASK_TASK_DESCRIPTION'] = update.message.text
        return await school_task_addition_details_month.SchoolTaskAdditionDetailsMonth().jump_along_route(update, context)
        # from school_tasker.screens import (
        #     communities_main,
        #     community_item_emoji_addition,
        #     community_item_group_addition,
        #     community_item_management,
        #     community_item_rod_name_addition,
        #     community_join,
        #     community_join_password_entry,
        #     community_management_main,
        #     community_name_creation,
        #     community_password_creation,
        #     main_menu,
        #     school_item_emoji_change,
        #     school_item_groups_change,
        #     school_item_management,
        #     school_task_addition_details_month,
        #     school_task_management_main,
        # )
        # if context.user_data['CURRENT_TYPING_ACTION'] == 'ADDING_TASK':
        #     pass
        #     try:
        #         if context.user_data['ADDING_TASK_TASK_DESCRIPTION']:
        #             context.user_data['ADDING_TASK_TASK_DESCRIPTION'] += update.message.text
        #     except KeyError:
        #         context.user_data['ADDING_TASK_TASK_DESCRIPTION'] = update.message.text
        #     return await school_task_addition_details_month.SchoolTaskAdditionDetailsMonth().jump(update, context)
        # elif context.user_data['CURRENT_TYPING_ACTION'] == 'CHANGING_CLASS_NAME':
        #     new_community_name = update.message.text.replace(' ', '')
        #     await backend.update_community_set_name_by_name(new_community_name, context)
        #     await backend.update_user_community_set_class_name_by_class_name(new_community_name, context)
        #     with suppress(OperationalError):
        #         await backend.rename_items_table(context, new_community_name)
        #         await backend.rename_tasks_table(context, new_community_name)
        #     context.user_data['CURRENT_CLASS_NAME'] = new_community_name
        #     context.user_data['CURRENT_TYPING_ACTION'] = ''
        #     return await backend.show_notification_screen(update, context, 'send',
        #                                                   NAME_OF_YOUR_COMMUNITY_WAS_SUCCESSFULLY_CHANGED,
        #                                                   [
        #                                                       [Button(CHANGE_COMMUNITY_NAME_AGAIN,
        #                                                               self.go_change_name,
        #                                                               source_type=SourceTypes.HANDLER_SOURCE_TYPE),
        #                                                        ],
        #                                                       [Button(TO_SCREEN_OF_MANAGING_COMMUNITY,
        #                                                               community_management_main.CommunityManagementMain,
        #                                                               source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                        ],
        #                                                       [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
        #                                                               source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                        ]])
        # elif context.user_data['CURRENT_TYPING_ACTION'] == 'CHANGING_TASK_DESCRIPTION':
        #     try:
        #         if context.user_data['ADDING_TASK_TASK_DESCRIPTION']:
        #             context.user_data['ADDING_TASK_TASK_DESCRIPTION'] += update.message.text
        #     except KeyError:
        #         context.user_data['ADDING_TASK_TASK_DESCRIPTION'] = update.message.text
        #     context.user_data['CURRENT_TYPING_ACTION'] = ''
        #     check_task = await backend.check_task_status(context)
        #     if not check_task:
        #         return await backend.show_notification_screen(update, context, 'send',
        #                                                       I_CANT_MAKE_YOUR_REQUEST,
        #                                                       [
        #                                                           [Button(MAKE_ANOTHER_TRY,
        #                                                                   school_task_management_main.SchoolTaskManagementMain,
        #                                                                   source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                            ],
        #                                                           [Button(BUTTON_BACK,
        #                                                                   school_task_management_main.SchoolTaskManagementMain,
        #                                                                   source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                            ]])
        #     else:
        #         await backend.update_task_description(context)
        #         item_name = await backend.get_item_name_from_tasks_by_item_index(context)
        #         item_name = get_clean_var(item_name, 'to_string', 0, True)
        #         context.user_data['ADDING_TASK_INDEX'] = await backend.get_item_index_from_items_by_main_name(context, item_name)
        #         context.user_data['ADDING_TASK_NAME'] = item_name
        #         context.user_data['ADDING_TASK_INDEX'] = get_clean_var(context.user_data['ADDING_TASK_INDEX'],
        #                                                                'to_string', 0, True)
        #         context.user_data['ADDING_TASK_GROUP_NUMBER'] = await backend.get_group_number_from_tasks_by_item_name(context, item_name)
        #         context.user_data['ADDING_TASK_GROUP_NUMBER'] = get_clean_var(
        #             context.user_data['ADDING_TASK_GROUP_NUMBER'], 'to_string', 0, True)
        #         del context.user_data['ADDING_TASK_TASK_DESCRIPTION']
        #         return await backend.send_update_notification(update, context, 'send',
        #                                                       context.user_data['ADDING_TASK_INDEX'],
        #                                                       True, 'change')
        # elif context.user_data['CURRENT_TYPING_ACTION'] == 'CHANGING_CLASS_PASSWORD':
        #     await backend.update_community_password_by_name(update, context)
        #     return await backend.show_notification_screen(update, context, 'send',
        #                                                   PASSWORD_OF_YOUR_COMMUNITY_WAS_SUCCESSFULLY_CHANGED,
        #                                                   [
        #                                                       [Button(CHANGE_COMMUNITY_PASSWORD_AGAIN,
        #                                                               self.go_change_password,
        #                                                               source_type=SourceTypes.HANDLER_SOURCE_TYPE),
        #                                                        ],
        #                                                       [Button(TO_SCREEN_OF_MANAGING_COMMUNITY,
        #                                                               community_management_main.CommunityManagementMain,
        #                                                               source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                        ],
        #                                                       [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
        #                                                               source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                        ]])
        # elif context.user_data['CURRENT_TYPING_ACTION'] == 'CHANGING_ITEM_NAME':
        #     await backend.update_items_set_main_name_by_main_name(context, update)
        #     await backend.update_tasks_set_item_name_by_item_name(context, update)
        #     context.user_data['CURRENT_TYPING_ACTION'] = ''
        #     return await backend.show_notification_screen(update, context, 'send',
        #                                                   ITEM_NAME_WAS_SUCCESSFULLY_CHANGED, [
        #                                                       [
        #                                                           Button(CHANGE_ITEM_NAME_AGAIN,
        #                                                                  self.go_change_item_name,
        #                                                                  source_type=SourceTypes.HANDLER_SOURCE_TYPE),
        #                                                       ],
        #                                                       [
        #                                                           Button(TO_THE_ITEM_SCREEN,
        #                                                                  school_item_management.SchoolItemManagement,
        #                                                                  source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                       ],
        #                                                       [
        #                                                           Button(TO_SCREEN_OF_MANAGING_COMMUNITY,
        #                                                                  community_management_main.CommunityManagementMain,
        #                                                                  source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                       ],
        #                                                       [
        #                                                           Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
        #                                                                  source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                       ],
        #                                                   ])
        # elif context.user_data['CURRENT_TYPING_ACTION'] == 'CHANGING_ITEM_ROD_NAME':
        #     await backend.update_items_set_rod_name_by_item_index(context, update)
        #     context.user_data['CURRENT_TYPING_ACTION'] = ''
        #     return await backend.show_notification_screen(update, context, 'send',
        #                                                   ITEM_ROD_NAME_WAS_SUCCESSFULLY_CHANGED,
        #                                                   [
        #                                                       [Button(
        #                                                           CHANGE_ITEM_ROD_NAME_AGAIN,
        #                                                           self.go_change_rod_name,
        #                                                           source_type=SourceTypes.HANDLER_SOURCE_TYPE),
        #                                                       ],
        #                                                       [Button(TO_THE_ITEM_SCREEN,
        #                                                               school_item_management.SchoolItemManagement,
        #                                                               source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                        ],
        #                                                       [Button(TO_SCREEN_OF_MANAGING_COMMUNITY,
        #                                                               community_management_main.CommunityManagementMain,
        #                                                               source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                        ],
        #                                                       [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
        #                                                               source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                        ]])
        # elif context.user_data['CURRENT_TYPING_ACTION'] == 'CHANGING_ITEM_GROUPS':
        #     try:
        #         if 0 < int(update.message.text) <= 98:
        #             await backend.update_items_set_groups_list_by_main_name(context, update)
        #             context.user_data['CURRENT_TYPING_ACTION'] = ''
        #             return await backend.show_notification_screen(update, context, 'send',
        #                                                           ITEM_GROUP_NUMBER_WAS_SUCCESSFULLY_CHANGED,
        #                                                           [
        #                                                               [Button(
        #                                                                   CHANGE_ITEM_GROUP_NUMBER_AGAIN,
        #                                                                   self.go_change_groups,
        #                                                                   source_type=SourceTypes.HANDLER_SOURCE_TYPE),
        #                                                               ],
        #                                                               [Button(TO_THE_ITEM_SCREEN,
        #                                                                       school_item_management.SchoolItemManagement,
        #                                                                       source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                                ],
        #                                                               [Button(TO_SCREEN_OF_MANAGING_COMMUNITY,
        #                                                                       community_management_main.CommunityManagementMain,
        #                                                                       source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                                ],
        #                                                               [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
        #                                                                       source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                                ],
        #                                                           ])
        #         else:
        #             return await school_item_groups_change.SchoolItemGroupsChange().jump(update, context)
        #     except ValueError:
        #         return await school_item_groups_change.SchoolItemGroupsChange().jump(update, context)
        # elif context.user_data['CURRENT_TYPING_ACTION'] == 'CHANGING_ITEM_EMOJI':
        #     if len(update.message.text) - 1 == 1 and is_emoji(update.message.text):
        #         context.user_data['CURRENT_TYPING_ACTION'] = ''
        #         await backend.update_items_set_emoji_by_main_name(context, update)
        #         return await backend.show_notification_screen(update, context, 'send',
        #                                                       ITEM_EMOJI_WAS_SUCCESSFULLY_CHANGED, [
        #                                                           [Button(CHANGE_ITEM_EMOJI_AGAIN,
        #                                                                   self.go_change_emoji,
        #                                                                   source_type=SourceTypes.HANDLER_SOURCE_TYPE),
        #                                                            ],
        #                                                           [Button(TO_THE_ITEM_SCREEN,
        #                                                                   school_item_management.SchoolItemManagement,
        #                                                                   source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                            ],
        #                                                           [Button(TO_SCREEN_OF_MANAGING_COMMUNITY,
        #                                                                   community_management_main.CommunityManagementMain,
        #                                                                   source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                            ],
        #                                                           [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
        #                                                                   source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                            ],
        #                                                       ])
        #     else:
        #         return await school_item_emoji_change.SchoolItemEmojiChange().jump(update, context)
        # elif context.user_data['CURRENT_TYPING_ACTION'] == 'CREATING_ITEM_EMOJI':
        #     if len(update.message.text) - 1 == 1 and is_emoji(update.message.text):
        #         context.user_data['CURRENT_TYPING_ACTION'] = ''
        #         context.user_data['CREATING_ITEM_EMOJI'] = update.message.text
        #         await backend.create_new_school_item(context)
        #         return await backend.show_notification_screen(update, context, 'send',
        #                                                       YOUR_ITEM_WAS_SUCCESSFULLY_CREATED,
        #                                                       [
        #                                                           [Button(CREATE_MORE_ITEM,
        #                                                                   self.go_create_more_items,
        #                                                                   source_type=SourceTypes.HANDLER_SOURCE_TYPE),
        #                                                            ],
        #                                                           [Button(TO_THE_ITEM_SCREEN,
        #                                                                   community_item_management.CommunityItemManagement,
        #                                                                   source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                            ],
        #                                                           [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
        #                                                                   source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                            ]])
        #     else:
        #         return await community_item_emoji_addition.CommunityItemEmojiAddition().jump_along_route(update, context)
        # elif context.user_data['CURRENT_TYPING_ACTION'] == 'CREATING_ITEM_NAME':
        #     context.user_data['CREATING_ITEM_NAME'] = update.message.text
        #     context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_ITEM_ROD_NAME'
        #     return await community_item_rod_name_addition.CommunityItemRodNameAddition().jump_along_route(update, context)
        # elif context.user_data['CURRENT_TYPING_ACTION'] == 'CREATING_ITEM_ROD_NAME':
        #     context.user_data['CREATING_ITEM_ROD_NAME'] = update.message.text
        #     context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_ITEM_GROUP'
        #     return await community_item_group_addition.CommunityItemGroupAddition().jump(update, context)
        # elif context.user_data['CURRENT_TYPING_ACTION'] == 'CREATING_ITEM_GROUP':
        #     try:
        #         if 0 < int(update.message.text) <= 98:
        #             context.user_data['CREATING_ITEM_GROUPS'] = update.message.text
        #             context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_ITEM_EMOJI'
        #             return await community_item_emoji_addition.CommunityItemEmojiAddition().jump_along_route(update, context)
        #         return await community_item_group_addition.CommunityItemGroupAddition().jump(update, context)
        #     except ValueError:
        #         return await community_item_group_addition.CommunityItemGroupAddition().jump(update, context)
        # elif context.user_data['CURRENT_TYPING_ACTION'] == 'CREATING_CLASS':
        #     context.user_data['CURRENT_CLASS_NAME'] = update.message.text
        #     context.user_data['CURRENT_CLASS_NAME'] = context.user_data['CURRENT_CLASS_NAME'].replace(' ', '')
        #     context.user_data['CURRENT_TYPING_ACTION'] = 'ADDING_PASSWORD_TO_CLASS'
        #     return await community_password_creation.CommunityPasswordCreation().jump_along_route(update, context)
        # elif context.user_data['CURRENT_TYPING_ACTION'] == 'ADDING_PASSWORD_TO_CLASS':
        #     try:
        #         context.user_data['CURRENT_CLASS_PASSWORD'] = update.message.text
        #         context.user_data['CURRENT_TYPING_ACTION'] = ''
        #         await backend.create_community_table(context)
        #         await backend.create_tasks_table(context)
        #         await backend.create_items_table(context)
        #         await backend.add_new_community(update, context)
        #         return await backend.show_notification_screen(update, context, 'send',
        #                                                       YOUR_COMMUNITY_WAS_SUCCESSFULLY_CREATED,
        #                                                       [
        #                                                           [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
        #                                                                   source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                            ]])
        #     except IntegrityError:
        #         context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_CLASS'
        #         return await community_name_creation.CommunityNameCreation().jump(update, context)
        #     except ProgrammingError:
        #         return await backend.show_notification_screen(update, context, 'send',
        #                                                       YOUR_COMMUNITY_WAS_SUCCESSFULLY_CREATED,
        #                                                       [
        #                                                           [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
        #                                                                   source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                            ]])
        # elif context.user_data['CURRENT_TYPING_ACTION'] == 'WRITING_PASSWORD_TO_JOIN':
        #     if update.message.text == context.user_data['ENTER_COMMUNITY_PASSWORD']:
        #         await backend.add_user_to_community(update, context)
        #         context.user_data['CURRENT_TYPING_ACTION'] = ''
        #         return await backend.show_notification_screen(update, context, 'send',
        #                                                       YOU_SUCCESSFULLY_JOINED_COMMUNITY, [
        #                                                           [
        #                                                               Button(JOIN_TO_MORE_COMMUNITIES,
        #                                                                      community_join.CommunityJoin,
        #                                                                      source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                           ],
        #                                                           [
        #                                                               Button(TO_THE_COMMUNITIES_SCREEN,
        #                                                                      communitites_main.CommunitiesMain,
        #                                                                      source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                           ],
        #                                                           [
        #                                                               Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
        #                                                                      source_type=SourceTypes.MOVE_SOURCE_TYPE),
        #                                                           ],
        #                                                       ])
        #     else:
        #         return await community_join_password_entry.CommunityJoinPasswordEntry().jump(update, context)

    @register_button_handler
    async def go_create_more_items(self, update, context):
        from school_tasker.screens import community_item_name_addition
        context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_ITEM_NAME'
        return await community_item_name_addition.CommunityItemNameAddition().move_along_route(update, context)

    @register_button_handler
    async def go_change_password(self, update, context):
        from school_tasker.screens import community_password_change
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_CLASS_PASSWORD'
        return await community_password_change.CommunityPasswordChange().move_along_route(update, context)

    @register_button_handler
    async def go_change_rod_name(self, update, context):
        from school_tasker.screens import school_item_rod_name_change
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_ITEM_ROD_NAME'
        return await school_item_rod_name_change.SchoolItemRodNameChange().move_along_route(update, context)

    @register_button_handler
    async def go_change_item_name(self, update, context):
        from school_tasker.screens import school_item_name_change
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_ITEM_NAME'
        return await school_item_name_change.SchoolItemNameChange().move_along_route(update, context)

    @register_button_handler
    async def go_change_name(self, update, context):
        from school_tasker.screens import community_name_change
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_CLASS_NAME'
        return await community_name_change.CommunityNameChange().move_along_route(update, context)

    @register_button_handler
    async def go_change_groups(self, update, context):
        from school_tasker.screens import school_item_groups_change
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_ITEM_GROUPS'
        return await school_item_groups_change.SchoolItemGroupsChange().move_along_route(update, context)

    @register_button_handler
    async def go_change_emoji(self, update, context):
        from school_tasker.screens import school_item_emoji_change
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_ITEM_EMOJI'
        return await school_item_emoji_change.SchoolItemEmojiChange().move_along_route(update, context)
