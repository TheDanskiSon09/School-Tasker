import asyncio
from gino import Gino
from sqlalchemy import UniqueConstraint
from hammett.conf import settings

db = Gino()


# ---------- ФИКСИРОВАННЫЕ ТАБЛИЦЫ ----------

class Community(db.Model):
    __tablename__ = "COMMUNITY"

    name = db.Column(db.String(), primary_key=True)
    password = db.Column(db.String(), unique=True)


class User(db.Model):
    __tablename__ = "USERS"

    id = db.Column(db.BigInteger(), primary_key=True)  # Telegram user_id
    send_notification = db.Column(db.Integer())
    name = db.Column(db.String())


class UserCommunity(db.Model):
    __tablename__ = "USER_COMMUNITIES"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger(), db.ForeignKey("users.id"))
    class_name = db.Column(db.String())
    user_role_in_class = db.Column(db.String())

    __table_args__ = (
        UniqueConstraint("user_id", "class_name", name="uix_user_class"),
    )


# ---------- ДИНАМИЧЕСКИЕ МОДЕЛИ ----------

def get_items_model(class_name: str):
    table_name = f"{class_name.lower()}_Items"

    class DynamicItems(db.Model):
        __tablename__ = table_name

        id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
        main_name = db.Column(db.String())
        rod_name = db.Column(db.String())
        emoji = db.Column(db.String())
        groups = db.Column(db.Integer())
        item_index = db.Column(db.String())

    return DynamicItems


def get_tasks_model(class_name: str):
    table_name = f"{class_name.lower()}_Tasks"

    class DynamicTasks(db.Model):
        __tablename__ = table_name

        id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
        item_name = db.Column(db.String())
        item_index = db.Column(db.String())
        group_number = db.Column(db.Integer())
        task_description = db.Column(db.String())
        task_day = db.Column(db.Integer())
        task_month = db.Column(db.Integer())
        task_year = db.Column(db.Integer())
        hypertime = db.Column(db.BigInteger())

    return DynamicTasks


# ---------- ИНИЦИАЛИЗАЦИЯ БД ----------

async def init_db():
    await db.set_bind(
        "postgresql://" + str(settings.DATABASE_USER) + ":" + str(settings.DATABASE_PASSWORD) + "@" +
        str(settings.DATABASE_HOST) + ":" + str(settings.DATABASE_PORT)+"/" + str(settings.DATABASE_NAME)
    )
    await db.gino.create_all()


if __name__ == "__main__":
    asyncio.run(init_db())
