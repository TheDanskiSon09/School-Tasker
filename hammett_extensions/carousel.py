from telegram.error import BadRequest
from constants import BUTTON_BACK, BUTTON_BACK_TO_MENU
from hammett.core.constants import RenderConfig, DEFAULT_STATE, SourcesTypes
from hammett.core.handlers import register_button_handler
from hammett.widgets import CarouselWidget
from typing import TYPE_CHECKING
from hammett.core import Button
from telegram import Update

if TYPE_CHECKING:
    from telegram.ext._utils.types import BT, UD, CD, BD
    from typing_extensions import Self
    from hammett.types import Keyboard, State
    from telegram.ext import CallbackContext

_START_POSITION = 0


class STCarouselWidget(CarouselWidget):
    disable_caption: str = '🚫'
    back_caption: str = '⬅'
    next_caption: str = '➡'
    callback_button_type = None
    callback_button_screen = None
    back_description = ''

    def __init__(self: 'Self') -> None:
        """Initialize a carousel widget object."""
        super().__init__()
        if self.callback_button_type == 'main_menu':
            self._callback_button = Button(
                BUTTON_BACK_TO_MENU,
                self._go_to_main_menu,
                source_type=SourcesTypes.HANDLER_SOURCE_TYPE
            )
        elif self.callback_button_type == 'school_tasks':
            self._callback_button = Button(
                BUTTON_BACK,
                self._go_to_school_tasks,
                source_type=SourcesTypes.HANDLER_SOURCE_TYPE
            )

    async def _init(
            self: 'Self',
            update: 'Update | None',
            context: 'CallbackContext[BT, UD, CD, BD]',
            config: 'RenderConfig | None' = None,
            images: list[list[str]] | None = None,
    ) -> 'State':
        """Initialize the widget."""
        config = config or RenderConfig()
        current_images = images or await self.get_images(update, context)

        cover, description = current_images[_START_POSITION]
        config.cover = cover
        if not config.description:
            config.description = description or self.description
        config.keyboard = await self._build_keyboard(
            update,
            context,
            current_images,
            _START_POSITION,
        )
        await self.render(update, context, config=config, extra_data={'images': current_images})
        return DEFAULT_STATE

    async def _build_keyboard(
            self: 'Self',
            update: 'Update | None',
            context: 'CallbackContext[BT, UD, CD, BD]',
            images: list[list[str]],
            current_image: int,
    ) -> 'Keyboard':
        """Determine which button to disable and return the updated keyboard."""
        try:
            images[current_image + 1]
        except IndexError:
            next_button = self._disabled_button
        else:
            next_button = self._next_button

        if current_image - 1 < 0:
            back_button = self._disabled_button
        else:
            try:
                images[current_image - 1]
            except IndexError:
                back_button = self._disabled_button
            else:
                back_button = self._back_button
        keyboard = []
        if len(self.images) > 1:
            keyboard.append(
                [back_button, next_button])
        keyboard.append([*await self.add_extra_keyboard(update, context)])
        return keyboard

    async def add_extra_keyboard(self, _update, _context):
        return [self._callback_button]

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
        new_config.cover, new_config.description = self.images[_START_POSITION]
        try:
            new_config.description = "<strong>" + "\n".join(self.description.split("\n")[1:])
            await self.render(update, context, config=new_config)
            return await self.callback_button_screen().jump(update, context)
        except BadRequest:
            new_config.description = self.back_description
            await self.render(update, context, config=new_config)
            return await self.callback_button_screen().jump(update, context)

    @register_button_handler
    async def _next(
            self: 'Self',
            update: 'Update',
            context: 'CallbackContext[BT, UD, CD, BD]',
    ) -> None:
        """Switch to the next image."""
        if context.user_data:
            current_image = (
                    await self.get_state_value(update, context, 'position') or _START_POSITION
            )
        else:
            current_image = _START_POSITION
        save_description = self.description
        try:
            self.description = "<strong>" + "\n".join(self.description.split("\n")[1:])
            self.back_description = self.description
            return await self._switch_handle_method(
                update,
                context,
                current_image,
                current_image + 1,
            )
        except BadRequest:
            self.description = save_description
            self.back_description = self.description
            return await self._switch_handle_method(
                update,
                context,
                current_image,
                current_image + 1,
            )

    @register_button_handler
    async def _back(
            self: 'Self',
            update: 'Update',
            context: 'CallbackContext[BT, UD, CD, BD]',
    ) -> None:
        """Switch to the previous image."""
        current_image = await self.get_state_value(update, context, 'position') or _START_POSITION
        self.cover, self.description = self.images[_START_POSITION]
        self.description = self.back_description
        return await self._switch_handle_method(
            update,
            context,
            current_image,
            current_image - 1,
        )
