from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import os
import numpy as np
import faiss
import pickle
import time

# Load environment variables from .env file
dotenv_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def get_embedding(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding

def process_content_file():
    """Read content.txt, get its embedding, and save results."""
    try:
        # Path to content.txt file
        content_file_path = "src/code_folder/content.txt"
        
        # Read the content file
        with open(content_file_path, 'r') as file:
            content = file.read()
        
        print(f"Content file loaded, length: {len(content)} characters")
        
        # If the content is too large, we might need to chunk it
        # OpenAI has token limits (e.g., about 4-8K tokens for embedding models)
        max_chunk_size = 10000  # characters, adjust based on your model's limits
        
        if len(content) > max_chunk_size:
            # Simple chunking by character count
            chunks = [content[i:i+max_chunk_size] for i in range(0, len(content), max_chunk_size)]
            print(f"Content split into {len(chunks)} chunks")
            
            # Get embeddings for each chunk and store chunk content
            embedded_chunks = []
            for i, chunk in enumerate(chunks):
                print(f"Processing chunk {i+1}/{len(chunks)}")
                embedding = get_embedding(chunk)
                embedded_chunks.append({
                    'chunk_id': str(i+1),
                    'text': chunk,
                    'embedding': embedding
                })
            
            # Store embeddings in FAISS index
            print("Storing embeddings in FAISS index...")
            index, _ = store_in_faiss(embedded_chunks)
            
            # Save FAISS index and embedded chunks
            output_dir = "src/code_folder/embedding"
            os.makedirs(output_dir, exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(index, f"{output_dir}/content.index")
            
            # Save embedded chunks as pickle
            with open(f"{output_dir}/embedded_chunks.pkl", "wb") as f:
                pickle.dump(embedded_chunks, f)
            
            print(f"FAISS index and embedded chunks saved to {output_dir}")
                
        else:
            # Get embedding for the entire content
            print("Getting embedding for the entire content...")
            embedding = get_embedding(content)
            
            # Create a single embedded chunk
            embedded_chunks = [{
                'chunk_id': 'full',
                'text': content,
                'embedding': embedding
            }]
            
            # Store in FAISS index
            print("Storing embedding in FAISS index...")
            index, _ = store_in_faiss(embedded_chunks)
            
            # Save FAISS index and embedded chunks
            output_dir = "src/code_folder/embedding"
            os.makedirs(output_dir, exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(index, f"{output_dir}/content.index")
            
            # Save embedded chunks as pickle
            with open(f"{output_dir}/embedded_chunks.pkl", "wb") as f:
                pickle.dump(embedded_chunks, f)
            
            print(f"FAISS index and embedded chunks saved to {output_dir}")
            
        return True
    
    except Exception as e:
        print(f"Error processing content file: {e}")
        return False

def store_in_faiss(embedded_chunks):
    """
    Store embeddings in a FAISS index for efficient similarity search.
    
    Args:
        embedded_chunks: List of dictionaries with 'embedding' key containing vector
    
    Returns:
        tuple: (faiss_index, embedded_chunks)
    """
    # Get dimension from first embedding
    dimension = len(embedded_chunks[0]['embedding'])
    
    # Create a FAISS index - using L2 distance
    index = faiss.IndexFlatL2(dimension)
    
    # Convert embeddings to numpy array
    embeddings = np.array([chunk['embedding'] for chunk in embedded_chunks], dtype=np.float32)
    
    # Add vectors to index
    index.add(embeddings)
    
    return index, embedded_chunks

def load_faiss_index():
    """
    Load FAISS index and embedded chunks from disk.
    
    Returns:
        tuple: (faiss_index, embedded_chunks)
    """
    try:
        output_dir = "src/code_folder/embedding"
        
        # Load FAISS index
        index = faiss.read_index(f"{output_dir}/content.index")
        
        # Load embedded chunks
        with open(f"{output_dir}/embedded_chunks.pkl", "rb") as f:
            embedded_chunks = pickle.load(f)
        
        return index, embedded_chunks
    
    except Exception as e:
        print(f"Error loading FAISS index: {e}")
        return None, None

def search_similar_chunks(query, top_k=5):
    """
    Search for similar chunks using FAISS.
    
    Args:
        query: String to search for
        top_k: Number of results to return
    
    Returns:
        list: List of dictionaries with 'chunk_id', 'text', and 'similarity'
    """
    try:
        # Load FAISS index and embedded chunks
        index, embedded_chunks = load_faiss_index()
        
        if index is None or embedded_chunks is None:
            print("FAISS index not found. Please run process_content_file() first.")
            return []
        
        # Get embedding for query
        print("Getting embedding for query...")
        query_embedding = get_embedding(query)
        
        # Convert to numpy array
        query_vector = np.array([query_embedding], dtype=np.float32)
        
        # Search FAISS index
        print("Searching FAISS index...")
        distances, indices = index.search(query_vector, top_k)
        
        # Prepare results
        results = []
        for i, idx in enumerate(indices[0]):
            # Check if idx is valid
            if idx < len(embedded_chunks) and idx >= 0:
                chunk = embedded_chunks[idx]
                # FAISS returns L2 distance, convert to similarity score (0 distance = perfect match)
                similarity = 1.0 / (1.0 + distances[0][i])
                
                results.append({
                    'chunk_id': chunk['chunk_id'],
                    'text': chunk['text'],
                    'similarity': similarity
                })
        
        return results
    
    except Exception as e:
        print(f"Error searching similar chunks: {e}")
        return []

def answer_question(query):
    """
    Use GPT model to answer a question based on context from similar chunks found via FAISS.
    
    Args:
        query: Question to ask
    
    Returns:
        string: AI-generated answer to the question
    """
    try:
        # Get similar chunks using FAISS
        results = search_similar_chunks(query, top_k=5)
        
        if not results:
            return "I couldn't find any relevant information in the codebase to answer your question."
        
        # Combine the text from the chunks to create context
        context = "\n\n---\n\n".join(result["text"] for result in results)
        
        # Prepare the prompt for GPT
        prompt = f"""You are an expert software engineer.
        Based on the following code context, answer the question.
        
        Context:
        {context}

        Question: {query}
        
        # Keep below thing in mind while answering the question:
        - Your final output should always be a concise answer to the question.
        - Also provide the relevant code snippets if necessary.
        - Generate the final a concise answer in markdown format.
        """

        print("Sending question to GPT...")
        
        # Call OpenAI API with the prompt
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract and return the answer
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error answering question: {e}")
        return f"Sorry, I encountered an error while trying to answer your question: {e}"

def interactive_search():
    """
    Start an interactive search session where the user can input queries
    and get related content from the embedded files using FAISS.
    """
    # ANSI color codes
    YELLOW = "\033[93m"  # Yellow
    GREEN = "\033[92m"   # Green
    CYAN = "\033[96m"    # Cyan
    BOLD = "\033[1m"     # Bold
    RESET = "\033[0m"    # Reset all formatting
    
    print(f"\n{BOLD}{CYAN}===== Interactive Code Search with FAISS ====={RESET}")
    print(f"{GREEN}Enter your query about the codebase, or type 'quit' to exit.{RESET}")
    print(f"{GREEN}To ask for AI assistance with a question, start your query with '?'{RESET}")
    
    while True:
        query = input(f"\n{YELLOW}Your query:{RESET} ")
        
        if query.lower() in ['quit', 'exit', 'q']:
            print(f"{GREEN}{BOLD}Exiting search. Goodbye!{RESET}")
            break
        
        if not query.strip():
            print(f"{YELLOW}Please enter a valid query.{RESET}")
            continue
            
        # Check if the user is asking a question (starts with ?)
        if query.strip().startswith('?'):
            question = query.strip()[1:].strip()  # Remove the ? and any leading/trailing whitespace
            if not question:
                print(f"{YELLOW}Please provide a question after '?'{RESET}")
                continue
                
            print(f"\n{YELLOW}Analyzing code and answering your question...{RESET}")
            start_time = time.time()
            answer = answer_question(question)
            answer_time = time.time() - start_time
            
            print(f"\n{YELLOW}----- Answer (generated in {answer_time:.2f} seconds) -----{RESET}")
            print(answer)
            print(f"\n{YELLOW}" + "-" * 50 + f"{RESET}")
            continue
        
        # Regular code search
        print(f"\n{YELLOW}Searching for relevant code snippets...{RESET}")
        start_time = time.time()
        results = search_similar_chunks(query, top_k=3)
        search_time = time.time() - start_time
        
        if not results:
            print(f"{YELLOW}No relevant results found. Try a different query.{RESET}")
            continue
        
        print(f"\n{YELLOW}----- Search Results (found in {search_time:.2f} seconds) -----{RESET}")
        
        for i, result in enumerate(results):
            chunk_id = result['chunk_id']
            similarity = result['similarity']
            text = result['text']
            
            print(f"\n{YELLOW}Result {i+1} (Similarity: {similarity:.2f}){RESET}")
            print(f"{YELLOW}" + "-" * 50 + f"{RESET}")
            
            # Show a preview (first 300 characters)
            preview_length = 300
            preview = text[:preview_length] + "..." if len(text) > preview_length else text
            print(preview)
            
            # Ask if user wants to see full content
            see_more = input(f"\n{YELLOW}See full content? (y/n):{RESET} ")
            if see_more.lower() in ['y', 'yes']:
                print("\n" + "=" * 30 + " FULL CONTENT " + "=" * 30)
                print(text)
                print("=" * 71)
        
        print("\n" + "-" * 50)

if __name__ == "__main__":
    # ANSI color codes
    YELLOW = "\033[93m"  # Yellow
    GREEN = "\033[92m"   # Green
    CYAN = "\033[96m"    # Cyan
    BOLD = "\033[1m"     # Bold
    RESET = "\033[0m"    # Reset all formatting
    
    # Check if the FAISS index exists
    output_dir = "src/code_folder/embedding"
    index_path = f"{output_dir}/content.index"
    
    if not os.path.exists(index_path):
        print(f"{YELLOW}{BOLD}FAISS index not found. Creating embeddings and index...{RESET}")
        success = process_content_file()
        
        if not success:
            print(f"{YELLOW}{BOLD}Failed to create FAISS index. Please check the errors above.{RESET}")
            exit(1)
    
    print(f"\n{CYAN}{BOLD}Starting interactive search...{RESET}")
    interactive_search()