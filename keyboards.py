from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

markup = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton("/led_on"), KeyboardButton("/led_off")]]
)
