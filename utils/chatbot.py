import streamlit as st
from PyPDF2 import PdfReader
import os
from dotenv import load_dotenv
load_dotenv()
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from datetime import datetime

def configure_genai(api_key):
    """Configure the GenerativeAI API with the provided key."""
    genai.configure(api_key=api_key)

# Document Processing Functions
def get_pdf_text(pdf_docs):
    """Extract text from uploaded PDF files"""
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

        if not text.strip():
            st.warning("No readable text found. Try OCR-based PDF.")
    return text

def get_text_chunks(text):
    """Split text into manageable chunks"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks, api_key):
    """Create vector store from text chunks"""
    embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")
    st.session_state.vector_store_ready = True
    return vector_store

def get_conversational_chain(api_key):
    """Create QA chain for document questions"""
    prompt_template = """
    Answer the question as detailed as possible from the provided context.
    If the answer isn't in the context, say "I couldn't find this in your documents. 
    Here's a general legal answer:"
    
    Context:\n{context}\n
    Question: \n{question}\n

    Answer:
    """
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,
        google_api_key=api_key
    )
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )
    return load_qa_chain(model, chain_type="stuff", prompt=prompt)

# Answering Functions
def answer_from_documents(question, api_key):
    """Answer using uploaded documents"""
    try:
        embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
)
        db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs = db.similarity_search(question)
        
        if docs:
            chain = get_conversational_chain(api_key)
            response = chain(
                {"input_documents": docs, "question": question},
                return_only_outputs=True
            )
            return response["output_text"]
    except Exception as e:
        st.error(f"Document search error: {str(e)}")
    return None

def answer_general_question(question, api_key):
    """Answer general questions"""
    try:
        model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3,
            google_api_key=api_key
        )
        prompt = f"""
        You are an intelligent assistant. Provide a detailed answer to the following question:
        "{question}"
        
        Format your answer with clear headings and bullet points when appropriate.
        """
        return model.invoke(prompt).content
    except Exception as e:
        return f"Failed to answer: {str(e)}"

# Main Chat Interface
def render_chatbot_page():
    """Main chatbot interface"""
    # Initialize session state
    if 'api_key' not in st.session_state:
        st.session_state.api_key = None
    if 'vector_store_ready' not in st.session_state:
        st.session_state.vector_store_ready = False
    if 'history' not in st.session_state:
        st.session_state.history = []

    st.title("VERA ⚖️")
    st.markdown("Ask me any question about your uploaded documents or any general law questions")

    # Set your API key directly (not recommended for public repos)
    API_KEY = os.getenv("GOOGLE_API_KEY")
    st.session_state.api_key = API_KEY
    configure_genai(API_KEY)

    # Document Processing
    with st.expander("Upload Documents"):
        pdf_docs = st.file_uploader(
            "Upload PDFs for document analysis",
            accept_multiple_files=True
        )
        if st.button("Process Documents") and pdf_docs:
            with st.spinner("Processing..."):
                raw_text = get_pdf_text(pdf_docs)
                chunks = get_text_chunks(raw_text)
                get_vector_store(chunks, st.session_state.api_key)
                st.success("Your Document is ready for questioning!")

    # Conversation History
    with st.expander("Conversation History"):
        if st.button("Clear Chat History 🧹"):
            st.session_state.history = []
            st.success("Chat history cleared successfully!")
        
        for entry in st.session_state.history:
            role = "User" if entry["role"] == "user" else "Assistant"
            timestamp = entry["timestamp"].strftime("%H:%M:%S")
            st.markdown(f"**{role}** ({timestamp}):")
            st.write(entry["content"])
            st.markdown("---")

    # Question Answering
    question = st.text_input("Ask me any Legal Question!")
    if question and st.session_state.api_key:
        st.session_state.history.append({
            "role": "user",
            "content": question,
            "timestamp": datetime.now()
        })
        
        response = None
        doc_answer = None
        
        if st.session_state.vector_store_ready:
            with st.spinner("Checking documents..."):
                doc_answer = answer_from_documents(question, st.session_state.api_key)
        
        if doc_answer:
            if "general legal answer" in doc_answer.lower():
                with st.spinner("Researching general law..."):
                    general_answer = answer_general_question(question, st.session_state.api_key)
                    response = f"{doc_answer}\n\n{general_answer}"
            else:
                response = doc_answer
        else:
            with st.spinner("Researching general law..."):
                response = answer_general_question(question, st.session_state.api_key)
        
        if response:
            st.subheader("Answer")
            st.write(response)
            st.session_state.history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now()
            })
