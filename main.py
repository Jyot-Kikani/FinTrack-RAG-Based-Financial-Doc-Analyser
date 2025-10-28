import os
import shutil
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# --- All our LangChain imports ---
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings, ChatHuggingFace, HuggingFaceEndpoint
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

# --- Configuration and Initialization ---
load_dotenv()

print("✅ Environment variables loaded.")
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
REPO_ID = "meta-llama/Llama-3.1-8B-Instruct"
VECTOR_STORE_PATH = "./vector_store"
PDF_STORAGE_PATH = "uploaded_report.pdf"

# Initialize a global variable for the RAG chain
# This is crucial so we don't rebuild it on every request
rag_chain = None

# --- FastAPI App Definition ---
app = FastAPI(
    title="Financial Reports RAG API",
    description="An API for processing financial PDFs and chatting with them.",
)

# --- Helper Functions (from your script) ---
def format_docs(docs):
    return "\n\n".join([f"Document {i+1}:\n{doc.page_content}" for i, doc in enumerate(docs)])

def format_chat_history(messages):
    if not messages: return "No previous conversation."
    formatted = []
    for msg in messages:
        if isinstance(msg, dict): # Handle dict representation from frontend
            role = "Human" if msg.get("type") == "human" else "Assistant"
            formatted.append(f"{role}: {msg.get('content')}")
        elif isinstance(msg, HumanMessage): formatted.append(f"Human: {msg.content}")
        elif isinstance(msg, AIMessage): formatted.append(f"Assistant: {msg.content}")
    return "\n".join(formatted)

# --- Core RAG Chain Creation ---
def build_rag_chain():
    # 1. Initialize LLM
    llm_endpoint = HuggingFaceEndpoint(
        repo_id=REPO_ID, task="text-generation", max_new_tokens=512, do_sample=False
    )
    llm = ChatHuggingFace(llm=llm_endpoint)
    
    # 2. Initialize Embeddings and Retriever from the existing vector store
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME, model_kwargs={"device": "cpu"})
    db = Chroma(persist_directory=VECTOR_STORE_PATH, embedding_function=embeddings)
    retriever = db.as_retriever(search_kwargs={"k": 3})

    # 3. Define Prompt
    template = """You are a helpful assistant that answers questions based on the following context.
    Context: {context}
    Chat History: {chat_history}
    Question: {question}
    Provide a clear and concise answer. If the context doesn't contain the answer, say so."""
    prompt = ChatPromptTemplate.from_template(template)

    # 4. Define the RAG logic
    def retrieve_and_answer(input_dict):
        question = input_dict["question"]
        docs = retriever.invoke(question)
        context = format_docs(docs)
        chat_history = format_chat_history(input_dict.get("chat_history", []))
        
        formatted_prompt = prompt.invoke({
            "context": context, "chat_history": chat_history, "question": question
        })
        response = llm.invoke(formatted_prompt.to_messages())
        return response.content

    return retrieve_and_answer

# --- API Endpoints ---
@app.post("/upload/")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Uploads a PDF, processes it, and creates a vector store.
    """
    global rag_chain
    rag_chain = None
    try:
        # Save the uploaded file
        with open(PDF_STORAGE_PATH, "wb") as f:
            f.write(await file.read())
        
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(PDF_STORAGE_PATH)
        docs = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = text_splitter.split_documents(docs)
        
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME, model_kwargs={"device": "cpu"})
        
        # Create a new vector store from the uploaded document
        if os.path.exists(VECTOR_STORE_PATH):
            shutil.rmtree(VECTOR_STORE_PATH) # Remove old store
            
        Chroma.from_documents(chunks, embeddings, persist_directory=VECTOR_STORE_PATH)
        
        # Now that the vector store is ready, build the chain
        rag_chain = build_rag_chain()
        
        return JSONResponse(content={"message": f"Successfully processed {file.filename}."})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

class ChatRequest(BaseModel):
    question: str
    chat_history: list = []

@app.post("/chat/")
async def chat_with_pdf(request: ChatRequest):
    """
    Handles chat requests by invoking the RAG chain.
    """
    global rag_chain
    if rag_chain is None:
        return JSONResponse(content={"error": "PDF not processed yet. Please upload a file first."}, status_code=400)
    
    try:
        answer = rag_chain(request.dict())
        return JSONResponse(content={"answer": answer})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)