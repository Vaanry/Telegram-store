from loguru import logger
from sqlalchemy import select, update, insert, delete, func
from data import Orders, Items
from data.config import AsyncSessionLocal


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
                # await session.execute(delete(Items).where(Items.row == row)) debug mode

    return rows


@logger.catch
async def update_order(tg_id: int, new_path: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            time_query = select(
                func.max(Orders.timestamp)
            ).where(Orders.tg_id == tg_id)
            max_time = await session.execute(time_query)
            await session.execute(
                update(Orders)
                .where(Orders.tg_id == tg_id,
                       Orders.timestamp == max_time.scalar()
                       ).values({
                           "is_paid": True,
                           "order_archive": new_path}
                )
            )
