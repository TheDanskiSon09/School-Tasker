from hammett.core import Button
from hammett.core.constants import SourceTypes, DEFAULT_STATE
from hammett.core.handlers import register_button_handler, register_typing_handler
from hammett.core.mixins import RouteMixin

import backend
from captions import BUTTON_BACK, ENTER_NEW_TASK_TEXT
from states import CHANGING_TASK_DESCRIPTION
from school_tasker.screens.base import base_screen
from utils import get_payload_safe, get_clean_var


class SchoolTaskChangeTask(base_screen.BaseScreen, RouteMixin):
    routes = (
        ({DEFAULT_STATE}, CHANGING_TASK_DESCRIPTION),
    )

    description = ENTER_NEW_TASK_TEXT
    current_index = 0
    task_description = ''

    async def add_default_keyboard(self, update, context):
        await get_payload_safe(self, update, context, 'change_task_description', 'deletion_index')
        return [
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE),
            ],
        ]

    @register_button_handler
    async def go_back(self, update, context):
        from school_tasker.screens import school_task_change_base
        context.user_data['CURRENT_TYPING_ACTION'] = ''
        return await school_task_change_base.SchoolTaskChangeBase().move(update, context)

    @register_typing_handler
    async def handle_new_task_text(self, update, context):
        """"""
        try:
            if context.user_data['ADDING_TASK_TASK_DESCRIPTION']:
                context.user_data['ADDING_TASK_TASK_DESCRIPTION'] += update.message.text
        except KeyError:
            context.user_data['ADDING_TASK_TASK_DESCRIPTION'] = update.message.text
        context.user_data['CURRENT_TYPING_ACTION'] = ''
        await backend.update_task_description(context)
        item_name = await backend.get_item_name_from_tasks_by_item_index(context)
        item_name = get_clean_var(item_name, 'to_string', 0, True)
        context.user_data['ADDING_TASK_NAME'] = item_name
        del context.user_data['ADDING_TASK_TASK_DESCRIPTION']
        return await backend.send_update_notification(update, context, 'change',
                                                      context.user_data['ADDING_TASK_INDEX'],
                                                      True, 'change')