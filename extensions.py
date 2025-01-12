from hammett.core.constants import RenderConfig, DEFAULT_STATE
from hammett.widgets import CarouselWidget
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telegram.ext._utils.types import BT, UD, CD, BD
    from typing_extensions import Self
    from hammett.types import State
    from telegram.ext import CallbackContext

_START_POSITION = 0


class STCarouselWidget(CarouselWidget):
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

        await self.render(update, context, config=config, extra_data={'images': current_images})
        return DEFAULT_STATE
