from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

markup = ReplyKeyboardMarkup()
# markup.row(KeyboardButton("/led_on"), KeyboardButton("/led_off"))
# markup.row(KeyboardButton("/work"), KeyboardButton("/rest"),
markup.row(KeyboardButton("🏡"), KeyboardButton("lk"))
markup.row(KeyboardButton("❤️"))
markup.row(KeyboardButton("weather"), KeyboardButton("internet"), KeyboardButton("bill"))
