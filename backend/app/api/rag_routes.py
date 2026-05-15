from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.rag.qa import answer

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


class QuestionRequest(BaseModel):
    question: str


@router.post("/ask")
def ask_question(request: QuestionRequest):
    try:
        result = answer(question=request.question)
        return {
            "answer": result["answer"],
            "references": result["references"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))