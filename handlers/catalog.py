from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import CallbackQuery
from loguru import logger

from crud import catalogs, users, orders
from app import dp
from utils import get_text, output_format, get_order_format


category_cb = CallbackData('category', 'name', 'action')
country_cb = CallbackData('country', 'name', 'action')
mark_cb = CallbackData('mark', 'name', 'action')
model_cb = CallbackData('model', 'name', 'action')
age_cb = CallbackData('age', 'name', 'action')
cc_cb = CallbackData('cc', 'name', 'action')
price_cb = CallbackData('price', 'name', 'action')


class Order(StatesGroup):
    amount = State()


@logger.catch
@dp.message_handler(regexp='.*Каталог|.*Catalog')
async def catalog(message: Message, state: FSMContext):
    markup = InlineKeyboardMarkup()
    categories = await catalogs.get_categories()
    for category in sorted(categories):
        markup.add(InlineKeyboardButton(
            category, callback_data=category_cb.new(name=category, action='view')))
    tg_id = message.chat.id
    current_language = await users.get_user_language(tg_id)
    text = get_text('category', current_language)
    await message.answer(text, reply_markup=markup)
    logger.debug(f'User {tg_id}: catalog')


@dp.callback_query_handler(lambda x: x.data == 'Back', state="*")
async def process_category_back(callback: CallbackQuery, state: FSMContext):
    await catalog(callback.message, state)


@logger.catch
@dp.callback_query_handler(category_cb.filter(action='view'), state="*")
async def country_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):
    category_name = callback_data['name']
    markup = InlineKeyboardMarkup(row_width=2)
    countries = await catalogs.get_countries_by_category(category_name)
    buttons = [InlineKeyboardButton(
        country, callback_data=country_cb.new(name=country, action='view')) for country in sorted(countries)]
    markup.add(*buttons)
    tg_id = query.from_user.id
    current_language = await users.get_user_language(tg_id)
    text = get_text('country', current_language)
    back = get_text('back', current_language)
    markup.add(InlineKeyboardButton(back, callback_data='Back'))
    await query.message.answer(text, reply_markup=markup)
    await state.update_data(category_name=category_name)
    logger.debug(f'User {tg_id}: category: {category_name}')


@logger.catch
@dp.callback_query_handler(country_cb.filter(action='view'), state="*")
async def mark_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):
    async with state.proxy() as data:
        if 'category_name' in data.keys():
            category_name = data['category_name']

    country = callback_data['name']
    markup = InlineKeyboardMarkup(row_width=4)
    types = await catalogs.get_manufactorers_by_category(category_name, country)
    for name in types:
        markup.add(InlineKeyboardButton(
            name, callback_data=mark_cb.new(name=name, action='view')))
    tg_id = query.from_user.id
    current_language = await users.get_user_language(tg_id)
    text = get_text('mark', current_language)
    back = get_text('back', current_language)
    markup.add(InlineKeyboardButton(back, callback_data=category_cb.new(name=category_name, action='view')))
    await query.message.answer(text, reply_markup=markup)
    await state.update_data(country=country)
    logger.debug(f'User {tg_id}: country: {country}')


@logger.catch
@dp.callback_query_handler(mark_cb.filter(action='view'), state="*")
async def model_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):
    async with state.proxy() as data:
        if 'category_name' in data.keys():
            category_name = data['category_name']

    mark = callback_data['name']
    markup = InlineKeyboardMarkup(row_width=4)
    types = await catalogs.get_models_by_mark(category_name, mark)
    for name in types:
        markup.add(InlineKeyboardButton(
            name.model, callback_data=model_cb.new(name=name.model, action='view')))
    tg_id = query.from_user.id
    current_language = await users.get_user_language(tg_id)
    text = get_text('model', current_language)
    back = get_text('back', current_language)
    markup.add(InlineKeyboardButton(back, callback_data=category_cb.new(name=category_name, action='view')))
    await query.message.answer(text, reply_markup=markup)
    await state.update_data(mark=mark)
    logger.debug(f'User {tg_id}: mark: {mark}')


@logger.catch
@dp.callback_query_handler(model_cb.filter(action='view'), state="*")
async def material_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):
    async with state.proxy() as data:
        if 'country' in data.keys():
            country = data['country']
        if 'mark' in data.keys():
            mark = data['mark']

    model = callback_data['name']
    tg_id = query.from_user.id
    current_language = await users.get_user_language(tg_id)
    markup = InlineKeyboardMarkup(row_width=2)
    back = get_text('back', current_language)

    bike = await catalogs.get_store(model)
    sort_type = bike.sort_type
    catalog = " ---> ".join([country, mark, model])
    await state.update_data(model=model, catalog=catalog)
    logger.debug(f'User {tg_id}: model: {model}')

    if sort_type == 'age':
        await age_handler(model, markup, back, country)
        text = get_text('age', current_language)
        await query.message.answer(text, reply_markup=markup)

    elif sort_type == 'cc':
        await vollume_handler(model, markup, back, country)
        text = get_text('vollume', current_language)
        await query.message.answer(text, reply_markup=markup)

    else:
        all_prices = await catalogs.get_prices(model)
        prices = [price for price in all_prices if price is not None]
        buttons = [InlineKeyboardButton(
            name, callback_data=price_cb.new(name=name, action='view')) for name in sorted(prices) if name is not None and name != 'NaN']
        markup.add(*buttons)
        markup.add(InlineKeyboardButton(back, callback_data=country_cb.new(name=country, action='view')))
        text = get_text('price', current_language)
        await query.message.answer(text, reply_markup=markup)


@logger.catch
async def vollume_handler(model, markup, back, country):
    all_states = await catalogs.get_vollumes(model)
    vollumes = [state for state in all_states if state is not None]
    buttons = [InlineKeyboardButton(
        name, callback_data=cc_cb.new(name=name, action='view')) for name in sorted(vollumes) if name is not None and name != 'NaN']
    markup.add(*buttons)
    markup.add(InlineKeyboardButton(back, callback_data=country_cb.new(name=country, action='view')))


@logger.catch
async def age_handler(model, markup, back, country):
    ages = await catalogs.get_ages(model)
    markup.add(InlineKeyboardButton(
        'Mix', callback_data=age_cb.new(name='Mix', action='view')))
    for age in sorted(ages):
        if age is not None:
            markup.add(InlineKeyboardButton(
                age, callback_data=age_cb.new(name=age, action='view')))
    markup.add(InlineKeyboardButton(back, callback_data=country_cb.new(name=country, action='view')))


@logger.catch
@dp.callback_query_handler(age_cb.filter(action='view'), state="*")
async def vollume_age_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):
    async with state.proxy() as data:
        if 'model' in data.keys():
            model = data['model']
            country = data['country']

    age = callback_data['name']
    markup = InlineKeyboardMarkup(row_width=4)
    all_vollumes = await catalogs.get_vollumes(model, age=age)
    vollumes = [cc for cc in all_vollumes if state is not None]
    buttons = [InlineKeyboardButton(
        name, callback_data=cc_cb.new(name=name, action='view')) for name in sorted(vollumes) if name is not None and name != 'NaN']
    markup.add(*buttons)
    tg_id = query.from_user.id
    current_language = await users.get_user_language(tg_id)
    text = get_text('vollume', current_language)
    back = get_text('back', current_language)
    markup.add(InlineKeyboardButton(back, callback_data=country_cb.new(name=country, action='view')))
    await state.update_data(age=age)
    await query.message.answer(text, reply_markup=markup)
    logger.debug(f'User {tg_id}: age: {age}')


@logger.catch
@dp.callback_query_handler(cc_cb.filter(action='view'), state="*")
async def price_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):
    cc = int(callback_data.pop('name'))
    async with state.proxy() as data:
        age = data.get('age')
        model = data['model']

    markup = InlineKeyboardMarkup(row_width=4)
    prices = await catalogs.get_prices(model, cc=cc, age=age)
    buttons = [InlineKeyboardButton(
        name, callback_data=price_cb.new(name=name, action='view')) for name in sorted(prices) if name is not None and name != 'NaN']
    markup.add(*buttons)
    tg_id = query.from_user.id
    current_language = await users.get_user_language(tg_id)
    text = get_text('price', current_language)
    back = get_text('back', current_language)
    markup.add(InlineKeyboardButton(back, callback_data=model_cb.new(name=model, action='view')))
    await state.update_data(cc=cc)
    await query.message.answer(text, reply_markup=markup)


@logger.catch
@dp.callback_query_handler(price_cb.filter(action='view'), state="*")
async def choose_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):
    price = float(callback_data.pop('name'))
    async with state.proxy() as data:
        catalog = data['catalog']
        model = data['model']
        age = data.get('age')
        cc = data.get('cc')

    quantity = await catalogs.get_items_quantity(model, price, cc, age)
    tg_id = query.from_user.id
    current_language = await users.get_user_language(tg_id)
    text_format = output_format(catalog, quantity, current_language)
    price_text = get_text("price_choosen", current_language)
    text_format += f'{price_text} - {price}'

    if cc:
        cc_text = get_text("vollume_choosen", current_language)
        text_format += f'{cc_text} - {cc}'

    if age:
        age_text = get_text("age_choosen", current_language)
        text_format += f'{age_text} - {age}'

    await state.update_data(price=price, text_format=text_format, quantity=quantity)
    await query.message.answer(text_format)
    if int(quantity) <= 0:
        await query.message.answer('Закончился товар | Out of stock')
    else:
        text_count = get_text('count', current_language)
        await query.message.answer(text_count)
        await Order.amount.set()
    logger.debug(f'User {tg_id}: choose_handler: {cc}')


@logger.catch
@dp.message_handler(state=Order.amount)
async def process_submit(message: Message, state: FSMContext):
    async with state.proxy() as data:
        quantity = data['quantity']
    tg_id = message.from_user.id
    current_language = await users.get_user_language(tg_id)
    logger.debug(f'User {tg_id}: process_submit: {message.text}')
    try:
        amount = int(message.text)
        if amount < 1 or amount != float(message.text):
            logger.debug(f'User {tg_id}: process_submit: incorrect quantity')
            await message.answer(get_text("incorrect quantity", current_language))

        elif int(quantity) < amount:
            logger.debug(f'User {tg_id}: process_submit: low_items')
            await message.answer(get_text("low_items", current_language))
        else:
            async with state.proxy() as data:
                data['amount'] = amount
                model = data['model']
                age = data.get('age')
                cc = data.get('cc')
                price = data.get('price', 0)
                text_format = data['text_format']
            purchase = amount * float(price)
            order, submit = get_order_format(current_language, amount, purchase, text_format)
            back = get_text('back', current_language)
            await orders.add_order(tg_id, amount, model, purchase, cc, age)
            markup = InlineKeyboardMarkup(row_width=2)
            submit_button = InlineKeyboardButton(submit, callback_data='submit_buy')
            back_batton = InlineKeyboardButton(back, callback_data='Back')
            markup.add(*[submit_button, back_batton])
            await message.answer(order, reply_markup=markup)
    except ValueError:
        from .keyboard_exept import submit_cheker
        logger.debug(f'User {tg_id}: process_submit: ValueError')
        await submit_cheker(message, state, current_language)
