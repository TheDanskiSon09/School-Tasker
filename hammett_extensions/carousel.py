from hammett.core.constants import RenderConfig, DEFAULT_STATE, SourcesTypes
from hammett.core.exceptions import ImproperlyConfigured
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
    disable_caption: str = '⛔'
    back_caption: str = '⬅'
    next_caption: str = '➡'
    callback_button_type = None
    callback_button_screen = None

    def __init__(self: 'Self') -> None:
        """Initialize a carousel widget object."""
        super().__init__()

        if not isinstance(self.images, list):
            msg = f'The images attribute of {self.__class__.__name__} must be a list of lists'
            raise ImproperlyConfigured(msg)

        if not (self.back_caption and self.next_caption and self.disable_caption):
            msg = (
                f'{self.__class__.__name__} must specify both back_caption, next_caption '
                f'and disable_caption'
            )
            raise ImproperlyConfigured(msg)

        self._back_button = Button(
            self.back_caption,
            self._back,
            source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
        )
        self._next_button = Button(
            self.next_caption,
            self._next,
            source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
        )
        self._disabled_button = Button(
            self.disable_caption,
            self._do_nothing,
            source_type=SourcesTypes.HANDLER_SOURCE_TYPE,
        )
        if self.callback_button_type == 'main_menu':
            self._callback_button = Button(
                '⬅На главный экран',
                self._go_to_main_menu,
                source_type=SourcesTypes.HANDLER_SOURCE_TYPE
            )
        elif self.callback_button_type == 'school_tasks':
            self._callback_button = Button(
                '⬅Назад',
                self._go_to_school_tasks,
                source_type=SourcesTypes.HANDLER_SOURCE_TYPE
            )
        if len(self.images) > 1:
            self._infinity_keyboard = [[self._back_button, self._next_button, self._callback_button]]
        else:
            self._infinity_keyboard = [[self._callback_button]]

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
        if self.infinity:
            config.keyboard = (self._infinity_keyboard +
                               await self.add_extra_keyboard(update, context))
        else:
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
        callback_button = self._callback_button
        if len(self.images) > 1:
            return [
                [back_button, next_button], [callback_button]
            ]
        else:
            return [[callback_button]]

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
        new_config.description = "<strong>" + "\n".join(self.description.split("\n")[1:])
        await self.render(update, context, config=new_config)
        return await self.callback_button_screen().jump(update, context)
