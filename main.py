from hammett.core import Bot
from hammett.core.constants import DEFAULT_STATE
from hammett.core.mixins import StartMixin
from hammett.utils.autodiscovery import autodiscover_screens

from school_tasker.screens.community_item_emoji_addition import CommunityItemEmojiAddition
from school_tasker.screens.community_item_group_addition import CommunityItemGroupAddition
from school_tasker.screens.community_item_name_addition import CommunityItemNameAddition
from school_tasker.screens.community_item_rod_name_addition import CommunityItemRodNameAddition
from school_tasker.screens.community_name_change import CommunityNameChange
from school_tasker.screens.community_name_creation import CommunityNameCreation
from school_tasker.screens.community_password_change import CommunityPasswordChange
from school_tasker.screens.community_password_creation import CommunityPasswordCreation
from school_tasker.screens.school_item_emoji_change import SchoolItemEmojiChange
from school_tasker.screens.school_item_groups_change import SchoolItemGroupsChange
from school_tasker.screens.school_item_name_change import SchoolItemNameChange
from school_tasker.screens.school_item_rod_name_change import SchoolItemRodNameChange
from school_tasker.screens.school_task_addition_details import SchoolTaskAdditionDetails
from states import CHANGING_TASK_DESCRIPTION, ADDING_TASK, CHANGING_CLASS_NAME, CHANGING_CLASS_PASSWORD, \
    CHANGING_ITEM_NAME, CHANGING_ITEM_ROD_NAME, CHANGING_ITEM_GROUPS, CHANGING_ITEM_EMOJI, CREATING_ITEM_EMOJI, \
    CREATING_ITEM_NAME, CREATING_ITEM_ROD_NAME, CREATING_ITEM_GROUP, CREATING_CLASS, ADDING_PASSWORD_TO_CLASS
from school_tasker.screens import main_menu
from school_tasker.screens.base.base_carousel import BaseCarouselWidget
from school_tasker.screens.base.base_screen import BaseScreen
from school_tasker.screens.school_item_change_base_class import SchoolItemChangeBaseClass
from school_tasker.screens.school_task_change_task import SchoolTaskChangeTask


def main():
    """Runs the bot."""
    name = 'School Tasker'
    app = Bot(
        name,
        entry_point=main_menu.MainMenu,
        states={
            DEFAULT_STATE: (autodiscover_screens(
                'school_tasker.screens',
                (BaseScreen, StartMixin, BaseCarouselWidget, SchoolItemChangeBaseClass, SchoolTaskAdditionDetails,
                 CommunityNameChange, SchoolTaskChangeTask, CommunityPasswordChange, SchoolItemNameChange,
                 SchoolItemRodNameChange,
                 SchoolItemGroupsChange, SchoolItemEmojiChange, CommunityItemEmojiAddition,
                 CommunityItemNameAddition, CommunityItemGroupAddition, CommunityItemRodNameAddition,
                 CommunityNameCreation,CommunityPasswordCreation))),
            ADDING_TASK: {SchoolTaskAdditionDetails},
            CHANGING_CLASS_NAME: {CommunityNameChange},
            CHANGING_TASK_DESCRIPTION: {SchoolTaskChangeTask},
            CHANGING_CLASS_PASSWORD: {CommunityPasswordChange},
            CHANGING_ITEM_NAME: {SchoolItemNameChange},
            CHANGING_ITEM_ROD_NAME: {SchoolItemRodNameChange},
            CHANGING_ITEM_GROUPS: {SchoolItemGroupsChange},
            CHANGING_ITEM_EMOJI: {SchoolItemEmojiChange},
            CREATING_ITEM_EMOJI: {CommunityItemEmojiAddition},
            CREATING_ITEM_NAME: {CommunityItemNameAddition},
            CREATING_ITEM_ROD_NAME: {CommunityItemRodNameAddition},
            CREATING_ITEM_GROUP: {CommunityItemGroupAddition},
            CREATING_CLASS: {CommunityNameCreation},
            ADDING_PASSWORD_TO_CLASS: {CommunityPasswordCreation}
        }
    )
    app.run()


if __name__ == '__main__':
    main()
