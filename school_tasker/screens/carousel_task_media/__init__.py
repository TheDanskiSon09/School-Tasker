from hammett.conf import settings
from school_tasker.screens.base import base_carousel
from school_tasker.screens.base import base_screen


class CarouselTaskMedia(base_screen.BaseScreen, base_carousel.BaseCarouselWidget):
    from school_tasker.screens import school_tasks
    images = [
        [settings.MEDIA_ROOT / "logo.webp", "_"]
    ]
    callback_button_type = 'school_tasks'
    callback_button_screen = school_tasks.SchoolTasks
    button_title = "⬅ На главный экран"
