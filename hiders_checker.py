from hammett.conf import settings
from hammett.core.hiders import HidersChecker


class SchoolTaskerBotHiderChecker(HidersChecker):
    async def is_admin(self, update, _context) -> bool:
        user = update.effective_user
        return str(user.id) in settings.ADMIN_GROUP
