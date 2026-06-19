from fastapi import FastAPI
from app.api.document_routes import router as document_router
from app.api.rag_routes import router as rag_router
from app.api.auth_routes import router as auth_router
from app.api.consent_routes import router as consent_router


app = FastAPI()


app.include_router(document_router)
app.include_router(rag_router)
app.include_router(auth_router)
app.include_router(consent_router)


@app.get("/")
def root():
    return {"message": "Body Donation Portal API"}