import asyncio
import datetime

from loguru import logger
from sqlalchemy import select, update, insert, delete, func
from data import Users, Payment, Manufacturer, Orders, Catalog, Items, Promo, UsersPromo
from data.config import AsyncSessionLocal

##########CATALOG#################################################################################################


@logger.catch
async def catalog_qnt(row, session):
    model = row[0]
    quantity = row[1]
    await session.execute(update(Catalog).where(Catalog.model == model).values({"quantity": quantity}))


@logger.catch
async def start_count_data():
    '''
    Пересчитывает количество товара в каждой из категорий и обновляет таблицу.
    '''
    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = select(
                Catalog.model, 
                func.count(Items.id)
                .label('qnt')).join(Items, isouter=True).group_by(Catalog.model)
            records = await session.execute(query)
            tasks = [asyncio.create_task(catalog_qnt(row, session)) for row in records]
            await asyncio.gather(*tasks)
            await session.commit()


@logger.catch
async def give_all_rows():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            records = await session.execute(
                select(func.sum(Catalog.quantity).label('sum')))
    return records.scalar()


@logger.catch
async def get_categories():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            records = await session.execute(
                select(Catalog.type, 
                       func.sum(Catalog.quantity).label('sum')).
                group_by(Catalog.type))
            categories = [row for row in records if row[1] is not None]
            categories = [row[0] for row in categories if row[1] > 0]
    return categories


@logger.catch
async def get_countries():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            records = await session.execute(
                select(Manufacturer.country).
                distinct())
            categories = records.scalars().all()
    return categories


async def get_countries_by_category(category_name: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            stmt = (
                select(Manufacturer.country)
                .distinct()
                .join(Catalog, Catalog.manufacturer == Manufacturer.name)
                .where(
                    Catalog.type == category_name,
                    Catalog.quantity > 0,
                    Catalog.quantity.is_not(None)
                )
            )
            actual_types = await session.execute(stmt)
            types = actual_types.scalars().all()
    return types


@logger.catch
async def get_manufactorers_by_category(category_name: str, country: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            stmt = (
                select(Manufacturer.name)
                .distinct()
                .join(Catalog, Catalog.manufacturer == Manufacturer.name)
                .where(
                    Manufacturer.country == country,
                    Catalog.type == category_name,
                    Catalog.quantity > 0,
                    Catalog.quantity.is_not(None)
                )
            )

            actual_types = await session.execute(stmt)
            types = actual_types.scalars().all()
    return types


@logger.catch
async def get_models_by_mark(category_name: str, mark: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            stmt = (
                select(Catalog.model).
                where(Catalog.type == category_name,
                      Catalog.manufacturer == mark,
                      Catalog.quantity > 0,
                      Catalog.quantity.is_not(None))
            )
            actual_types = await session.execute(stmt)
            models = actual_types.fetchall()
    return models


@logger.catch
async def get_store(model: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            actual = await session.execute(
                select(Catalog.manufacturer,
                       Catalog.quantity,
                       Catalog.sort_type).
                where(Catalog.model == model))
            types = actual.fetchone()
    return types


@logger.catch
async def get_ages(model: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            actual_ages = await session.execute(select(Items.age).distinct().where(Items.model == model))
            ages = actual_ages.scalars().all()
    return ages


@logger.catch
async def get_vollumes(model: str, age: str = None):
    filters = [Items.model == model]

    if age is not None and age != 'Mix':
        filters.append(Items.age == age)

    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = select(Items.cc).distinct().where(*filters)
            actual_vollumes = await session.execute(query)
            vollumes = actual_vollumes.scalars().all()
    return vollumes


@logger.catch
async def get_items_quantity(model: str, price: float, vollume: int = None, age: str = None):
    filters = [Items.model == model, Items.price == price]

    # Добавляем условия в список фильтров
    if vollume is not None:
        filters.append(Items.cc == vollume)

    if age is not None and age != 'Mix':
        filters.append(Items.age == age)

    async with AsyncSessionLocal() as session:
        async with session.begin():
            nums = await session.execute(select(func.count(Items.id)).where(*filters))

    return nums.scalar()


@logger.catch
async def get_prices(model: str, cc: int = None, age: str = None):
    filters = [Items.model == model]

    # Добавляем условия в список фильтров
    if cc is not None:
        filters.append(Items.cc == cc)

    if age is not None and age != 'Mix':
        filters.append(Items.age == age)

    async with AsyncSessionLocal() as session:
        query = select(Items.price).distinct().where(*filters)
        async with session.begin():
            nums = await session.execute(query)
            prices = nums.scalars().all()
    return prices
##########USERS#################################################################################################

@logger.catch
async def get_user_language(tg_id: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            user = await session.execute(select(Users.language).where(Users.tg_id == tg_id))
    if user:
        return user.scalar()
    else:
        return None


@logger.catch
async def update_user_language(tg_id: str, new_lang: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(update(Users).where(Users.tg_id == tg_id).values({"language": new_lang}))


@logger.catch
async def get_user_balance(tg_id: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            user = await session.execute(select(Users.balance).where(Users.tg_id == tg_id))
    return user.scalar()


@logger.catch
async def update_user_balance(tg_id: str, balance: float):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(update(Users).where(Users.tg_id == tg_id).values({"balance": balance}))


@logger.catch
async def add_user(tg_id: int, username: str, source: str = None):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            if source:
                await session.execute(insert(Users), [{"tg_id": tg_id, "username": username, "source": source}])
            else:
                await session.execute(insert(Users), [{"tg_id": tg_id, "username": username}])


@logger.catch
async def get_user(tg_id: int):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            user = await session.execute(select(Users).where(Users.tg_id == tg_id))
            info = user.scalars().first()
    if info:
        return info
    else:
        return False


@logger.catch
async def get_user_by_username(username: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            user = await session.execute(select(Users).where(Users.username == username))
            info = user.scalars().first()
    if info:
        return info
    else:
        return False


@logger.catch
async def get_all_users():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            all_users = await session.execute(select(Users))
            users = all_users.scalars().all()
    return users


@logger.catch
async def get_all_unblock_users():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            all_users = await session.execute(select(Users).where(Users.active == True, Users.block_bot == False))
            users = all_users.scalars().all()
    return users


@logger.catch
async def update_block_bot_status(tg_id: str, status: bool):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(update(Users).where(Users.tg_id == tg_id).values({"block_bot": status}))


@logger.catch
async def update_active_status(tg_id: str, status: bool):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(update(Users).where(Users.tg_id == tg_id).values({"active": status}))

##########ORDERS#################################################################################################

@logger.catch
async def add_order(tg_id: int, amount: int, model: str, purchase: float, cc: int = None, age: str = None):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(
                insert(Orders),
                [{
                    "tg_id": tg_id,
                    "quantity": amount,
                    "model": model,
                    "purchase": purchase,
                    "cc": cc,
                    "age": age
                }])


@logger.catch
async def get_last_order(tg_id: int):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = select(
                Orders.model,
                Orders.quantity,
                Orders.purchase,
                Orders.is_paid,
                Orders.cc,
                Orders.age
            ).where(
                Orders.tg_id == tg_id
            ).order_by(
                Orders.timestamp.desc())
            orders = await session.execute(query)
            order = orders.fetchone()
    return order


@logger.catch
async def give_order(model, amount, cc: int = None, age: str = None):
    rows = []
    filters = [Items.model == model]

    if age is not None and age != 'Mix':
        filters.append(Items.age == age)

    if cc is not None:
        filters.append(Items.cc == cc)

    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = select(Items.row).where(*filters).limit(amount)
            records = await session.execute(query)
            rows_count = records.scalars().all()
            print(f"Number of records fetched: {len(rows_count)}")
            for row in rows_count:
                rows.append(row)

    return rows


@logger.catch
async def update_order(tg_id: int, new_path: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            max_time = await session.execute(select(func.max(Orders.timestamp)).where(Orders.tg_id == tg_id))
            await session.execute(update(Orders).where(Orders.tg_id == tg_id, Orders.timestamp == max_time.scalar()).values({"is_paid": True, "order_archive": new_path}))

##########ADMIN#################################################################################################

@logger.catch
async def get_new_users(offset: int):
    data = datetime.datetime.now() - datetime.timedelta(days=offset)
    async with AsyncSessionLocal() as session:
        async with session.begin():
            users = await session.execute(select(Users.tg_id, Users.username, Users.reg_date, Users.source).where(Users.reg_date >= data))
    return users.fetchall()


@logger.catch
async def get_category(name: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = select(Manufacturer.name).where(Manufacturer.name == name)
            exist = await session.execute(query)
    return exist.scalar()


@logger.catch
async def add_category(name: str, country: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(insert(Manufacturer), [{"name": name, "country": country}])


@logger.catch
async def add_catalog(mark: str, type: str, model: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(insert(Catalog), [{"manufactorer": mark, "type": type, model: "model"}])


async def get_admins():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = select(Users.tg_id).where(Users.is_admin == True)
            users = await session.execute(query)
            admins = users.scalars().all()
    return admins


async def get_user_orders(username: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = select(
                Orders.model,
                Orders.order_archive
            ).join(Users, Users.tg_id == Orders.tg_id
                   ).where(Users.username == username,
                           Orders.is_paid == True)
            orders = await session.execute(query)
            user_orders = orders.fetchall()
    return user_orders


##########PROMO#################################################################################################

async def switch_promo_on(filename: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(insert(Promo), [{"file": filename}])


async def check_promo():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            promos = await session.execute(select(Promo.is_promo, Promo.file, Promo.downloads,
                                                  Promo.id).order_by(Promo.timestamp.desc()))
            promo = promos.fetchone()
    return promo


async def update_promo(id: int, status: bool, downloads: int):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(update(Promo).where(Promo.id == id).values({"is_promo": status, "downloads": downloads}))


async def add_user_promo(tg_id: int, promo_id: int):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(insert(UsersPromo), [{"tg_id": tg_id, "promo_id": promo_id}])


##########PAYMENT#################################################################################################


@logger.catch
async def add_cryptocloud_payment(tg_id: int, amount: float, uuid: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(insert(Payment), [{"tg_id": tg_id, "amount": amount, "uuid": uuid}])


@logger.catch
async def get_cryptocloud_unpaid_invoices():
    date = datetime.datetime.now() - datetime.timedelta(days=1)
    async with AsyncSessionLocal() as session:
        async with session.begin():
            invoices = await session.execute(select(Payment.uuid).where(Payment.confirmed == False, Payment.timestamp >= date))
    return invoices.scalars()


@logger.catch
async def get_payment_info_by_uuid(uuid: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            payment_info = await session.execute(select(Payment).where(Payment.uuid == uuid))
            info = payment_info.scalars().first()
    return info


@logger.catch
async def confirm_cryptocloud_payment(uuid: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(update(Payment).where(Payment.uuid == uuid).values({"confirmed": True}))
