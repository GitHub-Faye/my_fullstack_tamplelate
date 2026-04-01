from fastapi import FastAPI

from dotenv import load_dotenv

from app.api import router as api_router

load_dotenv()


app = FastAPI()

app.include_router(api_router)

