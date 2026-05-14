from fastapi import FastAPI
from app.api.document_routes import router as document_router

app = FastAPI()

app.include_router(document_router)

@app.get("/")
def root():
    return {"message": "Body Donation Portal API"}