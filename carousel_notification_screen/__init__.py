from school_tasker.screens.base import base_carousel
from school_tasker.screens.base import base_screen


class CarouselNotificationScreen(base_screen.BaseScreen, base_carousel.BaseCarouselWidget):
    from school_tasker.screens import main_menu
    callback_button_type = "main_menu"
    callback_button_screen = main_menu
    hide_keyboard = False
