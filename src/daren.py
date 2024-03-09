from data import config
from src.utils import Web3Utils
from fake_useragent import UserAgent
import aiohttp


class Daren:
    def __init__(self, key: str, thread: int, proxy=None):
        self.web3_utils = Web3Utils(key=key, http_provider=config.OPBNB_RPC)
        self.proxy = f"http://{proxy}" if proxy is not None else None
        self.thread = thread

        headers = {
            'User-Agent': UserAgent(os='windows').random,
        }

        connector = aiohttp.TCPConnector(force_close=True)
        self.session = aiohttp.ClientSession(
            headers=headers,
            trust_env=True,
            connector=connector,
            cookie_jar=aiohttp.CookieJar()
        )

    async def login(self):
        resp = await self.session.get(f"https://api.daren.market/v2/auth/web3/message?address={self.web3_utils.acct.address}", proxy=self.proxy)
        text = (await resp.json()).get("message")

        json_data = {
            "address": self.web3_utils.acct.address,
            "message": text,
            "signature": self.web3_utils.get_signed_code(text),
            "type": "NORMAL",
        }
        if config.REF_LINK: json_data['invitationCode'] = config.REF_LINK.split('=')[1]

        resp = await self.session.post("https://api.daren.market/v2/auth/web3/users", json=json_data, proxy=self.proxy)
        resp_json = await resp.json()

        self.session.headers['Authorization'] = resp_json.get('user').get('token')
        self.session.cookie_jar.update_cookies(resp.cookies)
        return True

    async def check_task(self, task_id: str, claimed: bool):
        resp = await self.session.get("https://api.daren.market/v2/tasks/", proxy=self.proxy)
        resp_json = await resp.json()

        for task in resp_json.get("myTasks"):
            if task["taskID"] == task_id:
                if claimed: return task['claimed']
                else: return task['completed']

    async def daily_check_in(self):
        resp = await self.session.post("https://api.daren.market/v2/tasks/+/DAILY_CHECK_IN/claim", proxy=self.proxy)
        return (await resp.json()).get('success')

    async def complete_opbnb_check_in(self):
        tx = {
            "from": self.web3_utils.acct.address,
            "to": self.web3_utils.w3.to_checksum_address("0xfe7079971c388463d18e83fbff363936150e9b92"),
            "value": 0,
            "nonce": self.web3_utils.w3.eth.get_transaction_count(self.web3_utils.acct.address),
            "gasPrice": self.web3_utils.w3.eth.gas_price,
            "chainId": 204,
            "data": "0x183ff085",
        }

        tx["gas"] = int(self.web3_utils.w3.eth.estimate_gas(tx))

        tx = self.web3_utils.w3.eth.account.sign_transaction(tx, self.web3_utils.acct.key.hex())
        transaction_hash = self.web3_utils.w3.eth.send_raw_transaction(tx.rawTransaction).hex()

        wait_tx = self.web3_utils.w3.eth.wait_for_transaction_receipt(transaction_hash)
        return wait_tx.status == 1, transaction_hash

    async def logout(self):
        await self.session.close()
