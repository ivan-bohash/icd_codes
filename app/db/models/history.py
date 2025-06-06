from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.db.init_db import Base
from app.db.models.abstract import MainMixin


class HistoryBaseModel(Base, MainMixin):
    """
    Base model for Billable and Non-billable code history

    """

    __abstract__ = True

    icd_code: Column[String] = Column(String, index=True, nullable=False)
    history: Column = Column(JSONB)

    def __repr__(self):
        return self._repr(
            id=self.id,
            icd_code=self.icd_code,
            history=self.history,
            created_at=self.created_at,
            updated_at=self.updated_at,
            url_id=self.url_id,
        )

    def __init__(self, icd_code, history, url_id):
        self.icd_code = icd_code
        self.history = history
        self.url_id = url_id


class HistoryBillModel(HistoryBaseModel):
    """
    Billable code history model

    """

    __tablename__ = "history_billable"

    url = relationship("UrlsBillModel", back_populates="history")
    url_id = Column(Integer, ForeignKey("urls_billable.id"), unique=True, nullable=False)


class HistoryNonBillModel(HistoryBaseModel):
    """
    Non-Billable code history model

    """

    __tablename__ = "history_non_billable"

    url = relationship("UrlsNonBillModel", back_populates="history")
    url_id = Column(Integer, ForeignKey("urls_non_billable.id"), unique=True, nullable=False)
