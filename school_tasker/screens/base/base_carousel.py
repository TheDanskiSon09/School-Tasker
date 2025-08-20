from telegram.error import BadRequest
from constants import BUTTON_BACK, BUTTON_BACK_TO_MENU
from hammett.core.constants import RenderConfig, SourceTypes
from hammett.core.handlers import register_button_handler
from hammett.widgets import CarouselWidget
from typing import TYPE_CHECKING
from hammett.core import Button
from telegram import Update

if TYPE_CHECKING:
    from telegram.ext._utils.types import BT, UD, CD, BD
    from typing_extensions import Self
    from telegram.ext import CallbackContext


class BaseCarouselWidget(CarouselWidget):
    disable_caption: str = '🚫'
    back_caption: str = '⬅'
    next_caption: str = '➡'
    callback_button_type = None
    callback_button_screen = None
    back_description = ''

    def __init__(self: 'Self') -> None:
        """Initialize a carousel widget object."""
        super().__init__()
        self._callback_button = None
        if self.callback_button_type == 'main_menu':
            self._callback_button = Button(
                BUTTON_BACK_TO_MENU,
                self._go_to_main_menu,
                source_type=SourceTypes.HANDLER_SOURCE_TYPE
            )
        elif self.callback_button_type == 'school_tasks':
            self._callback_button = Button(
                BUTTON_BACK,
                self._go_to_school_tasks,
                source_type=SourceTypes.HANDLER_SOURCE_TYPE
            )

    async def add_extra_keyboard(self, update, context):
        return [[self._callback_button]]

    @register_button_handler
    async def _go_to_school_tasks(
            self: 'Self',
            update: 'Update',
            context: 'CallbackContext[BT, UD, CD, BD]',
    ) -> None:
        await self.callback_button_screen().check_tasks(update, context, self.callback_button_screen)

    @register_button_handler
    async def _go_to_main_menu(
            self: 'Self',
            update: 'Update',
            context: 'CallbackContext[BT, UD, CD, BD]',
    ) -> None:
        new_config = RenderConfig()
        new_config.keyboard = []
        new_config.cover, new_config.description = self.images[0]
        try:
            new_config.description = "<strong>" + "\n".join(self.description.split("\n")[1:])
            await self.render(update, context, config=new_config)
            return await self.callback_button_screen().jump(update, context)
        except BadRequest:
            await self.render(update, context, config=new_config)
            return await self.callback_button_screen().jump(update, context)
