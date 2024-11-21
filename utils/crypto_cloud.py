import asyncio
import json

import aiohttp
from loguru import logger

from config import CLOUD_TOKEN, SHOP_ID, MANAGER
from crud import db_api
from utils import bot_send_message, get_text, balance_replenished


@logger.catch
async def create_invoice(amount):

    url = "https://api.cryptocloud.plus/v2/invoice/create"

    headers = {
        "Authorization": CLOUD_TOKEN,
        "Content-Type": "application/json"
    }

    data = json.dumps({
        "amount": amount,
        "shop_id": SHOP_ID,
        "currency": "USD",
        "add_fields": {
            "available_currencies": ["USDT_TRC20", "LTC", "BTC", "ETH"]
        }
    })

    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.post(url, headers=headers, data=data) as response:
            invoice = await response.json()
    return invoice


@logger.catch
async def crypto_cloud_balance_updater():
    unpaid_invoices = await db_api.get_cryptocloud_unpaid_invoices()
    invoice_ids = [invoice for invoice in unpaid_invoices if invoice is not None]

    url = "https://api.cryptocloud.plus/v2/invoice/merchant/info"
    headers = {
        "Authorization": CLOUD_TOKEN,
        'Content-Type': 'application/json; charset=UTF-8',
    }

    data = json.dumps({
        "uuids": invoice_ids
    })

    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.post(url, headers=headers, data=data) as response:
            invoices_info = await response.json()
    if invoices_info['status'] == 'success':
        tasks = [asyncio.create_task(process_balance_update(invoice)) for invoice in invoices_info['result']]
        await asyncio.gather(*tasks)
    else:
        pass


@logger.catch
async def process_balance_update(invoice):
    if invoice['status'] == 'paid' or invoice['status'] == 'overpaid' or invoice['status'] == 'partial':
        uuid = invoice['uuid']
        currency = invoice['currency']['code']
        amount_currency = invoice['amount_paid']
        amount_usd = invoice['amount_paid_usd']
        payment_info = await db_api.get_payment_info_by_uuid(uuid)
        tg_id = payment_info.tg_id
        # amount = payment_info.amount

        await db_api.confirm_cryptocloud_payment(uuid)

        user_info = await db_api.get_user(tg_id)
        username = user_info.username
        balance = float(user_info.balance)
        current_language = user_info.language
        new_balance = balance + float(amount_usd)
        await db_api.update_user_balance(tg_id, new_balance)
        logger.warning(f'User {tg_id}: payment_id: {uuid}, start_balance: {balance}, payment_amount: {amount_usd}, new_balance: {new_balance}, status: SUCCESS')
        text = get_text('pay_confirm', current_language)
        mess = balance_replenished(amount_usd, current_language)
        manager_text = f'{username} оплатил(а) ваш счёт {uuid} в CryptoCloud. Вы получили {amount_currency} {currency} (${amount_usd}).'
        await bot_send_message(tg_id, text)
        await bot_send_message(tg_id, mess)
        await bot_send_message(MANAGER, manager_text)
    else:
        pass
