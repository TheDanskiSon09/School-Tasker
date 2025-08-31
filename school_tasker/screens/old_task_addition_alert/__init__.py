from datetime import datetime

from hammett.core import Button
from hammett.core.constants import SourceTypes
from hammett.core.handlers import register_button_handler

import backend
from school_tasker.screens.base import base_screen
from utils import generate_id, get_hypertime


class OldTaskAdditionAlert(base_screen.BaseScreen):
    description = ('<strong>⚠Внимание!\nВы ввели дату и месяц задания, которые уже считаются устаревшими!'
                   ' Если Вы добавите задание с данными характеристиками, оно будет удалено при'
                   ' первом заходе в задачник!'
                   '\nВы точно хотите добавить данное задание?</strong>')
    task_args = list()
    taskcontext = ''
    current_index = 0

    async def get_description(self, update, context):
        if self.taskcontext == 'add':
            word00 = 'добавите '
            word01 = 'добавить '
        elif self.taskcontext == 'change':
            word00 = 'измените '
            word01 = 'изменить '
        else:
            word00 = ''
            word01 = ''
        part00 = '<strong>⚠Внимание!\nВы ввели дату и месяц задания, которые уже считаются устаревшими.'
        part01 = ' Если Вы ' + word00 + ('задание с данными характеристиками, оно будет удалено при первом заходе в'
                                         ' задачник!')
        part02 = '\nВы точно хотите ' + word01 + 'данное задание?</strong>'
        return part00 + part01 + part02

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import school_task_management_main
        keyboard = []
        if self.taskcontext == 'add':
            keyboard.append([
                Button('Добавить данное задание➕', self.add_old_task, source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ])
        elif self.taskcontext == 'change':
            keyboard.append([
                Button('Изменить данное задание✖', self.change_task, source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ])
        keyboard.append([
            Button('⬅️ Изменить дату/месяц задания', self.change_task_time,
                   source_type=SourceTypes.HANDLER_SOURCE_TYPE),
        ])
        keyboard.append([
            Button('⬅️ В меню редактора', school_task_management_main.SchoolTaskManagementMain, source_type=SourceTypes.MOVE_SOURCE_TYPE),
        ])
        return keyboard

    @register_button_handler
    async def change_task_time(self, update, context):
        from school_tasker.screens import school_task_addition_details
        context.user_data['CURRENT_TYPING_ACTION'] = 'CHANGE_TASK_TIME'
        return await school_task_addition_details.SchoolTaskAdditionDetails().move(update, context)

    @register_button_handler
    async def add_old_task(self, update, context):
        context.user_data['ADD_TASK_ITEM_INDEX'] = str(generate_id())
        await backend.add_task_school(update, context, self.task_args[0], self.task_args[1], self.task_args[2],
                              self.task_args[3], self.task_args[4], self.task_args[5])

    @register_button_handler
    async def change_task(self, update, context):
        from school_tasker.screens import (
            main_menu,
            school_task_change_main,
            school_task_management_main,
        )
        self.task_args[5] = datetime.now().year
        await backend._execute_query(
            'UPDATE SchoolTasker set task_day = %s, task_month = %s, task_year = %s WHERE item_index = %s',
            (self.task_args[3], self.task_args[4], self.task_args[5], self.current_index))
        hypertime = get_hypertime(self.task_args[4], self.task_args[3], self.task_args[5])
        await backend._execute_query('UPDATE SchoolTasker set hypertime = %s WHERE item_index = %s',
                                     (hypertime, self.current_index))
        await backend.send_update_notification(update, context, 'change', self.current_index, False, 'change')
        return await backend.show_notification_screen(update, context, 'send', '✅<strong>Задание успешно изменено!</strong>',
                                              [
                                                  [Button('⬅️ В меню редактора', school_task_management_main.SchoolTaskManagementMain,
                                                          source_type=SourceTypes.MOVE_SOURCE_TYPE)],
                                                  [Button('⬅ Изменить ещё задания', school_task_change_main.SchoolTaskChangeMain,
                                                          source_type=SourceTypes.MOVE_SOURCE_TYPE)],
                                                  [Button('⬅️ На главный экран', main_menu.MainMenu,
                                                          source_type=SourceTypes.MOVE_SOURCE_TYPE)]])
