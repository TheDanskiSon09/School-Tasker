from hammett.core import Screen
from hammett.conf import settings


class BaseScreen(Screen):
    cache_covers = True
    hide_keyboard = True
    cover = settings.MEDIA_ROOT / 'logo.webp'  # используй как в carousel demo
