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


supabase_client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def process_and_embed_pdf(file_bytes: bytes, original_file_name: str) -> None:

    print("Starting PDF processing...")
    with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(file_bytes)
        temp_file_path = temp_file.name

    try:
        print(f"Uploading {original_file_name} to Supabase Storage...")
        storage_path = f"public/{original_file_name}"
        supabase_client.storage.from_(config.PDF_BUCKET_NAME).upload(
            file=temp_file_path,
            path=storage_path,
            file_options={"content-type": "application/pdf", "x-upsert": "true"}
        )
        print("Upload successful.")

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

        print("Storing embeddings in Supabase Vector Store...")
        SupabaseVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            client=supabase_client,
            table_name=config.VECTOR_TABLE_NAME,
            query_name=config.MATCH_FUNCTION_NAME,
            chunk_size=100 
        )
        print("Embeddings stored successfully.")

    finally:
        os.unlink(temp_file_path)


def get_answer_from_rag(question: str, chat_history: list):

    print("Building RAG chain on-demand...")
    llm_endpoint = HuggingFaceEndpoint(
        repo_id=config.REPO_ID, task="text-generation", max_new_tokens=512, do_sample=False
    )
    llm = ChatHuggingFace(llm=llm_endpoint)

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

    template = """You are an expert financial analyst and research assistant. 
Your task is to provide clear, data-driven, and well-structured answers based strictly on the information provided in the context. 
If the context is insufficient to answer the question, explicitly state that.

--- 
**Guidelines:**
1. Use **Markdown formatting** throughout your response.  
2. When presenting:
   - **Financial data, ratios, or comparisons**, use **Markdown tables**.  
   - **Lists of factors, pros/cons, or steps**, use **bulleted lists**.  
3. Be **concise but analytical** — highlight insights, implications, and reasoning.  
4. If relevant, mention key **financial metrics**, **industry benchmarks**, or **risk factors** based on the context.  
5. Avoid speculation — only use information grounded in the provided context.  
6. Include a short **summary or recommendation** at the end when applicable.  

---
**Inputs:**
- **Context:** {context}  
- **Chat History:** {chat_history}  
- **Question:** {question}  

---
**Output Requirements:**
- Provide a **clear, structured, and actionable** financial analysis or answer.
- If data is missing, respond with: *“The context does not provide enough information to answer this question.”*
"""
    prompt = ChatPromptTemplate.from_template(template)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def format_chat_history(messages):
        if not messages: return "No previous conversation."
        formatted = []
        for msg in messages:
            role = "Human" if msg.get("type") == "human" else "Assistant"
            formatted.append(f"{role}: {msg.get('content')}")
        return "\n".join(formatted)

    print(f"Retrieving documents for question: {question}")
    docs = retriever.invoke(question)
    context = format_docs(docs)
    formatted_chat_history = format_chat_history(chat_history)
    
    
    formatted_prompt = prompt.invoke({
        "context": context,
        "chat_history": formatted_chat_history,
        "question": question
    })

    print("Invoking LLM...")
    response = llm.invoke(formatted_prompt.to_messages())
    return response.content
