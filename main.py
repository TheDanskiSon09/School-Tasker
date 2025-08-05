from hammett.core import Bot
from hammett.core.constants import DEFAULT_STATE
from hammett.utils.autodiscovery import autodiscover_screens
# from school_tasker.screens.screens import MainMenu, BaseScreen, StartMixin
# from hammett_extensions.carousel import BaseCarouselWidget
from screens import *


def main():
    """Runs the bot. """

    name = 'School Tasker'
    app = Bot(
        name,
        entry_point=MainMenu,
        states={
            DEFAULT_STATE: [MainMenu, SchoolTasks, SocialMedia, Options, SchoolTaskManagementMain,
                            SchoolTaskAddition, SchoolTaskAdditionDetails, SchoolTaskRemoval,
                            SchoolTaskRemovalConfirmation, StaticNotificationScreen, CarouselNotificationScreen,
                            WhatsNew, SchoolTaskChangeMain, SchoolTaskChangeBase,
                            SchoolTaskChangeItem,
                            SchoolTaskChangeTask, SchoolTaskChangeDay, SchoolTaskMonthChange,
                            SchoolTaskChangeGroupNumber, SchoolTaskAdditionGroupNumber,
                            OldTaskAdditionAlert, StaticTaskMedia, CarouselTaskMedia ,MediaCapture, SchoolItemManagement,
                            SchoolItemGroupsChange, SchoolItemNameChange, SchoolItemEmojiChange, SchoolItemRodNameChange,
                            SchoolItemDeletionConfirmation, CommunityItemManagement, CommunityItemNameAddition, SchoolTaskAdditionDetailsDay,
                            SchoolTaskAdditionDetailsMonth]
        }
    )
    app.run()


if __name__ == '__main__':
    main()
