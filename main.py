import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import routes, handlers

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://example.com",
]

# Устанавливаем соответствующие заголовки CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(app="main:app", reload=True)
    