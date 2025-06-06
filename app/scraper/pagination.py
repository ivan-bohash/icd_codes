import aiohttp
from lxml import html
from typing import Type

from app.db.init_db import SessionLocal
from app.config import settings
from app.services.icd_codes.pagination import PaginationService
from app.services.icd_codes.data_parser import DataParser
from app.services.icd_codes.retry_decorator import retry

from app.db.models.pagination import PaginationBaseModel, PaginationBillModel, PaginationNonBillModel


class PaginationParser:
    def __init__(self, base_url, pagination_model) -> None:
        """
        :param base_url: base URL to parse pagination data from
        :param pagination_model: model to manage pagination data

        """

        self.headers: dict[str] = settings.headers
        self.base_url: str = base_url
        self.pagination_model: Type[PaginationBaseModel] = pagination_model

    @retry(max_attempts=5, delay=30)
    async def get_icd_data(self, session, url) -> list[str]:
        """
        Method to create list of URLs.

        Depends on number of last page of base url

        :return: List of pagination URLs
        :rtype: list[str]

        """

        async with session.get(url=url, headers=self.headers) as response:
            if response.status == 200:
                response_html = await response.text()
                tree = html.fromstring(response_html)

                # get last index from URL
                last_index: int = int(
                    tree.xpath('//ul[@class="pagination"]/li[@class="PagedList-skipToLast"]/a/@href')
                    [0].split('/')[-1]
                )

                return [f"{url}{i}" for i in range(1, last_index + 1)]
            else:
                raise Exception(f"[{url.split('/')[-2]}] exception")

    async def main(self):
        async with aiohttp.ClientSession() as session:
            return await self.get_icd_data(session=session, url=self.base_url)

    async def manage_data(self) -> None:
        """
        Method to fetch and save URLs to database

        :return: None

        """

        with SessionLocal() as db:
            # fetch pagination URLs
            fetch_data: list[str] = await self.main()

            pagination_service = PaginationService(
                db=db,
                pagination_model=self.pagination_model,
                fetch_data=fetch_data
            )

            pagination_service.run()


def run_data_parsers() -> None:
    """
    Run non-billable and billable parsers

    :return: None

    """

    non_bill_parser = PaginationParser(
        base_url=settings.non_billable_url,
        pagination_model=PaginationNonBillModel
    )

    bill_parser = PaginationParser(
        base_url=settings.billable_url,
        pagination_model=PaginationBillModel
    )

    data_parser = DataParser(
        non_bill_parser=non_bill_parser,
        bill_parser=bill_parser,
        action=None
    )

    data_parser.run_data_parsers()
