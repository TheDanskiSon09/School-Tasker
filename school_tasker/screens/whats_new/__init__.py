from datetime import datetime

from hammett.core import Button
from hammett.core.constants import SourceTypes

from captions import BUTTON_BACK_TO_MENU, TODAY_IS_NO_CELEBRATIONS
from constants import (
    MONTH_APRIL,
    MONTH_AUG,
    MONTH_DEC,
    MONTH_FEB,
    MONTH_JAN,
    MONTH_JULY,
    MONTH_JUNE,
    MONTH_MARCH,
    MONTH_MAY,
    MONTH_NOV,
    MONTH_OCT,
    MONTH_SEP,
)
from school_tasker.screens.base import base_screen


class WhatsNew(base_screen.BaseScreen):

    async def add_default_keyboard(self, update, context):
        from school_tasker.screens import main_menu
        return [
            [
                Button(BUTTON_BACK_TO_MENU, main_menu.MainMenu, source_type=SourceTypes.MOVE_SOURCE_TYPE),
            ],
        ]

    async def get_description(self, update, context):
        current_day = datetime.now().day
        current_month = datetime.now().month
        try:
            title = ''
            title += '<strong>'
            month_dict = {1: MONTH_JAN,
                          2: MONTH_FEB,
                          3: MONTH_MARCH,
                          4: MONTH_APRIL,
                          5: MONTH_MAY,
                          6: MONTH_JUNE,
                          7: MONTH_JULY,
                          8: MONTH_AUG,
                          9: MONTH_SEP,
                          10: MONTH_OCT,
                          11: MONTH_NOV,
                          12: MONTH_DEC}
            month = month_dict[current_month]
            title += str(month[current_day])
            title += '</strong>'
            return title
        except KeyError:
            return TODAY_IS_NO_CELEBRATIONS
