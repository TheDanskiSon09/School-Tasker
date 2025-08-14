from contextlib import suppress

from hammett.core import Button
from hammett.core.constants import SourceTypes, RenderConfig
from hammett.core.handlers import register_button_handler

import backend
from constants import BUTTON_BACK, SEND_PHOTOS_THAT_TASK_NEEDS, SUCCESSFULLY_GOT_WHAT_YOU_WANT_TO_DO, CREATE_TASK, \
    DELETE_SENDED_TASKS, ARE_YOU_SURE_YOU_WANT_TO_DELETE_PHOTOS, DELETE, PHOTOS_WAS_DELETED, ADD_TASK
from hammett_extensions.handlers import register_input_handler
from school_tasker.screens.base import base_screen
from utils import check_task_validity, generate_id


class MediaCapture(base_screen.BaseScreen):
    description = SEND_PHOTOS_THAT_TASK_NEEDS

    @register_input_handler
    async def catch_media(self, update, context):
        from school_tasker.screens import main_menu
        if update.message.text and update.message.text == '/start':
            return await main_menu.MainMenu().jump(update, context)
        with suppress(KeyError):
            if context.user_data["IS_IN_MEDIA_SCREEN"]:
                message = update.message
                if message.photo:
                    file = message.photo[-1]
                    file_id = file.file_id
                    file = await context.bot.get_file(file_id)
                    try:
                        context.user_data["MEDIA_ADD"].append(file)
                    except KeyError:
                        context.user_data["MEDIA_ADD"] = []
                        context.user_data["MEDIA_ADD"].append(file)
                    new_config = RenderConfig()
                    new_config.description = SUCCESSFULLY_GOT_WHAT_YOU_WANT_TO_DO
                    new_config.keyboard = [
                        [
                            Button(CREATE_TASK, self.add_school_task,
                                   source_type=SourceTypes.HANDLER_SOURCE_TYPE)
                        ],
                        [
                            Button(DELETE_SENDED_TASKS, self.delete_media,
                                   source_type=SourceTypes.HANDLER_SOURCE_TYPE)
                        ],
                        [
                            Button(BUTTON_BACK, self.go_to_task_screen,
                                   source_type=SourceTypes.HANDLER_SOURCE_TYPE)
                        ]
                    ]
                    return await MediaCapture().send(context, config=new_config, extra_data=None)

    @register_button_handler
    async def go_to_task_screen(self, update, context):
        from school_tasker.screens.school_task_management_main import school_task_addition
        context.user_data["MEDIA_ADD"] = []
        return await school_task_addition.SchoolTaskAddition().move(update, context)

    @register_button_handler
    async def delete_media(self, _update, context):
        new_config = RenderConfig()
        new_config.description = ARE_YOU_SURE_YOU_WANT_TO_DELETE_PHOTOS
        new_config.keyboard = [
            [
                Button(DELETE, self.confirm_delete,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button(BUTTON_BACK, self.go_back,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE)
            ]
        ]
        return await MediaCapture().send(context, config=new_config, extra_data=None)

    @register_button_handler
    async def go_back(self, _update, context):
        new_config = RenderConfig()
        new_config.description = self.description
        new_config.keyboard = [
            [
                Button(CREATE_TASK, self.add_school_task,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button(DELETE_SENDED_TASKS, self.delete_media,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button(BUTTON_BACK, self.go_to_task_screen,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE)
            ]
        ]
        return await MediaCapture().send(context, config=new_config, extra_data=None)

    @register_button_handler
    async def confirm_delete(self, _update, context):
        context.user_data["MEDIA_ADD"] = []
        new_config = RenderConfig()
        new_config.description = PHOTOS_WAS_DELETED
        new_config.keyboard = [
            [
                Button(CREATE_TASK, self.add_school_task,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button(BUTTON_BACK, self.go_to_task_screen,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE)
            ]
        ]
        return await MediaCapture().send(context, config=new_config, extra_data=None)

    @register_button_handler
    async def add_school_task(self, update, context):
        check = check_task_validity(int(context.user_data["ADDING_TASK_TASK_DAY"]),
                                    context.user_data["ADDING_TASK_TASK_MONTH"],
                                    context.user_data["ADDING_TASK_TASK_YEAR"])
        context.user_data["ADD_TASK_ITEM_INDEX"] = str(generate_id())

        if check:
            try:
                try:
                    await backend.add_task_school(update, context, context.user_data["ADDING_TASK_NAME"],
                                                  context.user_data["ADDING_TASK_TASK_DESCRIPTION"],
                                                  context.user_data["ADDING_TASK_GROUP_NUMBER"],
                                                  int(context.user_data["ADDING_TASK_TASK_DAY"]),
                                                  int(context.user_data["ADDING_TASK_TASK_MONTH"]),
                                                  int(context.user_data["ADDING_TASK_TASK_YEAR"]))
                except KeyError:
                    await backend.add_task_school(update, context, context.user_data["ADDING_TASK_NAME"],
                                                  context.user_data["ADDING_TASK_TASK_DESCRIPTION"],
                                                  1,
                                                  int(context.user_data["ADDING_TASK_TASK_DAY"]),
                                                  int(context.user_data["ADDING_TASK_TASK_MONTH"]),
                                                  int(context.user_data["ADDING_TASK_TASK_YEAR"]))
            except KeyError:
                await backend.add_task_school(update, context, context.user_data["ADDING_TASK_NAME"],
                                              context.user_data["ADDING_TASK_TASK_DESCRIPTION"],
                                              1,
                                              int(context.user_data["ADDING_TASK_TASK_DAY"]),
                                              int(context.user_data["ADDING_TASK_TASK_MONTH"]),
                                              int(context.user_data["ADDING_TASK_TASK_YEAR"]))
        else:
            await go_to_alert([context.user_data["ADDING_TASK_NAME"],
                               context.user_data["ADDING_TASK_TASK_DESCRIPTION"],
                               context.user_data["ADDING_TASK_GROUP_NUMBER"],
                               context.user_data["ADDING_TASK_TASK_DAY"],
                               context.user_data["ADDING_TASK_TASK_MONTH"],
                               context.user_data["ADDING_TASK_TASK_YEAR"]],
                              "add", context.user_data['ADD_TASK_ITEM_INDEX'], update, context)

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens.school_task_management_main import school_task_addition
        return [
            [
                Button(ADD_TASK, self.add_school_task,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE)
            ],
            [
                Button(BUTTON_BACK, school_task_addition.SchoolTaskAddition,
                       source_type=SourceTypes.MOVE_SOURCE_TYPE)
            ]
        ]


async def go_to_alert(task_args: list, taskcontext: str, current_index, update, context):
    from school_tasker.screens import old_task_addition_alert
    old_task_addition_alert.OldTaskAdditionAlert().taskcontext = taskcontext
    old_task_addition_alert.OldTaskAdditionAlert.task_args = task_args
    old_task_addition_alert.OldTaskAdditionAlert().current_index = current_index
    return await old_task_addition_alert.OldTaskAdditionAlert().jump(update, context)
