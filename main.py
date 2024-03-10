from src import Daren
from data import config
from src.utils import random_line, logger
import asyncio


async def StartDaren(thread):
    logger.info(f"Поток {thread} | Начал работу")
    while True:
        act = await random_line('data/accounts.txt')
        if not act: break

        if '::' in act:
            private_key, proxy = act.split('::')
        else:
            private_key = act
            proxy = None

        daren = Daren(key=private_key, thread=thread, proxy=proxy)

        if await daren.login():
            # daily check in
            if not await daren.check_task(task_id="DAILY_CHECK_IN", claimed=True) and await daren.check_task(task_id="DAILY_CHECK_IN", claimed=False):
                if await daren.daily_check_in():
                    logger.success(f"Поток {thread} | Выполнил check-in {daren.web3_utils.acct.address}")
                else:
                    logger.error(f"Поток {thread} | Не выполнил check-in {daren.web3_utils.acct.address}")
            else:
                logger.warning(f"Поток {thread} | Уже выполнил check-in {daren.web3_utils.acct.address}")

            # opBNB Check-in
            if not await daren.check_task(task_id="OP_BNB_CHECK_IN", claimed=True) and not await daren.check_task(task_id="OP_BNB_CHECK_IN", claimed=False):
                try:
                    status, tx_hash = await daren.complete_opbnb_check_in()
                    if status:
                        logger.success(f"Поток {thread} | Выполнил opBNB check-in {daren.web3_utils.acct.address}:{tx_hash}")
                    else:
                        logger.error(f"Поток {thread} | Не выполнил opBNB check-in {daren.web3_utils.acct.address}:{tx_hash}")
                except Exception as e:
                    logger.error(f"Поток {thread} | Не выполнил opBNB check-in {daren.web3_utils.acct.address}: {e}")
            else:
                logger.warning(f"Поток {thread} | Уже выполнил opBNB check-in {daren.web3_utils.acct.address}")

            await daren.logout()


async def main():
    print("Автор софта: https://t.me/ApeCryptor")

    thread_count = int(input("Введите кол-во потоков: "))
    # thread_count = 1
    tasks = []
    for thread in range(1, thread_count+1):
        tasks.append(asyncio.create_task(StartDaren(thread)))

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
