from hammett.core import Screen
from hammett.conf import settings


class BaseScreen(Screen):
    cache_covers = True
    hide_keyboard = True
    cover = str(settings.MEDIA_ROOT) + '/' + 'logo.webp'
