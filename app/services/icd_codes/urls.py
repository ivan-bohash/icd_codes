import arrow
from arrow import Arrow
from typing import Type, Callable, Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models.pagination import PaginationBaseModel
from app.db.models.url import UrlsBaseModel
from app.db.models.history import HistoryBaseModel


class UrlsService:
    """
    Service responsible for updating, creating records

    and deleting urls with associated history in the database

    """

    def __init__(
            self,
            db: Session,
            pagination_model: Type[PaginationBaseModel],
            urls_model: Type[UrlsBaseModel] | Any,
            opposite_urls_model: Type[UrlsBaseModel],
            history_model: Type[HistoryBaseModel],
            fetch_method: Callable
    ) -> None:

        """
        :param db: current database session
        :param pagination_model: model that stores pagination links
        :param urls_model: model that stores urls and icd_codes
        :param opposite_urls_model: opposite model to check records
        :param history_model: model that stores ICD code history
        :param fetch_method: async method to fetch data

        """

        self.db: Session = db
        self.pagination_model: Type[PaginationBaseModel] = pagination_model
        self.urls_model: Type[UrlsBaseModel] | Any = urls_model
        self.opposite_urls_model: Type[UrlsBaseModel] = opposite_urls_model
        self.history_model: Type[HistoryBaseModel] = history_model
        self.fetch_method: Callable = fetch_method
        self.updated_at: Arrow = arrow.utcnow()

    async def update_urls(self) -> None:
        """
        Fetches URLs data, update or add new records

        :return: None

        """

        # get all pagination URLs from database
        urls = [icd.url for icd in self.db.query(self.pagination_model.url).all()]

        # fetch URLs data
        fetched_data = await self.fetch_method(urls=urls)

        def add_new() -> None:
            """
            Add new records if they don't exist to the database

            :return: None

            """

            db_icd_codes = set()

            # get icd codes from db
            obj_stream = self.db.execute(
                select(self.urls_model.icd_code).order_by(self.urls_model.id),
                execution_options={"stream_results": True}
            )

            # get icd codes from urls model
            while True:
                obj_partition = obj_stream.scalars().fetchmany(settings.DATA_PARTITION)

                if not obj_partition:
                    break

                db_icd_codes.update(obj_partition)

            new_icd_codes = []

            for data in fetched_data:
                # add if not exist in db
                if data["icd_code"] not in db_icd_codes:
                    icd = self.urls_model(icd_code=data["icd_code"], url=data["url"])
                    new_icd_codes.append(icd)

            if new_icd_codes:
                self.db.add_all(new_icd_codes)
                self.db.commit()
                print(f"{self.urls_model.__name__}: {len(new_icd_codes)} added elements")

        def update() -> None:
            """
            Update field "updated_at" for records that exist in database

            :return: None

            """

            db_urls = {}

            obj_stream = self.db.execute(
                select(self.urls_model).order_by(self.urls_model.id),
                execution_options={"stream_results": True}
            )

            # create dict from urls model
            while True:
                obj_partition = obj_stream.scalars().fetchmany(settings.DATA_PARTITION)

                if not obj_partition:
                    break

                for obj in obj_partition:
                    db_urls[obj.icd_code] = obj.id

            # update only existing records
            data = [
                {"id": db_urls.get(icd["icd_code"]), "updated_at": self.updated_at}
                for icd in fetched_data
            ]

            self.db.bulk_update_mappings(self.urls_model, data)
            self.db.commit()

            print(f"{self.urls_model.__name__}: {len(data)} updated records")

        add_new()
        update()

    def delete_urls(self) -> None:
        """
        Delete outdated ICD from database and remove ICD from history model

        :return: None

        """

        urls_to_delete = (self.db.query(self.urls_model).
                          filter(self.urls_model.updated_at != self.updated_at).
                          filter(self.urls_model.icd_code.in_(self.db.query(self.opposite_urls_model.icd_code))).
                          all())

        if urls_to_delete:
            for url in urls_to_delete:
                self.db.delete(url)

            print(f"{self.urls_model.__name__}, {self.history_model.__name__}: {len(urls_to_delete)} deleted records")

        print(f"{self.urls_model.__name__}, {self.history_model.__name__}: no records to delete")
