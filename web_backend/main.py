from fastapi import FastAPI
from routers import users, ddis, dsas
from fastapi.middleware.cors import CORSMiddleware
from utils.exception_handlers import register_exception_handlers

app = FastAPI()

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "",
        "docs": "请访问 /docs 查看API文档",
        "version": "1.0.0"
    }

app.include_router(users.router)
app.include_router(ddis.router)
app.include_router(dsas.router)

