from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
import qdrant_client
import os
from dotenv import load_dotenv
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime
import re
from openai import OpenAI
import tempfile
import time

# Load environment variables
load_dotenv()

# Initialize OpenAI client with timeout
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=60.0  # 60 seconds timeout
)

# Configure Qdrant client with timeout and retry strategy
def create_qdrant_client():
    """Create Qdrant client with proper timeout and retry configuration"""
    try:
        client = qdrant_client.QdrantClient(
            url=os.getenv("QDRANT_HOST"),
            api_key=os.getenv("QDRANT_API_KEY"),
            timeout=120,  # 120 seconds timeout
            prefer_grpc=False  # Use HTTP instead of gRPC for better compatibility
        )
        return client
    except Exception as e:
        st.error(f"Failed to connect to Qdrant: {str(e)}")
        return None

# Function to create a clean collection name
def create_collection_name(filename):
    clean_name = re.sub(r'[^\w\s-]', '', filename.rsplit('.', 1)[0])
    clean_name = re.sub(r'\s+', '_', clean_name.strip())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{clean_name}_{timestamp}"

# Function to process documents in batches
def process_documents_in_batches(documents, embedding_model, collection_name, batch_size=50):
    """Process documents in smaller batches to avoid timeouts"""
    total_docs = len(documents)
    
    # Create the vector store with the first batch
    if total_docs == 0:
        st.error("No documents to process")
        return None
    
    try:
        # Process first batch to create the collection
        first_batch = documents[:min(batch_size, total_docs)]
        
        vector_store = Qdrant.from_documents(
            documents=first_batch,
            embedding=embedding_model,
            url=os.getenv("QDRANT_HOST"),
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name=collection_name,
            timeout=120
        )
        
        st.success(f"✅ Created collection with {len(first_batch)} documents")
        
        # Process remaining batches if any
        if total_docs > batch_size:
            progress_bar = st.progress(0)
            
            for i in range(batch_size, total_docs, batch_size):
                batch = documents[i:i + batch_size]
                
                try:
                    vector_store.add_documents(batch)
                    progress = min((i + batch_size) / total_docs, 1.0)
                    progress_bar.progress(progress)
                    st.write(f"Processed {min(i + batch_size, total_docs)}/{total_docs} documents")
                    
                    # Small delay to prevent overwhelming the server
                    time.sleep(0.5)
                    
                except Exception as batch_error:
                    st.warning(f"Failed to process batch {i//batch_size + 1}: {str(batch_error)}")
                    continue
            
            progress_bar.progress(1.0)
        
        return vector_store
        
    except Exception as e:
        st.error(f"Failed to create vector store: {str(e)}")
        return None

# Function to retry operations with exponential backoff
def retry_operation(func, max_retries=3, delay=1):
    """Retry an operation with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            wait_time = delay * (2 ** attempt)
            st.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

# Streamlit UI
st.set_page_config(page_title="PDF Q&A with Qdrant", page_icon="📄")
st.title("📄 PDF Q&A with Qdrant")
st.markdown("Upload a PDF and ask questions about its content!")

# Add configuration options
with st.sidebar:
    st.header("⚙️ Configuration")
    chunk_size = st.slider("Chunk Size", 500, 2000, 1000, step=100)
    chunk_overlap = st.slider("Chunk Overlap", 50, 400, 200, step=50)
    batch_size = st.slider("Batch Size", 10, 100, 25, step=5)
    st.info("Smaller batch sizes help avoid timeouts but take longer to process.")

# Upload file
pdf = st.file_uploader("Upload your PDF", type="pdf")

if pdf is not None:
    # Check file size
    file_size = len(pdf.read())
    pdf.seek(0)  # Reset file pointer
    file_size_mb = file_size / (1024 * 1024)
    
    st.info(f"📄 File size: {file_size_mb:.2f} MB")
    
    if file_size_mb > 50:
        st.warning("⚠️ Large file detected. Processing may take longer. Consider using smaller batch sizes.")
    
    try:
        # Create collection name
        collection_name = create_collection_name(pdf.name)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(pdf.read())
            tmp_file_path = tmp_file.name

        # Load PDF with timeout handling
        with st.spinner("📖 Loading PDF..."):
            def load_pdf():
                loader = PyPDFLoader(tmp_file_path)
                return loader.load()
            
            docs = retry_operation(load_pdf)
            st.success(f"✅ Loaded {len(docs)} pages")

        # Chunking
        with st.spinner("✂️ Splitting document into chunks..."):
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            split_docs = text_splitter.split_documents(docs)
            st.success(f"✅ Created {len(split_docs)} chunks")

        # Generate embeddings and store in Qdrant
        with st.spinner("🔄 Creating embeddings and storing in Qdrant..."):
            embedding_model = OpenAIEmbeddings(
                model="text-embedding-3-large",
                timeout=60
            )

            # Process documents in batches
            vector_store = process_documents_in_batches(
                split_docs, 
                embedding_model, 
                collection_name, 
                batch_size=batch_size
            )

        # Clean up temporary file
        try:
            os.unlink(tmp_file_path)
        except:
            pass
        
        if vector_store is None:
            st.error("❌ Failed to create vector store. Please try again with smaller batch size.")
        else:
            st.success(f"✅ PDF processed and stored in Qdrant collection: `{collection_name}`")
            st.info(f"📊 Total chunks processed: {len(split_docs)}")

            # Ask question
            query = st.text_input("💬 Ask a question about the PDF:")

            if query:
                with st.spinner("🔍 Searching for relevant information..."):
                    try:
                        # Search for similar documents with retry
                        def search_documents():
                            return vector_store.similarity_search(
                                query=query, 
                                k=4  # Return top 4 most relevant chunks
                            )
                        
                        search_results = retry_operation(search_documents)

                        # Prepare context
                        context_parts = []
                        for i, result in enumerate(search_results, 1):
                            page_num = result.metadata.get('page', 'N/A')
                            context_parts.append(
                                f"[Chunk {i}] Page {page_num}: {result.page_content[:500]}..."
                            )
                        
                        context = "\n\n".join(context_parts)

                        SYSTEM_PROMPT = f"""You are a helpful AI assistant. Answer the user's question based ONLY on the provided context from a PDF document.

Rules:
1. Only use information from the context below
2. If the answer isn't in the context, say "I don't have enough information in the provided context to answer that question."
3. When possible, mention the relevant page number
4. Be concise but comprehensive
5. If you're uncertain, say so

Context:
{context}
"""

                    except Exception as e:
                        st.error(f"Search failed: {str(e)}")
                        search_results = []

                if 'search_results' in locals() and search_results:
                    with st.spinner("🤖 Generating answer..."):
                        try:
                            def generate_response():
                                return openai_client.chat.completions.create(
                                    model="gpt-4",
                                    messages=[
                                        {"role": "system", "content": SYSTEM_PROMPT},
                                        {"role": "user", "content": query}
                                    ],
                                    temperature=0.1,
                                    max_tokens=1000,
                                    timeout=30
                                )

                            response = retry_operation(generate_response)
                            answer = response.choices[0].message.content
                            
                            # Display the answer
                            st.markdown("### 🤖 Answer:")
                            st.markdown(answer)
                            
                            # Show source information
                            with st.expander("📚 View Source Context"):
                                for i, result in enumerate(search_results, 1):
                                    st.markdown(f"**Chunk {i} (Page {result.metadata.get('page', 'N/A')}):**")
                                    st.text(result.page_content[:300] + "..." if len(result.page_content) > 300 else result.page_content)
                                    st.markdown("---")

                        except Exception as e:
                            st.error(f"Error generating response: {str(e)}")

    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        st.info("💡 Try the following solutions:")
        st.markdown("""
        - Reduce the batch size in the sidebar
        - Check your internet connection
        - Verify your Qdrant and OpenAI credentials
        - Try with a smaller PDF file
        - Wait a moment and try again
        """)
        
        # Clean up temporary file if it exists
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass