from hammett.core.constants import RenderConfig, DEFAULT_STATE
from hammett.widgets import CarouselWidget
from typing import TYPE_CHECKING
from hammett.core import Button

if TYPE_CHECKING:
    from telegram.ext._utils.types import BT, UD, CD, BD
    from typing_extensions import Self
    from hammett.types import Keyboard, State
    from telegram.ext import CallbackContext

_START_POSITION = 0


class STCarouselWidget(CarouselWidget):
    disable_caption: str = '⛔'
    button_target = None
    button_source_type = None
    button_title = None

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
        if len(self.images) > 1:
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
        else:
            config.keyboard = [[Button(self.button_title, self.button_target,
                                       source_type=self.button_source_type)]]
        await self.render(update, context, config=config, extra_data={'images': current_images})
        return DEFAULT_STATE

    async def _build_keyboard(
            self: 'Self',
            update: 'Update | None',
            context: 'CallbackContext[BT, UD, CD, BD]',
            images: list[list[str]],
            current_image: int
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
        return [
            [back_button, next_button],
            [Button(self.button_title, self.button_target, source_type=self.button_source_type)]
        ]
