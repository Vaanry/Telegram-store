from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


cancel_message = '🚫Отменить'
confirm_message = '✅Подтвердить'
back_message = '👈Назад'
mass_letters = '📨Массовая рассылка'
users_log = '🆕Новые пользователи'
load_log = '📉Выгрузить лог'
add_cat = '➕Добавить категорию'
user_balance = '💰Пополнить баланс пользователя'
user_orders = '📋Получить заказы пользователя'


button_user_balance = KeyboardButton(user_balance)
button_confirm = KeyboardButton(confirm_message)
button_cancel = KeyboardButton(cancel_message)
button_letters = KeyboardButton(mass_letters)
button_users_log = KeyboardButton(users_log)
button_load_log = KeyboardButton(load_log)
button_add_cat = KeyboardButton(add_cat)
button_user_orders = KeyboardButton(user_orders)

admin_markup = ReplyKeyboardMarkup(selective=True, resize_keyboard=True, row_width=2)
admin_markup.add(button_user_balance, button_user_orders, button_letters, button_users_log, button_load_log, button_add_cat)

confirm_markup = ReplyKeyboardMarkup(selective=True, resize_keyboard=True, row_width=2)
confirm_markup.add(button_confirm, button_cancel)

cancel_markup = ReplyKeyboardMarkup(selective=True, resize_keyboard=True)
cancel_markup.add(button_cancel)
