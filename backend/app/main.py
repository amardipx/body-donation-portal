from fastapi import FastAPI
from app.api.document_routes import router as document_router
from app.api.rag_routes import router as rag_router
from app.api.auth_routes import router as auth_router
from app.api.donor_routes import router as donor_router
from app.api.family_routes import router as family_router
from app.api.admin_routes import router as admin_router
from app.api.institution_routes import router as institution_router


app = FastAPI()



app.include_router(auth_router)
app.include_router(donor_router)
app.include_router(family_router)
app.include_router(admin_router)
app.include_router(institution_router)
app.include_router(document_router)
app.include_router(rag_router)

@app.get("/")
def root():
    return {"message": "Body Donation Portal API"}