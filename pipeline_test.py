import os
from dotenv import load_dotenv

# --- All imports are now correct and using the latest packages ---
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

# --- 1. Load Environment Variables ---
load_dotenv()
print("✅ Environment variables loaded.")

# --- 2. Configuration ---
PDF_PATH = "report.pdf"
VECTOR_STORE_PATH = "./vector_store"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
REPO_ID = "HuggingFaceH4/zephyr-7b-beta"
print("✅ Configuration set.")

# --- 3. Load & Process Document ---
print("\nStep 3: Loading and processing the PDF...")
loader = PyPDFLoader(PDF_PATH)
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
chunks = text_splitter.split_documents(docs)
print(f"Successfully split the document into {len(chunks)} chunks.")

# --- 4. Create Embeddings and Vector Store ---
print("\nStep 4: Creating embeddings and vector store...")
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL_NAME,
    model_kwargs={"device": "cpu"}
)

if not os.path.exists(VECTOR_STORE_PATH):
    print("Creating a new vector store...")
    db = Chroma.from_documents(chunks, embeddings, persist_directory=VECTOR_STORE_PATH)
    print("Vector store created successfully.")
else:
    print("Loading existing vector store.")
    db = Chroma(persist_directory=VECTOR_STORE_PATH, embedding_function=embeddings)

retriever = db.as_retriever(search_kwargs={"k": 3})
print("✅ Vector store and retriever are ready.")

# --- 5. Initialize the LLM ---
print("\nStep 5: Initializing the LLM...")
# Using HuggingFaceEndpoint with ChatHuggingFace for cloud-based inference
llm_endpoint = HuggingFaceEndpoint(
    repo_id="meta-llama/Llama-3.1-8B-Instruct",
    task="text-generation",
    max_new_tokens=512,
    do_sample=False,
    repetition_penalty=1.03,
    provider="auto",  # HuggingFace chooses the best provider
)

# Wrap it in ChatHuggingFace for chat interface
llm = ChatHuggingFace(llm=llm_endpoint)
print("✅ LLM initialized successfully (using HuggingFace cloud API).")

# --- 6. Create the RAG Chain ---
print("\nStep 6: Creating the Conversational RAG chain...")

# Define the prompt template
template = """You are a helpful assistant that answers questions based on the following context.

Context:
{context}

Chat History:
{chat_history}

Question: {question}

Provide a clear and concise answer based on the context provided. If the context doesn't contain enough information, say so."""

prompt = ChatPromptTemplate.from_template(template)

def format_docs(docs):
    """Format retrieved documents into a single string"""
    return "\n\n".join([f"Document {i+1}:\n{doc.page_content}" for i, doc in enumerate(docs)])

def format_chat_history(messages):
    """Format chat history for the prompt"""
    if not messages:
        return "No previous conversation."
    formatted = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            formatted.append(f"Human: {msg.content}")
        elif isinstance(msg, AIMessage):
            formatted.append(f"Assistant: {msg.content}")
    return "\n".join(formatted)

# Create the RAG chain
def create_rag_chain(retriever, llm, prompt):
    def retrieve_and_answer(input_dict):
        # Retrieve documents
        question = input_dict["question"]
        docs = retriever.invoke(question)
        
        # Format context and chat history
        context = format_docs(docs)
        chat_history = format_chat_history(input_dict.get("chat_history", []))
        
        # Create the full prompt
        formatted_prompt = prompt.invoke({
            "context": context,
            "chat_history": chat_history,
            "question": question
        })
        
        # Get response from LLM 
        # For ChatModel, we send a list of messages
        messages = formatted_prompt.messages if hasattr(formatted_prompt, 'messages') else [HumanMessage(content=str(formatted_prompt))]
        response = llm.invoke(messages)
        return response.content
    
    return retrieve_and_answer

rag_chain = create_rag_chain(retriever, llm, prompt)

print("✅ RAG chain created successfully.")

# --- 7. Start the Conversation ---
print("\nStep 7: Starting conversation...")

# We need to manage the chat history manually
chat_history = []

# First question
question = "what is the overall cgpa?"
print(f"\nHuman: {question}")

input_dict = {
    "question": question,
    "chat_history": chat_history
}
answer = rag_chain(input_dict)
print(f"AI: {answer}")

# Add the first interaction to the history
chat_history.extend([HumanMessage(content=question), AIMessage(content=answer)])

# Follow-up question
question_follow_up = "what are the weak subjects?"
print(f"\nHuman: {question_follow_up}")

# Include chat history for conversational context
input_dict_follow_up = {
    "question": question_follow_up,
    "chat_history": chat_history
}
answer_follow_up = rag_chain(input_dict_follow_up)
print(f"AI: {answer_follow_up}")