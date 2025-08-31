from datetime import datetime
from json import dumps
from os import listdir
from os.path import exists
from shutil import rmtree

from bs4 import BeautifulSoup
from hammett.conf import settings
from hammett.core import Button
from hammett.core.constants import RenderConfig, SourceTypes
from hammett.core.exceptions import ScreenDescriptionIsEmpty
from hammett.core.handlers import register_button_handler
from telegram.error import BadRequest

import backend
from captions import BUTTON_BACK, THERE_IS_NO_SCHOOL_TASKS_FOR_NOW
from school_tasker.screens.base import base_screen
from utils import get_clean_var, get_payload_safe, load_html_markers, save_html_markers


class SchoolTasks(base_screen.BaseScreen):

    async def check_tasks(self, update, context, target_screen):
        from school_tasker.screens import main_menu
        new_config = RenderConfig()
        new_config.keyboard = []
        database_length = await backend.get_var_from_database(None, 'database_length_SchoolTasker', True, context)
        title = ''
        if database_length < 1:
            if target_screen:
                target_screen.description = THERE_IS_NO_SCHOOL_TASKS_FOR_NOW
                new_config.keyboard = [[Button(BUTTON_BACK, main_menu.MainMenu,
                                               source_type=SourceTypes.MOVE_SOURCE_TYPE)]]
                return await target_screen().render(update, context, config=new_config)
        else:
            context.user_data['RENDER_OPEN_DATE'] = True
            new_title = ''
            tasks_to_delete = []
            for i in range(database_length):
                title, current_title, check_day, check_month, check_year = await backend.get_multipy_async(i, title,
                                                                                                           context)
                if check_year == datetime.now().year:
                    if check_month == datetime.now().month:
                        if check_day <= datetime.now().day:
                            title = ''
                            del_index = await backend.get_item_index_from_community_tasks_order_by(context)
                            del_index = get_clean_var(del_index, 'to_string', i, True)
                            if del_index not in tasks_to_delete:
                                tasks_to_delete.append(del_index)
                    if check_month < datetime.now().month:
                        title = ''
                        del_index = await backend.get_item_index_from_community_tasks_order_by(context)
                        del_index = get_clean_var(del_index, 'to_string', i, True)
                        if del_index not in tasks_to_delete:
                            tasks_to_delete.append(del_index)
                if check_year < datetime.now().year:
                    title = ''
                    del_index = await backend.get_item_index_from_community_tasks_order_by(context)
                    del_index = get_clean_var(del_index, 'to_string', i, True)
                    if del_index not in tasks_to_delete:
                        tasks_to_delete.append(del_index)
                else:
                    new_title = title
                    context.user_data['RENDER_OPEN_DATE'] = False
                    media_index = await backend.get_item_index_from_community_tasks_order_by(context)
                    media_index = get_clean_var(media_index, 'to_string', i, True)
                    if exists(str(settings.MEDIA_ROOT) + '/' + media_index) and media_index not in tasks_to_delete:
                        media_button_title = ''
                        media_item_name = await backend.get_item_name_from_community_tasks_by_index(context, media_index)
                        media_item_name = get_clean_var(media_item_name, 'to_string', 0, True)
                        media_button_title += '🖼' + media_item_name
                        groups_check = await backend.get_group_from_community_tasks_by_name(context, media_item_name)
                        groups_check = get_clean_var(groups_check, 'to_string', 0, True)
                        if int(groups_check) > 1:
                            media_group_number = await backend.get_group_number_from_community_tasks_by_index(context, media_index)
                            media_group_number = get_clean_var(media_group_number, 'to_string', False,
                                                               True)
                            media_button_title += '(' + media_group_number + 'я группа)'
                        media_button_title += ': '
                        media_task_description = await backend.get_task_description_from_community_tasks_by_index(context, media_index)
                        # media_task_description = await backend._execute_query('SELECT task_description FROM ' + context.user_data[
                        #     'CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
                        #                        (media_index,))
                        # backend.cursor.execute('SELECT task_description FROM ' + context.user_data[
                        #     'CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
                        #                        (media_index,))
                        # media_task_description = backend.cursor.fetchone()
                        media_task_description = get_clean_var(media_task_description, 'to_string',
                                                               0, True)
                        media_button_title += media_task_description
                        new_config.keyboard.append([Button(media_button_title, self._goto_task_media,
                                                           source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                                                           payload=dumps({'MEDIA_INDEX_GOTO': media_index,
                                                                          'MEDIA_TITLE': current_title}))])
                if not new_title:
                    if target_screen:
                        target_screen.description = THERE_IS_NO_SCHOOL_TASKS_FOR_NOW
                elif target_screen:
                    target_screen.description = new_title
            for task_id in tasks_to_delete:
                await backend.logger_alert([], 'delete', task_id, False, context)
                await backend.delete_task_from_community_tasks_by_index(context, task_id)
                # await backend._execute_query('DELETE FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
                #     (task_id,))
                # backend.cursor.execute(
                #     'DELETE FROM ' + context.user_data['CURRENT_CLASS_NAME'] + '_Tasks WHERE item_index = %s',
                #     (task_id,))
                # backend.connection.commit()
                if exists(str(settings.MEDIA_ROOT) + '/' + task_id):
                    rmtree(str(settings.MEDIA_ROOT) + '/' + task_id)
            if target_screen:
                target_screen.description = new_title
            if database_length < 1:
                if target_screen:
                    target_screen.description = THERE_IS_NO_SCHOOL_TASKS_FOR_NOW
            if target_screen:
                new_config.keyboard.append([Button(BUTTON_BACK, main_menu.MainMenu,
                                                   source_type=SourceTypes.MOVE_SOURCE_TYPE)])
                try:
                    return await target_screen().render(update, context, config=new_config)
                except ScreenDescriptionIsEmpty:
                    bad_config = RenderConfig()
                    bad_config.description = THERE_IS_NO_SCHOOL_TASKS_FOR_NOW
                    bad_config.keyboard = [[Button(BUTTON_BACK, main_menu.MainMenu,
                                                   source_type=SourceTypes.MOVE_SOURCE_TYPE)]]
                    return await target_screen().render(update, context, config=bad_config)
                except BadRequest:
                    for x in range(0, len(target_screen.description), settings.MAX_CAPTION_LENGTH):
                        current_description = target_screen.description[x:x + settings.MAX_CAPTION_LENGTH]
                        save_markers = save_html_markers(current_description)
                        soup = BeautifulSoup(save_markers, 'html.parser')
                        soup.prettify()
                        current_description = str(soup)
                        current_description = load_html_markers(current_description)
                        current_description = '<strong>' + current_description + '</strong>'
                        if x + settings.MAX_CAPTION_LENGTH >= len(target_screen.description):
                            new_config.description = current_description
                            await target_screen().send(context, config=new_config)
                        else:
                            await update.effective_chat.send_message(current_description, parse_mode='HTML')

    @register_button_handler
    async def _goto_task_media(self, update, context):
        from school_tasker.screens import static_task_media
        await get_payload_safe(self, update, context, 'task_media_index', 'MEDIA_INDEX_GOTO')
        await get_payload_safe(self, update, context, 'task_media_index', 'MEDIA_TITLE')
        try:
            show_images = listdir('media/' + context.user_data['MEDIA_INDEX_GOTO'] + '/')
            if len(show_images) > 1:
                from school_tasker.screens import carousel_task_media
                new_task_media = carousel_task_media.CarouselTaskMedia()
            else:
                new_task_media = static_task_media.StaticTaskMedia()
            new_task_media.images = []
            for image in show_images:
                path = context.user_data['MEDIA_INDEX_GOTO'] + '/' + image
                item = [settings.MEDIA_ROOT / path, context.user_data['MEDIA_TITLE']]
                new_task_media.images.append(item)
            new_config = RenderConfig()
            if len(show_images) == 1:
                new_task_media.current_images = new_task_media.images[0]
                new_task_media.cover = new_task_media.current_images[0]
                new_task_media.description = context.user_data['MEDIA_TITLE']
                new_config.keyboard = [
                    [
                        Button(BUTTON_BACK, self._static_check_tasks,
                               source_type=SourceTypes.HANDLER_SOURCE_TYPE),
                    ],
                ]
                try:
                    return await new_task_media.render(update, context, config=new_config)
                except BadRequest:
                    for x in range(0, len(new_task_media.description), settings.MAX_CAPTION_LENGTH):
                        current_description = new_task_media.description[x:x + settings.MAX_CAPTION_LENGTH]
                        save_markers = save_html_markers(current_description)
                        soup = BeautifulSoup(save_markers, 'html.parser')
                        soup.prettify()
                        current_description = str(soup)
                        current_description = load_html_markers(current_description)
                        current_description = '<strong>' + current_description + '</strong>'
                        if x + settings.MAX_CAPTION_LENGTH >= len(new_task_media.description):
                            new_config.description = current_description
                            return await new_task_media.send(context, config=new_config)
                        else:
                            await update.effective_chat.send_message(current_description, parse_mode='HTML')
            else:
                try:
                    return await new_task_media.move(update, context)
                except BadRequest:
                    for x in range(0, len(new_task_media.description), settings.MAX_CAPTION_LENGTH):
                        current_description = new_task_media.description[x:x + settings.MAX_CAPTION_LENGTH]
                        save_markers = save_html_markers(current_description)
                        soup = BeautifulSoup(save_markers, 'html.parser')
                        soup.prettify()
                        current_description = str(soup)
                        current_description = load_html_markers(current_description)
                        current_description = '<strong>' + current_description + '</strong>'
                        if x + settings.MAX_CAPTION_LENGTH >= len(new_task_media.description):
                            new_config.description = current_description
                            await new_task_media.send(context, config=new_config)
                        else:
                            await update.effective_chat.send_message(current_description, parse_mode='HTML')
        except FileNotFoundError:
            await SchoolTasks().check_tasks(update, context, SchoolTasks)

    @register_button_handler
    async def _static_check_tasks(self, update, context):
        new_st_screen = SchoolTasks
        return await self.check_tasks(update, context, new_st_screen)
