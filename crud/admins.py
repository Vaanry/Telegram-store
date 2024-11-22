import datetime

from loguru import logger
from sqlalchemy import select, insert
from data import Users, Manufacturer, Orders, Catalog
from data.config import AsyncSessionLocal


@logger.catch
async def get_new_users(offset: int):
    data = datetime.datetime.now() - datetime.timedelta(days=offset)
    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = select(
                Users.tg_id,
                Users.username,
                Users.reg_date,
                Users.source).where(Users.reg_date >= data)
            users = await session.execute(query)
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
    print(mark, type, model)
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(insert(Catalog), [{"manufacturer": mark, "type": type, "model": model}])


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
                Orders.purchase,
                Orders.order_archive
            ).join(Users, Users.tg_id == Orders.tg_id
                   ).where(Users.username == username,
                           Orders.is_paid == True)
            orders = await session.execute(query)
            user_orders = orders.fetchall()
    return user_orders
