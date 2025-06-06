import uvicorn
from fastapi import FastAPI

from app.db.init_db import engine, Base
from app.api.routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
