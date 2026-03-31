# # app/main.py
# from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
# from fastapi.middleware.cors import CORSMiddleware
# # from gotrue import User

# from . import rag_service
# from . import schemas
# from .security import get_current_user, oauth2_scheme

# app = FastAPI(
#     title="Financial Reports RAG API",
#     description="An API for processing financial reports and answering questions about them.",
# )


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.post("/upload/", response_model=schemas.UploadResponse)
# async def upload_pdf(file: UploadFile = File(...), current_user: dict = Depends(get_current_user), token: str = Depends(oauth2_scheme)):
#     """
#     Endpoint to upload a PDF. The file is processed and its content is
#     embedded and stored in a Supabase vector store.
#     """
#     if not file.filename.endswith(".pdf"):
#         raise HTTPException(status_code=400, detail="Invalid file type. Only PDFs are allowed.")

#     try:
#         file_bytes = await file.read()
#         rag_service.process_and_embed_pdf(file_bytes, file.filename, current_user.id, token)
#         return schemas.UploadResponse(
#             message="File processed and embeddings stored successfully.",
#             file_name=file.filename
#         )
#     except Exception as e:
#         print(f"Error during PDF upload and processing: {e}")
#         raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


# @app.post("/chat/", response_model=schemas.ChatResponse)
# async def chat_with_document(request: schemas.ChatRequest, current_user: dict = Depends(get_current_user), token: str = Depends(oauth2_scheme)):
#     """
#     Endpoint to handle chat requests. It uses the existing vector store
#     to answer questions based on the uploaded document.
#     """
#     try:
#         answer = rag_service.get_answer_from_rag(request.question, request.chat_history, current_user.id, token)
#         return schemas.ChatResponse(answer=answer)
#     except Exception as e:
#         print(f"Error during chat processing: {e}")
#         raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

from fastapi import FastAPI
from . import schemas
from . import rag_service
from .security import get_current_user, oauth2_scheme

app = FastAPI()

@app.get("/")
def health():
    return {"status": "ok"}