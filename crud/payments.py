import datetime

from loguru import logger
from sqlalchemy import select, update, insert
from data import Payment
from data.config import AsyncSessionLocal


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
            query = select(
                Payment.uuid
            ).where(Payment.confirmed == False,
                    Payment.timestamp >= date)
            invoices = await session.execute(query)
    return invoices.scalars()


@logger.catch
async def get_payment_info_by_uuid(uuid: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = select(Payment).where(Payment.uuid == uuid)
            payment_info = await session.execute(query)
            info = payment_info.scalars().first()
    return info


@logger.catch
async def confirm_cryptocloud_payment(uuid: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(
                update(Payment)
                .where(Payment.uuid == uuid)
                .values({"confirmed": True}))
