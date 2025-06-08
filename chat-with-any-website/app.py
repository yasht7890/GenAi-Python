import streamlit as st
from langchain_core.messages import AIMessage,HumanMessage
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings,ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain.chains import create_history_aware_retriever
import os
from dotenv import load_dotenv



load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
pinecone_key = os.getenv("PINECONE_API_KEY")


def get_response(user_input):
    return "I dont know"

def get_vectorstore_from_url(url):
    loader = WebBaseLoader(url)
    document = loader.load()

    #chunking
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,
    chunk_overlap=400)
    document_chunks = text_splitter.split_documents(document)

    #make vectore store
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large"
    )
    index_name = "website-chatbot"

    vectorstore = PineconeVectorStore.from_documents(document_chunks,embeddings,index_name=index_name)


    return vectorstore

def get_context_retriever_chain(vector_store):
    llm = ChatOpenAI()
    
    retriever = vector_store.as_retriever()
    
    prompt = ChatPromptTemplate.from_messages([
      MessagesPlaceholder(variable_name="chat_history"),
      ("user", "{input}"),
      ("user", "Given the above conversation, generate a search query to look up in order to get information relevant to the conversation")
    ])
    
    retriever_chain = create_history_aware_retriever(llm, retriever, prompt)
    
    return retriever_chain
    

st.set_page_config(page_title="Chat with websites", page_icon="🤖")
st.title("Chat with websites")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="Hello jii, How may I help you??")
    ]


# sidebar
with st.sidebar:
    st.header("Settings")
    website_url = st.text_input("Website URL")

if website_url is None or website_url == "":
    st.info("Please Enter A Valid URL")

else:
    vectorstore = get_vectorstore_from_url(website_url)

    retriverchain = get_context_retriever_chain(vectorstore)
    
    #user input
    user_query = st.chat_input("Type your message here....")
    if user_query is not None and user_query != "":
        response = get_response(user_query)
        st.session_state.chat_history.append(HumanMessage(content=user_query))
        st.session_state.chat_history.append(AIMessage(content=response))
        
        retrived_documents = retriverchain.invoke({
            "chat_history":st.session_state.chat_history,
            "input":user_query
        })
        st.write(retrived_documents)
            
    for message in st.session_state.chat_history:
        if isinstance(message,AIMessage):
            with st.chat_message("AI"):
                st.write(message.content)
        elif isinstance(message,HumanMessage):
            with st.chat_message("Human"):
                st.write(message.content)
