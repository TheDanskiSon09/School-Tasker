from contextlib import suppress

from emoji import is_emoji
from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler, register_typing_handler
from mysql.connector import OperationalError, IntegrityError, ProgrammingError

import backend
from constants import BUTTON_BACK, BUTTON_BACK_TO_MENU, ENTER_TEXT_OF_TASK, \
    NAME_OF_YOUR_COMMUNITY_WAS_SUCCESSFULLY_CHANGED, CHANGE_COMMUNITY_NAME_AGAIN, TO_SCREEN_OF_MANAGING_COMMUNITY, \
    I_CANT_MAKE_YOUR_REQUEST, MAKE_ANOTHER_TRY, PASSWORD_OF_YOUR_COMMUNITY_WAS_SUCCESSFULLY_CHANGED, \
    CHANGE_COMMUNITY_PASSWORD_AGAIN, ITEM_NAME_WAS_SUCCESSFULLY_CHANGED, CHANGE_ITEM_NAME_AGAIN, TO_THE_ITEM_SCREEN, \
    ITEM_ROD_NAME_WAS_SUCCESSFULLY_CHANGED, CHANGE_ITEM_ROD_NAME_AGAIN, ITEM_GROUP_NUMBER_WAS_SUCCESSFULLY_CHANGED, \
    CHANGE_ITEM_GROUP_NUMBER_AGAIN, ITEM_EMOJI_WAS_SUCCESSFULLY_CHANGED, CHANGE_ITEM_EMOJI_AGAIN, \
    YOUR_ITEM_WAS_SUCCESSFULLY_CREATED, CREATE_MORE_ITEM, YOUR_COMMUNITY_WAS_SUCCESSFULLY_CREATED, \
    YOU_SUCCESSFULLY_JOINED_COMMUNITY, JOIN_TO_MORE_COMMUNITIES, TO_THE_COMMUNITIES_SCREEN
from school_tasker.screens.base import base_screen
from utils import get_clean_var, generate_id


class SchoolTaskAdditionDetails(base_screen.BaseScreen):
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
        from school_tasker.screens import school_task_change_base, school_task_addition
        if context.user_data['CURRENT_TYPING_ACTION'] == "CHANGING_MONTH" or context.user_data[
            'CURRENT_TYPING_ACTION'] == 'CHANGING_TASK_DESCRIPTION' or context.user_data[
            'CURRENT_TYPING_ACTION'] == 'CHANGING_GROUP_NUMBER' or context.user_data[
            'CURRENT_TYPING_ACTION'] == 'CHANGING_DAY':
            context.user_data['CURRENT_TYPING_ACTION'] = ''
            return await school_task_change_base.SchoolTaskChangeBase().move(update, context)
        else:
            context.user_data['CURRENT_TYPING_ACTION'] = ''
            return await school_task_addition.SchoolTaskAddition().move(update, context)

    @register_typing_handler
    async def set_details(self, update, context):
        from school_tasker.screens import communitites_main, school_task_addition_details_month
        from school_tasker.screens import community_item_emoji_addition
        from school_tasker.screens import community_item_group_addition
        from school_tasker.screens import community_item_management
        from school_tasker.screens import community_item_rod_name_addition
        from school_tasker.screens import community_join
        from school_tasker.screens import community_join_password_entry
        from school_tasker.screens import community_management_main
        from school_tasker.screens import community_name_creation
        from school_tasker.screens import community_password_creation
        from school_tasker.screens import main_menu
        from school_tasker.screens import school_item_emoji_change
        from school_tasker.screens import school_item_groups_change
        from school_tasker.screens import school_item_management
        from school_tasker.screens import school_task_management_main
        if context.user_data['CURRENT_TYPING_ACTION'] == 'ADDING_TASK':
            context.user_data["ADDING_TASK_TASK_DESCRIPTION"] = update.message.text
            return await school_task_addition_details_month.SchoolTaskAdditionDetailsMonth().jump(update, context)
        elif context.user_data['CURRENT_TYPING_ACTION'] == 'CHANGING_CLASS_NAME':
            new_community_name = update.message.text.replace(' ', '')
            await backend.execute_query('UPDATE Community SET name = %s WHERE name = %s',
                                   (new_community_name, context.user_data['CURRENT_CLASS_NAME'],))
            await backend.execute_query('UPDATE UserCommunities SET class_name = %s WHERE class_name = %s',
                                   (new_community_name, context.user_data['CURRENT_CLASS_NAME'],))
            # backend.cursor.execute('UPDATE Community SET name = %s WHERE name = %s',
            #                        (new_community_name, context.user_data['CURRENT_CLASS_NAME'],))
            # backend.cursor.execute('UPDATE UserCommunities SET class_name = %s WHERE class_name = %s',
            #                        (new_community_name, context.user_data['CURRENT_CLASS_NAME'],))
            with suppress(OperationalError):
                await backend.execute_query('ALTER TABLE ' + context.user_data[
                    'CURRENT_CLASS_NAME'] + '_Items RENAME TO ' + new_community_name + '_Items')
                await backend.execute_query('ALTER TABLE ' + context.user_data[
                    'CURRENT_CLASS_NAME'] + '_Tasks RENAME TO ' + new_community_name + '_Tasks')
                # backend.cursor.execute('ALTER TABLE ' + context.user_data[
                #     'CURRENT_CLASS_NAME'] + '_Items RENAME TO ' + new_community_name + '_Items')
                # backend.cursor.execute('ALTER TABLE ' + context.user_data[
                #     'CURRENT_CLASS_NAME'] + '_Tasks RENAME TO ' + new_community_name + '_Tasks')
                # backend.connection.commit()
            context.user_data['CURRENT_CLASS_NAME'] = new_community_name
            context.user_data['CURRENT_TYPING_ACTION'] = ''
            return await backend.show_notification_screen(update, context, 'send',
                                                          NAME_OF_YOUR_COMMUNITY_WAS_SUCCESSFULLY_CHANGED,
                                                          [
                                                              [Button(CHANGE_COMMUNITY_NAME_AGAIN,
                                                                      self.go_change_name,
                                                                      source_type=SourceTypes.HANDLER_SOURCE_TYPE)
                                                               ],
                                                              [Button(TO_SCREEN_OF_MANAGING_COMMUNITY,
                                                                      community_management_main.CommunityManagementMain,
                                                                      source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                               ],
                                                              [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                      source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                               ]])
        elif context.user_data['CURRENT_TYPING_ACTION'] == 'CHANGING_TASK_DESCRIPTION':
            context.user_data['ADDING_TASK_TASK_DESCRIPTION'] = update.message.text
            context.user_data['CURRENT_TYPING_ACTION'] = ''
            check_task = await backend.check_task_status(context)
            if not check_task:
                return await backend.show_notification_screen(update, context, 'send',
                                                              I_CANT_MAKE_YOUR_REQUEST,
                                                              [
                                                                  [Button(MAKE_ANOTHER_TRY,
                                                                          school_task_management_main.SchoolTaskManagementMain,
                                                                          source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                                   ],
                                                                  [Button(BUTTON_BACK, school_task_management_main.SchoolTaskManagementMain,
                                                                          source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                                   ]])
            else:
                await backend.execute_query('UPDATE ' + context.user_data[
                        'CURRENT_CLASS_NAME'] + '_Tasks SET task_description = %s WHERE item_index = %s',
                    (context.user_data['ADDING_TASK_TASK_DESCRIPTION'], context.user_data['ADDING_TASK_INDEX'],))
                item_name = await backend.execute_query('SELECT item_name FROM ' + context.user_data[
                        'CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
                    (context.user_data['ADDING_TASK_INDEX'],))
                # backend.cursor.execute(
                #     'UPDATE ' + context.user_data[
                #         'CURRENT_CLASS_NAME'] + '_Tasks SET task_description = %s WHERE item_index = %s',
                #     (context.user_data['ADDING_TASK_TASK_DESCRIPTION'], context.user_data['ADDING_TASK_INDEX'],))
                # backend.connection.commit()
                # backend.cursor.execute(
                #     'SELECT item_name FROM ' + context.user_data[
                #         'CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
                #     (context.user_data['ADDING_TASK_INDEX'],))
                # item_name = backend.cursor.fetchall()
                item_name = get_clean_var(item_name, 'to_string', 0, True)
                context.user_data['ADDING_TASK_INDEX'] = await backend.execute_query('SELECT item_index FROM ' + context.user_data[
                        'CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
                    (item_name,))
                # backend.cursor.execute(
                #     'SELECT item_index FROM ' + context.user_data[
                #         'CURRENT_CLASS_NAME'] + '_Items WHERE main_name = %s',
                #     (item_name,))
                # context.user_data['ADDING_TASK_INDEX'] = backend.cursor.fetchall()
                context.user_data['ADDING_TASK_NAME'] = item_name
                context.user_data['ADDING_TASK_INDEX'] = get_clean_var(context.user_data['ADDING_TASK_INDEX'],
                                                                        'to_string', 0, True)
                context.user_data['ADDING_TASK_GROUP_NUMBER'] = await backend.execute_query('SELECT group_number FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks '
                                                                                                               'WHERE item_name = %s',
                                       (item_name,))
                # backend.cursor.execute('SELECT group_number FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks '
                #                                                                                                'WHERE item_name = %s',
                #                        (item_name,))
                # context.user_data['ADDING_TASK_GROUP_NUMBER'] = backend.cursor.fetchall()
                context.user_data['ADDING_TASK_GROUP_NUMBER'] = get_clean_var(
                    context.user_data['ADDING_TASK_GROUP_NUMBER'], 'to_string', 0, True)
                return await backend.send_update_notification(update, context, 'change',
                                                              context.user_data['ADDING_TASK_INDEX'],
                                                              True)
        elif context.user_data['CURRENT_TYPING_ACTION'] == 'CHANGING_CLASS_PASSWORD':
            await backend.execute_query('UPDATE Community set password = %s WHERE name = %s',
                                   (update.message.text, context.user_data['CURRENT_CLASS_NAME'],))
            # backend.cursor.execute('UPDATE Community set password = %s WHERE name = %s',
            #                        (update.message.text, context.user_data['CURRENT_CLASS_NAME'],))
            # backend.connection.commit()
            return await backend.show_notification_screen(update, context, 'send',
                                                          PASSWORD_OF_YOUR_COMMUNITY_WAS_SUCCESSFULLY_CHANGED,
                                                          [
                                                              [Button(CHANGE_COMMUNITY_PASSWORD_AGAIN,
                                                                      self.go_change_password,
                                                                      source_type=SourceTypes.HANDLER_SOURCE_TYPE)
                                                               ],
                                                              [Button(TO_SCREEN_OF_MANAGING_COMMUNITY ,
                                                                      community_management_main.CommunityManagementMain,
                                                                      source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                               ],
                                                              [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                      source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                               ]])
        elif context.user_data['CURRENT_TYPING_ACTION'] == 'CHANGING_ITEM_NAME':
            # backend.cursor.execute('UPDATE ' + context.user_data[
            #     'CURRENT_CLASS_NAME'] + '_Items SET main_name = %s WHERE main_name = %s',
            #                        (update.message.text, context.user_data['MANAGE_ITEM_MAIN_NAME']))
            # backend.cursor.execute('UPDATE ' + context.user_data[
            #     'CURRENT_CLASS_NAME'] + '_Tasks SET item_name = %s WHERE item_name = %s',
            #                        (update.message.text, context.user_data['MANAGE_ITEM_MAIN_NAME'],))
            # backend.connection.commit()
            await backend.execute_query('UPDATE ' + context.user_data[
                'CURRENT_CLASS_NAME'] + '_Items SET main_name = %s WHERE main_name = %s',
                                   (update.message.text, context.user_data['MANAGE_ITEM_MAIN_NAME']))
            await backend.execute_query('UPDATE ' + context.user_data[
                'CURRENT_CLASS_NAME'] + '_Tasks SET item_name = %s WHERE item_name = %s',
                                   (update.message.text, context.user_data['MANAGE_ITEM_MAIN_NAME'],))
            context.user_data['CURRENT_TYPING_ACTION'] = ''
            return await backend.show_notification_screen(update, context, 'send',
                                                          ITEM_NAME_WAS_SUCCESSFULLY_CHANGED, [
                                                              [
                                                                  Button(CHANGE_ITEM_NAME_AGAIN,
                                                                         self.go_change_item_name,
                                                                         source_type=SourceTypes.HANDLER_SOURCE_TYPE)
                                                              ],
                                                              [
                                                                  Button(TO_THE_ITEM_SCREEN,
                                                                         school_item_management.SchoolItemManagement,
                                                                         source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                              ],
                                                              [
                                                                  Button(TO_SCREEN_OF_MANAGING_COMMUNITY,
                                                                         community_management_main.CommunityManagementMain,
                                                                         source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                              ],
                                                              [
                                                                  Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                         source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                              ]
                                                          ])
        elif context.user_data['CURRENT_TYPING_ACTION'] == 'CHANGING_ITEM_ROD_NAME':
            # backend.cursor.execute('UPDATE ' + context.user_data[
            #     'CURRENT_CLASS_NAME'] + '_Items SET rod_name = %s WHERE item_index = %s',
            #                        (update.message.text, context.user_data['MANAGE_ITEM_INDEX']))
            # backend.connection.commit()
            await backend.execute_query('UPDATE ' + context.user_data[
                'CURRENT_CLASS_NAME'] + '_Items SET rod_name = %s WHERE item_index = %s',
                                   (update.message.text, context.user_data['MANAGE_ITEM_INDEX']))
            context.user_data['CURRENT_TYPING_ACTION'] = ''
            return await backend.show_notification_screen(update, context, 'send',
                                                          ITEM_ROD_NAME_WAS_SUCCESSFULLY_CHANGED,
                                                          [
                                                              [Button(
                                                                  CHANGE_ITEM_ROD_NAME_AGAIN,
                                                                  self.go_change_rod_name,
                                                                  source_type=SourceTypes.HANDLER_SOURCE_TYPE)
                                                              ],
                                                              [Button(TO_THE_ITEM_SCREEN,
                                                                      school_item_management.SchoolItemManagement,
                                                                      source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                               ],
                                                              [Button(TO_SCREEN_OF_MANAGING_COMMUNITY,
                                                                      community_management_main.CommunityManagementMain,
                                                                      source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                               ],
                                                              [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                      source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                               ]])
        elif context.user_data['CURRENT_TYPING_ACTION'] == 'CHANGING_ITEM_GROUPS':
            try:
                if 0 < int(update.message.text) <= 98:
                    # backend.cursor.execute('UPDATE ' + context.user_data[
                    #     'CURRENT_CLASS_NAME'] + '_Items SET groups_list = %s WHERE main_name = %s',
                    #                        (update.message.text, context.user_data['MANAGE_ITEM_MAIN_NAME'],))
                    # backend.connection.commit()
                    await backend.execute_query('UPDATE ' + context.user_data[
                        'CURRENT_CLASS_NAME'] + '_Items SET groups_list = %s WHERE main_name = %s',
                                           (update.message.text, context.user_data['MANAGE_ITEM_MAIN_NAME'],))
                    context.user_data['CURRENT_TYPING_ACTION'] = ''
                    return await backend.show_notification_screen(update, context, 'send',
                                                                  ITEM_GROUP_NUMBER_WAS_SUCCESSFULLY_CHANGED,
                                                                  [
                                                                      [Button(
                                                                          CHANGE_ITEM_GROUP_NUMBER_AGAIN,
                                                                          self.go_change_groups,
                                                                          source_type=SourceTypes.HANDLER_SOURCE_TYPE)
                                                                       ],
                                                                      [Button(TO_THE_ITEM_SCREEN,
                                                                              school_item_management.SchoolItemManagement,
                                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                                       ],
                                                                      [Button(TO_SCREEN_OF_MANAGING_COMMUNITY,
                                                                              community_management_main.CommunityManagementMain,
                                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                                       ],
                                                                      [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                                       ]
                                                                  ])
                else:
                    return await school_item_groups_change.SchoolItemGroupsChange().jump(update, context)
            except ValueError:
                return await school_item_groups_change.SchoolItemGroupsChange().jump(update, context)
        elif context.user_data['CURRENT_TYPING_ACTION'] == 'CHANGING_ITEM_EMOJI':
            if len(update.message.text) - 1 == 1 and is_emoji(update.message.text):
                context.user_data['CURRENT_TYPING_ACTION'] = ''
                await backend.execute_query('UPDATE ' + context.user_data[
                    'CURRENT_CLASS_NAME'] + '_Items SET emoji = %s WHERE main_name = %s',
                                       (update.message.text, context.user_data['MANAGE_ITEM_MAIN_NAME'],))
                # backend.cursor.execute('UPDATE ' + context.user_data[
                #     'CURRENT_CLASS_NAME'] + '_Items SET emoji = %s WHERE main_name = %s',
                #                        (update.message.text, context.user_data['MANAGE_ITEM_MAIN_NAME'],))
                # backend.connection.commit()
                return await backend.show_notification_screen(update, context, 'send',
                                                              ITEM_EMOJI_WAS_SUCCESSFULLY_CHANGED, [
                                                                  [Button(CHANGE_ITEM_EMOJI_AGAIN,
                                                                          self.go_change_emoji,
                                                                          source_type=SourceTypes.HANDLER_SOURCE_TYPE)
                                                                   ],
                                                                  [Button(TO_THE_ITEM_SCREEN,
                                                                          school_item_management.SchoolItemManagement,
                                                                          source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                                   ],
                                                                  [Button(TO_SCREEN_OF_MANAGING_COMMUNITY,
                                                                          community_management_main.CommunityManagementMain,
                                                                          source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                                   ],
                                                                  [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                          source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                                   ]
                                                              ])
            else:
                return await school_item_emoji_change.SchoolItemEmojiChange().jump(update, context)
        elif context.user_data['CURRENT_TYPING_ACTION'] == 'CREATING_ITEM_EMOJI':
            if len(update.message.text) - 1 == 1 and is_emoji(update.message.text):
                context.user_data['CURRENT_TYPING_ACTION'] = ''
                context.user_data['CREATING_ITEM_EMOJI'] = update.message.text
                await backend.execute_query('INSERT INTO ' + context.user_data[
                    'CURRENT_CLASS_NAME'] + '_Items (item_index, emoji, main_name, rod_name, groups_list) VALUES (%s, %s, %s, '
                                            '%s, %s)',
                                       (generate_id(), context.user_data['CREATING_ITEM_EMOJI'],
                                        context.user_data['CREATING_ITEM_NAME'],
                                        context.user_data['CREATING_ITEM_ROD_NAME'],
                                        context.user_data['CREATING_ITEM_GROUPS']))
                # backend.cursor.execute('INSERT INTO ' + context.user_data[
                #     'CURRENT_CLASS_NAME'] + '_Items (item_index, emoji, main_name, rod_name, groups_list) VALUES (%s, %s, %s, '
                #                             '%s, %s)',
                #                        (generate_id(), context.user_data['CREATING_ITEM_EMOJI'],
                #                         context.user_data['CREATING_ITEM_NAME'],
                #                         context.user_data['CREATING_ITEM_ROD_NAME'],
                #                         context.user_data['CREATING_ITEM_GROUPS']), )
                # backend.connection.commit()
                return await backend.show_notification_screen(update, context, 'send',
                                                              YOUR_ITEM_WAS_SUCCESSFULLY_CREATED,
                                                              [
                                                                  [Button(CREATE_MORE_ITEM,
                                                                          self.go_create_more_items,
                                                                          source_type=SourceTypes.HANDLER_SOURCE_TYPE)
                                                                   ],
                                                                  [Button(TO_THE_ITEM_SCREEN, community_item_management.CommunityItemManagement,
                                                                          source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                                   ],
                                                                  [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                          source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                                   ]])
            else:
                return await community_item_emoji_addition.CommunityItemEmojiAddition().jump(update, context)
        elif context.user_data['CURRENT_TYPING_ACTION'] == 'CREATING_ITEM_NAME':
            context.user_data['CREATING_ITEM_NAME'] = update.message.text
            context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_ITEM_ROD_NAME'
            return await community_item_rod_name_addition.CommunityItemRodNameAddition().jump(update, context)
        elif context.user_data['CURRENT_TYPING_ACTION'] == 'CREATING_ITEM_ROD_NAME':
            context.user_data['CREATING_ITEM_ROD_NAME'] = update.message.text
            context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_ITEM_GROUP'
            return await community_item_group_addition.CommunityItemGroupAddition().jump(update, context)
        elif context.user_data['CURRENT_TYPING_ACTION'] == 'CREATING_ITEM_GROUP':
            try:
                if 0 < int(update.message.text) <= 98:
                    context.user_data['CREATING_ITEM_GROUPS'] = update.message.text
                    context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_ITEM_EMOJI'
                    return await community_item_emoji_addition.CommunityItemEmojiAddition().jump(update, context)
                return await community_item_group_addition.CommunityItemGroupAddition().jump(update, context)
            except ValueError:
                return await community_item_group_addition.CommunityItemGroupAddition().jump(update, context)
        elif context.user_data['CURRENT_TYPING_ACTION'] == "CREATING_CLASS":
            context.user_data['CURRENT_CLASS_NAME'] = update.message.text
            context.user_data['CURRENT_CLASS_NAME'] = context.user_data['CURRENT_CLASS_NAME'].replace(' ', '')
            context.user_data['CURRENT_TYPING_ACTION'] = 'ADDING_PASSWORD_TO_CLASS'
            return await community_password_creation.CommunityPasswordCreation().jump(update, context)
        elif context.user_data['CURRENT_TYPING_ACTION'] == 'ADDING_PASSWORD_TO_CLASS':
            try:
                context.user_data['CURRENT_CLASS_PASSWORD'] = update.message.text
                context.user_data['CURRENT_TYPING_ACTION'] = ''
                await backend.execute_query('INSERT INTO Community (name, password) VALUES (%s,%s)',
                                       (context.user_data['CURRENT_CLASS_NAME'],
                                        context.user_data['CURRENT_CLASS_PASSWORD']))
                await backend.execute_query('''
                CREATE TABLE IF NOT EXISTS ''' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks' + ''' (
                item_name TEXT,
                item_index TEXT,
                group_number TEXT,
                task_description TEXT,
                task_day TEXT,
                task_month TEXT,
                task_year TEXT,
                hypertime TEXT
                )
                ''')
                # backend.cursor.execute('INSERT INTO Community (name, password) VALUES (%s,%s)',
                #                        (context.user_data['CURRENT_CLASS_NAME'],
                #                         context.user_data['CURRENT_CLASS_PASSWORD']))
                # backend.connection.commit()
                # backend.cursor.execute('''
                # CREATE TABLE IF NOT EXISTS ''' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks' + ''' (
                # item_name TEXT,
                # item_index TEXT,
                # group_number TEXT,
                # task_description TEXT,
                # task_day TEXT,
                # task_month TEXT,
                # task_year TEXT,
                # hypertime TEXT
                # )
                # ''')
                await backend.execute_query('''
                                             CREATE TABLE IF NOT EXISTS ''' + context.user_data[
                        'CURRENT_CLASS_NAME'] + '_Items' + ''' (
                                            item_index TEXT,
                                            emoji TEXT,
                                            main_name VARCHAR(255) UNIQUE,
                                            rod_name VARCHAR(255) UNIQUE,
                                            groups_list TEXT
                                            )
                                            ''')
                # backend.cursor.execute('''
                #                             CREATE TABLE IF NOT EXISTS ''' + context.user_data[
                #         'CURRENT_CLASS_NAME'] + '_Items' + ''' (
                #                             item_index TEXT,
                #                             emoji TEXT,
                #                             main_name VARCHAR(255) UNIQUE,
                #                             rod_name VARCHAR(255) UNIQUE,
                #                             groups_list TEXT
                #                             )
                #                             ''')
                await backend.execute_query('INSERT INTO UserCommunities (user_id, class_name, user_role_in_class) VALUES (%s,%s,%s)',
                    (update.message.chat.id, context.user_data['CURRENT_CLASS_NAME'], "HOST"))
                # backend.cursor.execute(
                #     'INSERT INTO UserCommunities (user_id, class_name, user_role_in_class) VALUES (%s,%s,%s)',
                #     (update.message.chat.id, context.user_data['CURRENT_CLASS_NAME'], "HOST"))
                # backend.connection.commit()
                return await backend.show_notification_screen(update, context, 'send',
                                                                YOUR_COMMUNITY_WAS_SUCCESSFULLY_CREATED,
                                                                [
                                                                    [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                              source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                                    ]])
            except IntegrityError:
                context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_CLASS'
                return await community_name_creation.CommunityNameCreation().jump(update, context)
            except ProgrammingError:
                pass
                # await backend.execute_query('DROP TABLE ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks')
                # await backend.execute_query('DROP TABLE ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items')
                # backend.cursor.execute('DROP TABLE ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks')
                # backend.cursor.execute('DROP TABLE ' + context.user_data['CURRENT_CLASS_NAME'] + '_Items')
                # backend.connection.commit()
                return await backend.show_notification_screen(update, context, 'send',
                                                              YOUR_COMMUNITY_WAS_SUCCESSFULLY_CREATED,
                                                              [
                                                                  [Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                          source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                                   ]])
        elif context.user_data['CURRENT_TYPING_ACTION'] == 'WRITING_PASSWORD_TO_JOIN':
            if update.message.text == context.user_data['ENTER_COMMUNITY_PASSWORD']:
                await backend.execute_query('INSERT INTO UserCommunities (user_id, class_name, user_role_in_class) VALUES (%s,%s,%s)',
                    (update.effective_user.id, context.user_data['ENTER_COMMUNITY_NAME'], 'ANONIM'))
                # backend.cursor.execute(
                #     'INSERT INTO UserCommunities (user_id, class_name, user_role_in_class) VALUES (%s,%s,%s)',
                #     (update.effective_user.id, context.user_data['ENTER_COMMUNITY_NAME'], 'ANONIM'))
                # backend.connection.commit()
                context.user_data['CURRENT_TYPING_ACTION'] = ''
                return await backend.show_notification_screen(update, context, 'send',
                                                              YOU_SUCCESSFULLY_JOINED_COMMUNITY, [
                                                                  [
                                                                      Button(JOIN_TO_MORE_COMMUNITIES, community_join.CommunityJoin,
                                                                             source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                                  ],
                                                                  [
                                                                      Button(TO_THE_COMMUNITIES_SCREEN, communitites_main.CommunitiesMain,
                                                                             source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                                  ],
                                                                  [
                                                                      Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu,
                                                                             source_type=SourceTypes.MOVE_SOURCE_TYPE)
                                                                  ]
                                                              ])
            else:
                return await community_join_password_entry.CommunityJoinPasswordEntry().jump(update, context)

    @register_button_handler
    async def go_create_more_items(self, update, context):
        from school_tasker.screens import community_item_name_addition
        context.user_data['CURRENT_TYPING_ACTION'] = 'CREATING_ITEM_NAME'
        return await community_item_name_addition.CommunityItemNameAddition().move(update, context)

    @register_button_handler
    async def go_change_password(self, update, context):
        from school_tasker.screens import community_password_change
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_CLASS_PASSWORD'
        return await community_password_change.CommunityPasswordChange().move(update, context)

    @register_button_handler
    async def go_change_rod_name(self, update, context):
        from school_tasker.screens import school_item_rod_name_change
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_ITEM_ROD_NAME'
        return await school_item_rod_name_change.SchoolItemRodNameChange().move(update, context)

    @register_button_handler
    async def go_change_item_name(self, update, context):
        from school_tasker.screens import school_item_name_change
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_ITEM_NAME'
        return await school_item_name_change.SchoolItemNameChange().move(update, context)

    @register_button_handler
    async def go_change_name(self, update, context):
        from school_tasker.screens import community_name_change
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_CLASS_NAME'
        return await community_name_change.CommunityNameChange().move(update, context)

    @register_button_handler
    async def go_change_groups(self, update, context):
        from school_tasker.screens import school_item_groups_change
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_ITEM_GROUPS'
        return await school_item_groups_change.SchoolItemGroupsChange().move(update, context)

    @register_button_handler
    async def go_change_emoji(self, update, context):
        from school_tasker.screens import school_item_emoji_change
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGING_ITEM_EMOJI'
        return await school_item_emoji_change.SchoolItemEmojiChange().move(update, context)
