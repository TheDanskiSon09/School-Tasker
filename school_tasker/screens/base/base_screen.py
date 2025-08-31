from hammett.conf import settings
from hammett.core import Screen


class BaseScreen(Screen):
    cache_covers = True
    hide_keyboard = True
    cover = settings.MEDIA_ROOT / 'logo.webp'
