import asyncio
import itertools
from abc import ABCMeta, abstractmethod

import aiohttp
from aiohttp import ClientSession


class BaseICD(metaclass=ABCMeta):
    @staticmethod
    async def exception_handler(e: Exception) -> None:
        """
        Logs exception and delays execution

        :param e: Exception
        :return: None

        """

        print(f"Exception: {e}.\nSleep 60 seconds before next execution.")
        await asyncio.sleep(60)

    @abstractmethod
    async def get_icd_data(self, session: ClientSession, url: str) -> list[dict[str, str]]:
        """
        Fetches data from the provided URL

        :param session: current aiohttp.ClientSession
        :param url: URL to fetch data from

        :return: Fetched data
        :rtype: list[dict]

        """

    async def get_all(self, session: ClientSession, url: str) -> list[dict[str, str]]:
        """
        Wrapper method to fetch data using 'get_icd_data' method

        :param session: current aiohttp.ClientSession
        :param url: URL to fetch data from

        :return: Fetch data
        :rtype: list[dict]

        """

        return await self.get_icd_data(session=session, url=url)

    async def run_all(self, session: ClientSession, urls: list[str]) -> list[dict[str, str]]:
        """
        :param session: current aiohttp.ClientSession
        :param urls: List of URLs to fetch from

        :return: fetch data
        :rtype: list[dict]

        """

        tasks = [self.get_all(session, url) for url in urls]
        result = await asyncio.gather(*tasks)

        return list(itertools.chain(*result))

    async def main(self, urls: list[str]) -> list[dict[str, str]]:
        """
        Method that fetches data in batches
        in order to avoid blocking by the server

        :param urls: List of URLs to fetch
        :param step: Number of URLs to fetch per batch request

        :return: List of fetched data
        :rtype: list[dict]

        """

        result = []
        start = 0
        step = 100

        async with aiohttp.ClientSession() as session:
            print(f"Sleeping 30 seconds after each request to avoid server blocking")
            while start < len(urls):
                try:
                    # end of batch
                    end = min(start + step, len(urls))

                    # slice urls to fetch in this batch
                    batch_urls = urls[start:end]
                    batch_response = await self.run_all(session=session, urls=batch_urls)
                    result.append(batch_response)

                    # update start index for the next batch
                    start += step
                    print(f"[{end}/{len(urls)}]")

                    # sleep if more urls remain
                    if end != len(urls):
                        await asyncio.sleep(30)

                except Exception as e:
                    await self.exception_handler(e=e)

        return list(itertools.chain(*result))
