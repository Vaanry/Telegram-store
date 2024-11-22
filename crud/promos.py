from loguru import logger
from sqlalchemy import select, update, insert
from data import Promo, UsersPromo
from data.config import AsyncSessionLocal


@logger.catch
async def switch_promo_on(filename: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(insert(Promo), [{"file": filename}])


@logger.catch
async def check_promo():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = select(
                Promo.is_promo,
                Promo.file,
                Promo.downloads,
                Promo.id
            ).order_by(Promo.timestamp.desc())
            promos = await session.execute(query)
            promo = promos.fetchone()
    return promo


@logger.catch
async def update_promo(id: int, status: bool, downloads: int):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(
                update(Promo)
                .where(Promo.id == id)
                .values({"is_promo": status, "downloads": downloads}))


@logger.catch
async def add_user_promo(tg_id: int, promo_id: int):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(
                insert(UsersPromo), [{"tg_id": tg_id, "promo_id": promo_id}])
