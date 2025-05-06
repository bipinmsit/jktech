from pydantic import BaseModel
from sqlalchemy import select
from utils.config.logger import logger
from fastapi import UploadFile, File, HTTPException, Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
from transformers import AutoTokenizer, AutoModel
import torch
from postgres.database import get_db
from models.models import Document
import fitz
from sqlalchemy.sql import text
from utils.config.openai import generate_answer_with_llm
from openai.error import RateLimitError
from routers.auth import get_current_user

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/")
def read_root():
    return {"message": "Welcome to FastAPI"}


# Load embedding model
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")


def generate_embedding(text: str):
    tokens = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        embedding = model(**tokens).last_hidden_state.mean(dim=1)
    return embedding.squeeze().numpy().tolist()  # Ensure it's a 1D list


@router.post("/ingest/")
async def ingest_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    content = await file.read()

    try:
        # Load PDF from bytes
        pdf_doc = fitz.open(stream=content, filetype="pdf")
        text = ""
        for page in pdf_doc:
            text += page.get_text()

        print("Extracted text:", text)  # Debugging line to check extracted text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {str(e)}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="No extractable text found in PDF.")

    embedding = generate_embedding(text)

    doc = Document(content=text, embedding=embedding)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return {"id": doc.id, "content": doc.content}


@router.post("/query/")
async def query_document(
    query: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query_embedding = generate_embedding(query)
    print("Query embedding shape:", len(query_embedding))  # Debugging
    # print("Query embedding type:", type(query_embedding))  # Debugging
    # print("Query embedding:", query_embedding)  # Debugging

    # Dynamically construct the SQL query with placeholders
    placeholders = ", ".join(
        [f":query_embedding_{i}" for i in range(len(query_embedding))]
    )
    sql = text(
        f"""
        SELECT * FROM documents
        ORDER BY l2_distance(embedding, ARRAY[{placeholders}]::vector) ASC
        LIMIT 1
        """
    )

    # Bind parameters dynamically
    params = {f"query_embedding_{i}": value for i, value in enumerate(query_embedding)}
    result = db.execute(sql, params)
    doc = result.fetchone()
    if not doc:
        raise HTTPException(status_code=404, detail="No relevant document found")

    try:
        # Call LLM to get answer from doc.content
        answer = generate_answer_with_llm(context=doc.content, question=query)
    except RateLimitError as e:
        raise e

    return {"answer": answer}


@router.get("/documents/")
def list_documents(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    result = db.execute(select(Document))
    documents = result.scalars().all()
    return [{"id": doc.id, "content": doc.content} for doc in documents]
