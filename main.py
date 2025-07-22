from hammett.core import Application
from hammett.core.constants import DEFAULT_STATE
from hammett.utils.autodiscovery import _autodiscover_screens_in_module
import screens
# from screens import MainMenu
from screens import *


def main():
    """Runs the bot. """

    name = 'School Tasker'
    app = Application(
        name,
        entry_point=MainMenu,
        states={
            DEFAULT_STATE: [MainMenu, SchoolTasks, SocialMedia, Options, ManageSchoolTasksMain,
                            ManageSchoolTasksAdd, ManageSchoolTasksAddDetails,ManageSchoolTasksRemove,
                            ManageSchoolTasksRemoveConfirm, NotificationScreen,
                            WhatsNew, ManageSchoolTasksChangeMain, ManageSchoolTasksChangeBase,
                            ManageSchoolTasksChangeItem,
                            ManageSchoolTasksChangeTask, ManageSchoolTasksChangeDay, ManageSchoolTasksChangeMonth,
                            ManageSchoolTasksChangeGroupNumber, ManageSchoolTasksAddGroupNumber,
                            AlertAddingOldTask, TaskMedia, CatchMedia, CommunitiesMain, SelectCommunityToWatch,
                            CreateCommunityName, CreateCommunityPassword, JoinCommunity,
                            ChangeCurrentCommunity, SelectCommunityToTasks, ManageCommunityMain, SelectCommunityToManage,
                            ManageCommunityChangeName, ManageCommunityChangePassword, ManageCommunityChangeUser,
                            ManageCommunityItems, ManageCommunityItemsAddEmoji, ManageCommunityItemsAddName,
                            ManageCommunityItemsAddRodName, ManageCommunityItemsAddGroup,ManageSchoolItem,
                            ManageSchoolItemChangeName, ManageSchoolItemChangeRodName, ManageSchoolItemChangeGroups,
                            ManageSchoolItemChangeEmoji, ConfirmDeletionSchoolItem]
        },
        # states={
        #     DEFAULT_STATE: (
        #         _autodiscover_screens_in_module(screens, []))
        # }
    )
    app.run()


if __name__ == '__main__':
    main()
