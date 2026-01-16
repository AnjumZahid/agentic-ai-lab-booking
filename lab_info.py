import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain.embeddings.base import Embeddings
import numpy as np

# ==============================
# Fake Embeddings for local testing
# ==============================
class FakeEmbeddings(Embeddings):
    """Fake embeddings for local RAG testing."""
    
    def embed_documents(self, texts):
        # Generate a random vector for each document
        return [np.random.rand(1536).tolist() for _ in texts]

    def embed_query(self, text):
        # Generate a random vector for the query
        return np.random.rand(1536).tolist()

# ==============================
# Load environment variables
# ==============================
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ==============================
# Models
# ==============================
LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

# Use FakeEmbeddings for local testing
EMBEDDINGS = FakeEmbeddings()
# For real embeddings, uncomment the line below
# EMBEDDINGS = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# ==============================
# In-Memory Vector Store
# ==============================
VECTOR_STORE = InMemoryVectorStore(embedding=EMBEDDINGS)

# ==============================
# Prompt
# ==============================
PROMPT_TEMPLATE = """
You are a precise assistant.
Answer strictly from the provided context.
If the answer is not found, say "I don't know".

Question:
{question}

Context:
{context}

Answer:
"""

PROMPT = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

# ==============================
# Functions
# ==============================
def load_and_index_pdf(pdf_path: str):
    print("Loading PDF...")
    loader = PDFPlumberLoader(pdf_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(documents)
    VECTOR_STORE.add_documents(chunks)

    print(f"Indexed {len(chunks)} chunks into memory.")


# def ask_question(question: str):
#     docs = VECTOR_STORE.similarity_search(question, k=2)

#     # Print retrieved chunks for debugging
#     print("\n--- Retrieved Chunks ---")
#     for i, doc in enumerate(docs, start=1):
#         print(f"Chunk {i}:")
#         print(doc.page_content)
#         print("-----------------------")

#     context = "\n\n".join(doc.page_content for doc in docs)

#     chain = PROMPT | LLM
#     response = chain.invoke({
#         "question": question,
#         "context": context
#     })

#     return response.content

def ask_question(question: str):
    """
    Retrieve relevant document chunks for a query.
    No LLM call. No prints.
    """
    docs = VECTOR_STORE.similarity_search(question, k=2)

    return [doc.page_content for doc in docs]


# ==============================
# PDF Loading - moved outside __main__
# ==============================
pdf_path = "lab_info.pdf"  # directly use the PDF
load_and_index_pdf(pdf_path)

# ==============================
# CLI Interface
# ==============================
if __name__ == "__main__":
    print("\nAsk questions (type 'exit' to quit)\n")

    while True:
        query = input("You: ").strip()
        if query.lower() == "exit":
            break

        answer = ask_question(query)
        print("\nBot:", answer)
        print("-" * 50)





# import os
# from dotenv import load_dotenv
# from langchain_google_genai import (
#     ChatGoogleGenerativeAI,
#     GoogleGenerativeAIEmbeddings
# )
# from langchain_community.document_loaders import PDFPlumberLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_core.vectorstores import InMemoryVectorStore
# from langchain_core.prompts import ChatPromptTemplate
# from langchain.embeddings import Embeddings
# import numpy as np

# class FakeEmbeddings:
#     """Generate random embeddings for local RAG testing."""
    
#     def embed_documents(self, texts):
#         # Return a list of random vectors (length 1536 per document)
#         return [np.random.rand(1536).tolist() for _ in texts]

#     def embed_query(self, text):
#         # Return a single random vector
#         return np.random.rand(1536).tolist()



# class FakeEmbeddings(Embeddings):
#     """Fake embeddings for local RAG testing"""
    
#     def embed_documents(self, texts):
#         # Generate a random vector for each document
#         return [np.random.rand(1536).tolist() for _ in texts]

#     def embed_query(self, text):
#         # Generate a random vector for the query
#         return np.random.rand(1536).tolist()

# # ==============================
# # Load environment variables
# # ==============================
# load_dotenv()

# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# # ==============================
# # Models
# # ==============================
# LLM = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     temperature=0
# )

# EMBEDDINGS = FakeEmbeddings()
# # EMBEDDINGS = GoogleGenerativeAIEmbeddings(
# #     model="models/embedding-001"
# # )

# # ==============================
# # In-Memory Vector Store
# # ==============================
# VECTOR_STORE = InMemoryVectorStore(embedding=EMBEDDINGS)

# # ==============================
# # Prompt
# # ==============================
# PROMPT_TEMPLATE = """
# You are a precise assistant.
# Answer strictly from the provided context.
# If the answer is not found, say "I don't know".

# Question:
# {question}

# Context:
# {context}

# Answer:
# """

# PROMPT = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

# # ==============================
# # Functions
# # ==============================
# def load_and_index_pdf(pdf_path: str):
#     print("Loading PDF...")
#     loader = PDFPlumberLoader(pdf_path)
#     documents = loader.load()

#     splitter = RecursiveCharacterTextSplitter(
#         chunk_size=500,
#         chunk_overlap=100
#     )

#     chunks = splitter.split_documents(documents)
#     VECTOR_STORE.add_documents(chunks)

#     print(f"Indexed {len(chunks)} chunks into memory.")


# def ask_question(question: str):
#     docs = VECTOR_STORE.similarity_search(question, k=4)

#     context = "\n\n".join(doc.page_content for doc in docs)

#     chain = PROMPT | LLM
#     response = chain.invoke({
#         "question": question,
#         "context": context
#     })

#     return response.content


# # ==============================
# # CLI Interface
# # ==============================
# if __name__ == "__main__":
#     pdf_path = "lab_info.pdf"  # directly use the PDF
#     load_and_index_pdf(pdf_path)

#     print("\nAsk questions (type 'exit' to quit)\n")

#     while True:
#         query = input("You: ").strip()
#         if query.lower() == "exit":
#             break

#         answer = ask_question(query)
#         print("\nBot:", answer)
#         print("-" * 50)

