from aiogram import Router
from aiogram.types import Message, Chat
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from main import ADMIN_IDS

admin_router = Router()
help_router = Router()


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_IDS


@admin_router.message(Command("admin_help"))
async def admin_help(message: Message):
    """Команда помощи для администраторов"""
    if not is_admin(message.from_user.id):
        return

    help_text = """
🤖 <b>Админские команды:</b>

/get_channel_id - Получить ID канала
/get_chat_id - Получить ID текущего чата
/list_admins - Список администраторов бота
"""
    await message.answer(help_text, parse_mode="HTML")


@admin_router.message(Command("get_channel_id"))
async def get_channel_id(message: Message, command: CommandObject):
    """Получение ID канала по username"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для использования этой команды")
        return

    if not command.args:
        await message.answer(
            "❗ Укажите username канала: /get_channel_id @channel_name"
        )
        return

    channel_username = command.args.strip()

    if not channel_username.startswith("@"):
        channel_username = "@" + channel_username

    try:
        chat: Chat = await message.bot.get_chat(channel_username)
        response = f"""
📍 <b>Информация о канале:</b>
📝 Название: {chat.title}
🔗 Username: {chat.username}
🆔 ID: <code>{chat.id}</code>
📊 Тип: {chat.type}
"""
        await message.answer(response, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка при получении информации о канале: {str(e)}")


@admin_router.message(Command("get_chat_id"))
async def get_chat_id(message: Message):
    """Получение ID текущего чата"""
    if not is_admin(message.from_user.id):
        return

    chat_info = f"""
📍 <b>Информация о чате:</b>
🆔 ID чата: <code>{message.chat.id}</code>
📝 Название: {message.chat.title or "Личный чат"}
🔗 Username: {message.chat.username or "Нет"}
📊 Тип: {message.chat.type}
👤 Ваш ID: <code>{message.from_user.id}</code>
"""

    await message.answer(chat_info, parse_mode="HTML")


@admin_router.message(Command("list_admins"))
async def list_admins(message: Message):
    """Список администраторов"""
    if not is_admin(message.from_user.id):
        return

    admins_list = "\n".join([f"👤 <code>{admin_id}</code>" for admin_id in ADMIN_IDS])
    response = f"""
👨‍💼 <b>Администраторы бота:</b>

{admins_list}
"""
    await message.answer(response, parse_mode="HTML")


@admin_router.message(Command("get_user_info"))
async def get_user_info(message: Message, command: CommandObject):
    """Получение информации о пользователе по ID"""
    if not is_admin(message.from_user.id):
        return

    if not command.args:
        await message.answer("❗ Укажите ID пользователя: /get_user_info 123456789")
        return

    try:
        user_id = int(command.args.strip())
        user = await message.bot.get_chat(user_id)

        response = f"""
👤 <b>Информация о пользователе:</b>
🆔 ID: <code>{user.id}</code>
📝 Имя: {user.first_name}
👥 Фамилия: {user.last_name or "Нет"}
🔗 Username: @{user.username or "Нет"}
🤖 Тип: {user.type}
"""
        await message.answer(response, parse_mode="HTML")

    except ValueError:
        await message.answer("❌ Неверный формат ID пользователя")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@admin_router.message(Command("update_commands"))
async def update_commands(message: Message):
    """Обновление списка команд бота"""
    if not is_admin(message.from_user.id):
        return

    try:
        from aiogram.types import BotCommand

        commands = [
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="help", description="Помощь"),
            # Админские команды
            BotCommand(command="admin_help", description="Админские команды"),
            BotCommand(command="get_channel_id", description="Получить ID канала"),
            BotCommand(command="get_chat_id", description="Получить ID чата"),
            BotCommand(command="list_admins", description="Список админов"),
            BotCommand(command="get_user_info", description="Инфо о пользователе"),
        ]

        await message.bot.set_my_commands(commands)
        await message.answer("✅ Список команд успешно обновлен")

    except Exception as e:
        await message.answer(f"❌ Ошибка при обновлении команд: {str(e)}")


@help_router.message(Command("help"))
async def help_command_with_buttons(message: Message):
    """Обработчик команды /help с кнопками"""
    help_text = """
🤖 <b>Помощь по боту</b>

Доступные команды:
/start - Запустить бота
/help - Показать помощь

💡 <b>Основные функции:</b>
• Получение информации
• Работа с данными
• Обратная связь с поддержкой

❓ <b>Часто задаваемые вопросы:</b>
<b>Q:</b> Как начать использовать бота?
<b>A:</b> Нажмите команду /start

<b>Q:</b> Где найти дополнительную информацию?
<b>A:</b> Посетите наш сайт или свяжитесь с поддержкой
"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏠 На главную", callback_data="main_menu"),
                InlineKeyboardButton(text="👤 Поддержка", callback_data="support"),
            ],
            [InlineKeyboardButton(text="🌐 Наш сайт", url="https://example.com")],
        ]
    )

    await message.answer(help_text, parse_mode="HTML", reply_markup=keyboard)
