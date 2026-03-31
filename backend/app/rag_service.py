import os
from tempfile import NamedTemporaryFile
from supabase.client import Client, create_client, ClientOptions

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings, ChatHuggingFace, HuggingFaceEndpoint
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

from . import config

# Initialize base Supabase Client for uncontrolled routes if needed
supabase_client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def process_and_embed_pdf(file_bytes: bytes, original_file_name: str, user_id: str) -> None:
    """
    Processes an uploaded PDF, uploads it to Supabase Storage, and embeds its content
    into the Supabase Vector Store tied to the specific user.
    """
    print("Starting PDF processing...")
    with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(file_bytes)
        temp_file_path = temp_file.name

    try:
        print("Loading and chunking document...")
        loader = PyPDFLoader(temp_file_path)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = text_splitter.split_documents(docs)
        
        # Inject user_id into the metadata of every chunk for multi-tenant isolation
        for chunk in chunks:
            chunk.metadata["user_id"] = str(user_id)
            
        print(f"Document split into {len(chunks)} chunks and tagged with user_id.")

        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL_NAME,
            model_kwargs={"device": "cpu"}
        )

        # Clear old data and store new embeddings in Supabase Vector Store
        print("Embedding documents securely and linking to user constraint...")
        vectors = embeddings.embed_documents([chunk.page_content for chunk in chunks])
        rows = [
            {
                "content": chunk.page_content,
                "embedding": vector,
                "metadata": chunk.metadata,
                "user_id": str(user_id)  # Explicitly pass the top-level user_id column constraint required for RLS
            }
            for chunk, vector in zip(chunks, vectors)
        ]
        
        # Chunk the rows to limit payload sizes on the network
        for i in range(0, len(rows), 100):
            supabase_client.table(config.VECTOR_TABLE_NAME).insert(rows[i:i+100]).execute()
            
        print("Embeddings stored successfully under secure RLS constraint.")

    finally:
        os.unlink(temp_file_path)


def get_answer_from_rag(question: str, chat_history: list, user_id: str):
    """
    Builds a RAG chain on-demand and gets an answer for a given question, isolated to the user.
    """
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
    # Crucial: Filter the vector space to only include this user's documents
    retriever = vector_store.as_retriever(search_kwargs={"k": 3, "filter": {"user_id": str(user_id)}})

    # 3. Define Prompt Template
    template = """You are a specialized AI financial analyst. Your primary function is to extract, summarize, and present quantitative and qualitative data from the provided financial report context.

    **Instructions:**
    1.  **Analyze the Request:** Understand the user's question and identify the key financial metrics or topics they are asking about.
    2.  **Context is King:** Base your entire answer strictly on the information within the provided "Context" section. Do not use any external knowledge.
    3.  **Prioritize Quantitative Data:** When a question involves financial figures (e.g., revenue, profit, assets), extract the specific numbers and present them clearly.
    4.  **Format for Clarity:** Always use Markdown tables for presenting numerical data, comparisons, or lists. When citing specific figures, use the currency format mentioned in the report (e.g., '$1.25 million').
    5.  **Be Objective:** Do not provide opinions, predictions, or any form of investment advice. Your role is to report the facts as stated in the document.
    6.  **Handle Missing Information:** If the information is not present in the context, you must state: "The provided context does not contain specific information on this topic." Do not speculate.

    **Context:**
    {context}

    **Chat History:**
    {chat_history}

    **Question:**
    {question}

    **Answer:**
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
