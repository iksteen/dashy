from aiohttp import ClientSession

from dashy.services import ServiceProvider


class AiohttpProvider(ServiceProvider[ClientSession]):
    session: ClientSession

    async def start(self) -> ClientSession:
        self.session = ClientSession()
        return self.session

    async def stop(self) -> None:
        await self.session.close()
