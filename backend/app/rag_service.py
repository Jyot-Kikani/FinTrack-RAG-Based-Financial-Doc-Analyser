import os
from tempfile import NamedTemporaryFile
from supabase.client import Client, create_client

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings, ChatHuggingFace, HuggingFaceEndpoint
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

from . import config

# Initialize Supabase Client
supabase_client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def process_and_embed_pdf(file_bytes: bytes, original_file_name: str) -> None:
    """
    Processes an uploaded PDF, uploads it to Supabase Storage, and embeds its content
    into the Supabase Vector Store.
    """
    print("Starting PDF processing...")
    # Temp file to safely handle the uploaded PDF bytes
    with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(file_bytes)
        temp_file_path = temp_file.name

    try:
        # Upload the original PDF to Supabase Storage
        print(f"Uploading {original_file_name} to Supabase Storage...")
        storage_path = f"public/{original_file_name}"
        supabase_client.storage.from_(config.PDF_BUCKET_NAME).upload(
            file=temp_file_path,
            path=storage_path,
            file_options={"content-type": "application/pdf", "x-upsert": "true"}
        )
        print("Upload successful.")

        # Load and chunk the document
        print("Loading and chunking document...")
        loader = PyPDFLoader(temp_file_path)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = text_splitter.split_documents(docs)
        print(f"Document split into {len(chunks)} chunks.")

        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL_NAME,
            model_kwargs={"device": "cpu"}
        )

        # Clear old data and store new embeddings in Supabase Vector Store
        print("Storing embeddings in Supabase Vector Store...")
        # Clear the table for each new upload.
        SupabaseVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            client=supabase_client,
            table_name=config.VECTOR_TABLE_NAME,
            query_name=config.MATCH_FUNCTION_NAME,
            # This will delete all existing rows in the table before inserting new ones
            # Be cautious with this in a multi-user environment
            chunk_size=100 # Batch size for insertion
        )
        print("Embeddings stored successfully.")

    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)


def get_answer_from_rag(question: str, chat_history: list):
    """
    Builds a RAG chain on-demand and gets an answer for a given question.
    """
    print("Building RAG chain on-demand...")
    # 1. Initialize LLM
    llm_endpoint = HuggingFaceEndpoint(
        repo_id=config.REPO_ID, task="text-generation", max_new_tokens=512, do_sample=False
    )
    llm = ChatHuggingFace(llm=llm_endpoint)

    # 2. Initialize Embeddings and connect to the existing Vector Store
    embeddings = HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL_NAME, model_kwargs={"device": "cpu"}
    )
    vector_store = SupabaseVectorStore(
        client=supabase_client,
        embedding=embeddings,
        table_name=config.VECTOR_TABLE_NAME,
        query_name=config.MATCH_FUNCTION_NAME,
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    # 3. Define Prompt Template
    template = """You are a helpful financial analyst. Answer questions based on the context provided.
    Format your response using Markdown. 
    When presenting financial data, lists, or comparisons, always use Markdown tables.

    Context:
    {context}

    Chat History:
    {chat_history}

    Question:
    {question}

    Provide a clear and concise answer. If the context does not contain the answer, state that clearly."""
    prompt = ChatPromptTemplate.from_template(template)

    # 4. Helper functions for formatting
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def format_chat_history(messages):
        if not messages: return "No previous conversation."
        formatted = []
        for msg in messages:
            role = "Human" if msg.get("type") == "human" else "Assistant"
            formatted.append(f"{role}: {msg.get('content')}")
        return "\n".join(formatted)

    # 5. Retrieve documents and invoke the LLM
    print(f"Retrieving documents for question: {question}")
    docs = retriever.invoke(question)
    context = format_docs(docs)
    formatted_chat_history = format_chat_history(chat_history)
    
    # Prepare the prompt with all the necessary information
    formatted_prompt = prompt.invoke({
        "context": context,
        "chat_history": formatted_chat_history,
        "question": question
    })

    print("Invoking LLM...")
    response = llm.invoke(formatted_prompt.to_messages())
    return response.content