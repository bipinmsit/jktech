from fastapi import FastAPI
import routers.endpoints as process_pdf
import routers.auth as auth
from fastapi.middleware.cors import CORSMiddleware

from datetime import datetime, timedelta
from utils.config.logger import logger

# from utils.config import env


origins = [
    "http://localhost",
    "http://localhost:4200",
    "http://localhost:5432",
]

app = FastAPI(debug=True)


# Add CORS Policy middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# run()

# For OCR & Extraction
app.include_router(process_pdf.router)

# User Login
app.include_router(auth.router)
