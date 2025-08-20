from hammett.core import Bot
from hammett.core.constants import DEFAULT_STATE
from hammett.core.mixins import StartMixin
# from hammett.core.persistence import RedisPersistence
from hammett.utils.autodiscovery import autodiscover_screens

from school_tasker.screens.base.base_carousel import BaseCarouselWidget
from school_tasker.screens.base.base_screen import BaseScreen
from school_tasker.screens import main_menu


def main():
    """Runs the bot. """

    name = 'School Tasker'
    app = Bot(
        name,
        entry_point=main_menu.MainMenu,
        states={DEFAULT_STATE: autodiscover_screens('school_tasker.screens', [BaseScreen, StartMixin, BaseCarouselWidget])},
        # persistence=RedisPersistence()
    )
    app.run()


if __name__ == '__main__':
    main()
