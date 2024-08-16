from hammett.core import Application
from hammett.core.constants import DEFAULT_STATE
from screens import *


def main():
    """Runs the bot. """

    name = 'School Tasker'
    app = Application(
        name,
        entry_point=MainMenu,
        states={
            DEFAULT_STATE: [MainMenu, SchoolTasks, Options, ManageSchoolTasksMain,
                            ManageSchoolTasksAdd, ManageSchoolTasksAddDetails,
                            TaskWasAdded, ManageSchoolTasksRemove,
                            ManageSchoolTasksRemoveConfirm, ReplaceOrAddTask, TaskWasChanged, NotificationScreen,
                            WhatsNew, ManageSchoolTasksChangeMain, ManageSchoolTasksChangeBase,
                            ManageSchoolTasksChangeItem,
                            ManageSchoolTasksChangeTask, ManageSchoolTasksChangeDay, ManageSchoolTasksChangeMonth,
                            ManageSchoolTasksChangeGroupNumber, ManageSchoolTasksAddGroupNumber, ManageAdminUsersMain,
                            ManageAdminUsersAdd, ManageAdminUsersAddConfirm, ManageAdminUsersRemove,
                            ManageAdminUsersRemoveConfirm, UserWasMarkedAsAnonim, UserWasMarkedAsAdmin,
                            ],
        },
    )
    app.run()


if __name__ == '__main__':
    main()
