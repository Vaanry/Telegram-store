from loguru import logger
from sqlalchemy import select, update, insert
from data import Users
from data.config import AsyncSessionLocal


@logger.catch
async def get_user_language(tg_id: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = select(Users.language).where(Users.tg_id == tg_id)
            user = await session.execute(query)
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
            query = select(Users.balance).where(Users.tg_id == tg_id)
            user = await session.execute(query)
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
            query = select(Users).where(Users.tg_id == tg_id)
            user = await session.execute(query)
            info = user.scalars().first()
    if info:
        return info
    else:
        return False


@logger.catch
async def get_user_by_username(username: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = select(Users).where(Users.username == username)
            user = await session.execute(query)
            info = user.scalars().first()
    if info:
        return info
    else:
        return False


@logger.catch
async def get_all_users():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = select(Users)
            all_users = await session.execute(query)
            users = all_users.scalars().all()
    return users


@logger.catch
async def get_all_unblock_users():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            query = select(Users).where(Users.active == True, Users.block_bot == False)
            all_users = await session.execute(query)
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
