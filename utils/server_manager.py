import os

import asyncssh
from dotenv import load_dotenv

load_dotenv()

SERVER_IP = os.getenv("SERVER_IP")
SERVER_USERNAME = os.getenv("SERVER_USERNAME")
SERVER_PASSWORD = os.getenv("SERVER_PASSWORD")


class ServerManager:
    def __init__(self):
        pass

    @staticmethod
    async def run_command(command: str) -> str:
        async with asyncssh.connect(
            SERVER_IP, username=SERVER_USERNAME, password=SERVER_PASSWORD, known_hosts=None
        ) as conn:
            result = await conn.run(command, check=True)
            return result.stdout

    async def restart(self) -> None:
        await self.run_command("sudo systemctl restart tgbot")

    async def get_logs(self) -> str:
        logs = await self.run_command("sudo journalctl -u tgbot -n 20 --no-pager")
        return logs
