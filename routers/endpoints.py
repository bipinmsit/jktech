from pydantic import BaseModel
from sqlalchemy import select
from typing import List
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
from sqlalchemy.sql import text, func
from utils.config.openai import generate_answer_with_llm
from openai.error import RateLimitError
from routers.auth import get_current_user
from langchain.text_splitter import RecursiveCharacterTextSplitter

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/")
def read_root():
    return {"message": "Welcome to FastAPI"}


# Load embedding model
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")


def chunk_text(text: str) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_text(text)


def generate_embedding(text: str) -> list:
    tokens = tokenizer(
        text, return_tensors="pt", padding=True, truncation=True, max_length=512
    )

    with torch.no_grad():
        outputs = model(**tokens)

    # Proper mean pooling with attention mask
    attention_mask = tokens["attention_mask"]
    embeddings = outputs.last_hidden_state * attention_mask.unsqueeze(-1)
    sum_embeddings = embeddings.sum(dim=1)
    sum_mask = attention_mask.sum(dim=1).unsqueeze(-1)

    # Final embedding calculation
    embedding = (sum_embeddings / sum_mask).squeeze()

    # Verify dimension (all-MiniLM-L6-v2 should output 384 dimensions)
    print(f"Embedding dimension: {len(embedding)}")  # Should print 384

    return embedding.tolist()  # Keep this conversion


@router.post("/ingest/")
async def ingest_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    # current_user: dict = Depends(get_current_user),
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

    doc = Document(name=file.filename, content=text, embedding=embedding)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return {"id": doc.id, "content": doc.content}


@router.post("/query/")
async def query_document(
    query: str,
    db: AsyncSession = Depends(get_db),
    # current_user: dict = Depends(get_current_user),
):
    try:
        # Generate query embedding
        query_embedding = generate_embedding(query)

        # Build proper vector query
        stmt = (
            select(Document)
            .order_by(func.l2_distance(Document.embedding, query_embedding))
            .limit(3)
        )

        result = await db.execute(stmt)
        docs = result.scalars().all()

        if not docs:
            raise HTTPException(status_code=404, detail="No documents found")

        # Generate context from matching documents
        context = "\n".join([doc.content for doc in docs])

        # Get LLM answer
        answer = generate_answer_with_llm(context=context, question=query)
        return {"answer": answer}

    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(status_code=500, detail="Query failed")


@router.get("/documents/")
def list_documents(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    result = db.execute(select(Document))
    documents = result.scalars().all()
    return [
        {"id": doc.id, "name": doc.name, "content": doc.content} for doc in documents
    ]
