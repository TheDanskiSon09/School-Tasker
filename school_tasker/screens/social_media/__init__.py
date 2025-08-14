from hammett.core import Button
from hammett.core.constants import SourceTypes

from constants import BUTTON_BACK_TO_MENU, MORE_ABOUT_SCHOOL_TASKER_YOU_CAN_FIND_HERE, OUR_NEWS_CHANNEL_TG, \
    OUR_NEWS_CHANNEL_VK, GITHUB_REPOSITORY, CONTACT_WITH_DEVELOPER
from school_tasker.screens.base import base_screen


class SocialMedia(base_screen.BaseScreen):
    description = MORE_ABOUT_SCHOOL_TASKER_YOU_CAN_FIND_HERE

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens.main_menu import MainMenu
        return [
            [
                Button(OUR_NEWS_CHANNEL_TG, 'https://t.me/SchoolTaskerNews',
                       source_type=SourceTypes.URL_SOURCE_TYPE)
            ],
            [
                Button(OUR_NEWS_CHANNEL_VK, 'https://vk.ru/schooltasker',
                       source_type=SourceTypes.WEB_APP_SOURCE_TYPE)
            ],

            [
                Button(GITHUB_REPOSITORY, 'https://github.com/TheDanskiSon09/School-Tasker',
                       source_type=SourceTypes.WEB_APP_SOURCE_TYPE)
            ],
            [
                Button(CONTACT_WITH_DEVELOPER, 'https://t.me/TheDanskiSon09',
                       source_type=SourceTypes.URL_SOURCE_TYPE)
            ],
            [
                Button(BUTTON_BACK_TO_MENU, MainMenu,
                       source_type=SourceTypes.MOVE_SOURCE_TYPE)
            ]
        ]