import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
pinecone_key = os.getenv("PINECONE_API_KEY")

def get_vectorstore_from_url(url):
    """Create vector store from website URL"""
    try:
        # Load documents from URL
        loader = WebBaseLoader(url)
        document = loader.load()

        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        document_chunks = text_splitter.split_documents(document)

        # Create embeddings (using ada-002 for 1536 dimensions to match existing index)
        embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            api_key=openai_key
        )
        
        # Use your existing index
        index_name = "website-chatbot"  # Your existing index
        
        try:
            vectorstore = PineconeVectorStore.from_documents(
                document_chunks, 
                embeddings, 
                index_name=index_name
            )
        except Exception as idx_error:
            st.error(f"Index error: {str(idx_error)}")
            st.error("Please check your Pinecone index configuration")
            return None

        return vectorstore
    except Exception as e:
        st.error(f"Error creating vector store: {str(e)}")
        return None

def get_context_retriever_chain(vector_store):
    """Create context-aware retriever chain"""
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
        api_key=openai_key
    )
    
    retriever = vector_store.as_retriever(
        search_kwargs={"k": 3}
    )
    
    prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        ("user", "Given the above conversation, generate a search query to look up information relevant to the conversation")
    ])
    
    retriever_chain = create_history_aware_retriever(llm, retriever, prompt)
    return retriever_chain

def get_conversational_rag_chain(retriever_chain):
    """Create conversational RAG chain"""
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
        api_key=openai_key
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Answer the user's questions based on the below context. 
        If you don't know the answer based on the context, just say that you don't know.
        Don't make up an answer.
        
        Context: {context}"""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
    ])
    
    stuff_documents_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever_chain, stuff_documents_chain)

def get_response(user_input, retriever_chain, chat_history):
    """Get response from the conversational RAG chain"""
    try:
        conversation_rag_chain = get_conversational_rag_chain(retriever_chain)
        
        response = conversation_rag_chain.invoke({
            "chat_history": chat_history,
            "input": user_input
        })
        
        return response['answer']
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return "I'm sorry, I encountered an error while processing your question."

# Streamlit UI
st.set_page_config(page_title="Chat with Websites", page_icon="🤖")
st.title("🤖 Chat with Websites")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="Hello! I'm ready to help you chat with any website. Please enter a website URL in the sidebar to get started.")
    ]

if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

if "retriever_chain" not in st.session_state:
    st.session_state.retriever_chain = None

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    website_url = st.text_input("Website URL", placeholder="https://example.com")
    
    if st.button("Process Website", type="primary"):
        if website_url and website_url.strip():
            with st.spinner("Processing website... This may take a moment."):
                # Create vector store
                vectorstore = get_vectorstore_from_url(website_url)
                if vectorstore:
                    st.session_state.vectorstore = vectorstore
                    st.session_state.retriever_chain = get_context_retriever_chain(vectorstore)
                    st.success("Website processed successfully!")
        else:
            st.error("Please enter a valid URL")

# Main chat interface
if st.session_state.vectorstore is None:
    st.info("👆 Please enter a website URL in the sidebar and click 'Process Website' to start chatting!")
else:
    # Chat input
    user_query = st.chat_input("Type your message here...")
    
    if user_query is not None and user_query.strip() != "":
        # Get response
        response = get_response(
            user_query, 
            st.session_state.retriever_chain, 
            st.session_state.chat_history
        )
        
        # Update chat history
        st.session_state.chat_history.append(HumanMessage(content=user_query))
        st.session_state.chat_history.append(AIMessage(content=response))

# Display chat history
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.write(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.write(message.content)

# Optional: Display debug information
if st.session_state.vectorstore is not None:
    with st.sidebar:
        st.write("---")
        if st.checkbox("Show Debug Info"):
            st.write("✅ Vector store loaded")
            st.write("✅ Retriever chain initialized")
            st.write(f"📊 Chat history length: {len(st.session_state.chat_history)}")