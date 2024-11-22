import asyncio

from loguru import logger
from sqlalchemy import select, update, func
from data import Manufacturer, Catalog, Items
from data.config import AsyncSessionLocal


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
            query = select(func.sum(Catalog.quantity).label('sum'))
            records = await session.execute(query)
    return records.scalar()


@logger.catch
async def get_categories():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = select(
                Catalog.type,
                func.sum(Catalog.quantity)
                       .label('sum')
            ).group_by(Catalog.type)
            records = await session.execute(query)
            categories = [row for row in records if row[1] is not None]
            categories = [row[0] for row in categories if row[1] > 0]
    return categories


@logger.catch
async def get_countries():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = select(Manufacturer.country).distinct()
            records = await session.execute(query)
            categories = records.scalars().all()
    return categories


async def get_countries_by_category(category_name: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = (
                select(Manufacturer.country)
                .distinct()
                .join(Catalog, Catalog.manufacturer == Manufacturer.name)
                .where(
                    Catalog.type == category_name,
                    Catalog.quantity > 0,
                    Catalog.quantity.is_not(None)
                )
            )
            actual_types = await session.execute(query)
            types = actual_types.scalars().all()
    return types


@logger.catch
async def get_manufactorers_by_category(category_name: str, country: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = (
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

            actual_types = await session.execute(query)
            types = actual_types.scalars().all()
    return types


@logger.catch
async def get_models_by_mark(category_name: str, mark: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = (
                select(Catalog.model).
                where(Catalog.type == category_name,
                      Catalog.manufacturer == mark,
                      Catalog.quantity > 0,
                      Catalog.quantity.is_not(None))
            )
            actual_types = await session.execute(query)
            models = actual_types.fetchall()
    return models


@logger.catch
async def get_store(model: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = select(
                Catalog.manufacturer,
                Catalog.quantity,
                Catalog.sort_type).where(Catalog.model == model)
            actual = await session.execute(query)
            types = actual.fetchone()
    return types


@logger.catch
async def get_ages(model: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = select(Items.age).distinct().where(Items.model == model)
            actual_ages = await session.execute(query)
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
