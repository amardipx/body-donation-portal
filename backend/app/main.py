from fastapi import FastAPI
from app.db.database import Base, engine
from app.api.document_routes import router as document_router
from app.api.rag_routes import router as rag_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(rag_router)
app.include_router(document_router)

@app.get("/")
def root():
    return {"message": "Body Donation Portal API"}