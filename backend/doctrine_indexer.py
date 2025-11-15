"""
Doctrine document indexer - loads and indexes Navy doctrine documents
"""

from pathlib import Path
from typing import List, Optional
import faiss
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer
import numpy as np
import pickle

from config import DOCTRINES_DIR, VECTOR_STORE_DIR, CHUNK_SIZE, CHUNK_OVERLAP


class LocalEmbeddings(Embeddings):
    """Local embeddings using sentence-transformers (offline)"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        return self.model.encode(text).tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents"""
        return self.model.encode(texts).tolist()


class DoctrineIndexer:
    """Indexes doctrine documents for RAG retrieval"""

    def __init__(self, embeddings: Optional[LocalEmbeddings] = None):
        self.embeddings = embeddings or LocalEmbeddings()
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            add_start_index=True
        )

    def load_pdf(self, file_path: Path) -> List[Document]:
        """Load and split a PDF document"""
        loader = PyPDFLoader(str(file_path))
        pages = loader.load()

        # Add source metadata
        for page in pages:
            page.metadata["source_file"] = file_path.name
            page.metadata["doctrine_type"] = "naval_doctrine"

        splits = self.text_splitter.split_documents(pages)
        return splits

    def load_text(self, file_path: Path) -> List[Document]:
        """Load and split a text document"""
        loader = TextLoader(str(file_path))
        docs = loader.load()

        # Add source metadata
        for doc in docs:
            doc.metadata["source_file"] = file_path.name
            doc.metadata["doctrine_type"] = "naval_doctrine"

        splits = self.text_splitter.split_documents(docs)
        return splits

    def load_all_doctrines(self, doctrines_dir: Path = DOCTRINES_DIR) -> List[Document]:
        """Load all doctrine documents from directory"""
        all_docs = []

        # Load PDFs
        for pdf_file in doctrines_dir.glob("**/*.pdf"):
            print(f"Loading PDF: {pdf_file.name}")
            docs = self.load_pdf(pdf_file)
            all_docs.extend(docs)
            print(f"  Added {len(docs)} chunks")

        # Load text files
        for txt_file in doctrines_dir.glob("**/*.txt"):
            print(f"Loading text: {txt_file.name}")
            docs = self.load_text(txt_file)
            all_docs.extend(docs)
            print(f"  Added {len(docs)} chunks")

        print(f"\nTotal doctrine chunks loaded: {len(all_docs)}")
        return all_docs

    def create_vector_store(self, documents: List[Document]) -> FAISS:
        """Create FAISS vector store from documents"""
        if not documents:
            print("No documents to index!")
            # Create empty vector store
            embedding_dim = self.embeddings.dimension
            index = faiss.IndexFlatL2(embedding_dim)
            vector_store = FAISS(
                embedding_function=self.embeddings,
                index=index,
                docstore=InMemoryDocstore(),
                index_to_docstore_id={}
            )
            return vector_store

        # Create embeddings for all documents
        print("Creating embeddings...")
        texts = [doc.page_content for doc in documents]
        embeddings = self.embeddings.embed_documents(texts)

        # Create FAISS index
        embedding_dim = len(embeddings[0])
        index = faiss.IndexFlatL2(embedding_dim)

        # Add embeddings to index
        embeddings_array = np.array(embeddings).astype('float32')
        index.add(embeddings_array)

        # Create docstore
        docstore = InMemoryDocstore({str(i): doc for i, doc in enumerate(documents)})
        index_to_docstore_id = {i: str(i) for i in range(len(documents))}

        # Create FAISS vector store
        vector_store = FAISS(
            embedding_function=self.embeddings,
            index=index,
            docstore=docstore,
            index_to_docstore_id=index_to_docstore_id
        )

        print(f"Vector store created with {len(documents)} documents")
        return vector_store

    def index_doctrines(self, force_reindex: bool = False) -> FAISS:
        """Index all doctrine documents"""
        vector_store_path = VECTOR_STORE_DIR / "doctrine_index"

        # Load existing index if available
        if vector_store_path.exists() and not force_reindex:
            print("Loading existing doctrine index...")
            try:
                self.vector_store = FAISS.load_local(
                    str(vector_store_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print("Loaded existing index")
                return self.vector_store
            except Exception as e:
                print(f"Error loading existing index: {e}")
                print("Creating new index...")

        # Create new index
        documents = self.load_all_doctrines()
        self.vector_store = self.create_vector_store(documents)

        # Save index
        if documents:
            print(f"Saving index to {vector_store_path}")
            self.vector_store.save_local(str(vector_store_path))

        return self.vector_store

    def search(self, query: str, k: int = 5) -> List[Document]:
        """Search for relevant doctrine passages"""
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Call index_doctrines() first.")

        return self.vector_store.similarity_search(query, k=k)

    def create_sample_doctrine(self, output_path: Optional[Path] = None):
        """Create a sample doctrine document for testing"""
        sample_doctrine = """
NAVAL DOCTRINE - SAMPLE TRAINING MANUAL
========================================

CHAPTER 1: SPEED CHANGES
------------------------

1.1 Standard Operating Procedures for Speed Changes

When changing speed during operations:
- All speed changes must be logged with timestamp and tracking number
- Changes exceeding 5 knots must be communicated to all stations
- Speed reductions for man overboard drills must follow emergency protocols:
  * Reduce speed to 5 knots immediately
  * Maintain heading until search pattern initiated
  * Log all actions with timestamps

1.2 Speed Change Documentation

Required documentation for speed changes:
- Timestamp of change (UTC)
- Previous speed
- New speed
- Reason for change
- Tracking number for reference


CHAPTER 2: COURSE CHANGES
--------------------------

2.1 Course Change Protocols

When changing course:
- Log timestamp, previous course, new course
- Assign tracking number to maneuver
- Notify navigation team of all course changes > 10 degrees
- For training exercises, document reasoning for tactical review


CHAPTER 3: CONTACT DETECTION AND TRACKING
------------------------------------------

3.1 Surface Contact Detection

Upon detecting surface contact:
- Immediately assign tracking number
- Log bearing, range, and timestamp
- Classify contact type (merchant, military, unknown)
- Maintain continuous tracking until contact passes
- Document all detection events for post-mission analysis

3.2 Contact Classification Requirements

All contacts must be classified according to:
- Visual identification when possible
- Radar signature analysis
- AIS data (when available)
- Behavior patterns

Contact classification must be documented with:
- Tracking number
- Timestamp of detection
- Initial classification
- Confidence level


CHAPTER 4: MAN OVERBOARD PROCEDURES
------------------------------------

4.1 Immediate Actions

Upon man overboard:
- Sound alarm immediately
- Reduce speed to 5 knots
- Mark position with GPS timestamp
- Deploy recovery equipment
- Initiate search pattern

All man overboard drills and actual events must be logged with:
- Exact timestamp
- Position (latitude/longitude)
- Sea conditions
- Recovery time
- Lessons learned


CHAPTER 5: MISSION START AND END PROCEDURES
--------------------------------------------

5.1 Mission Commencement

At mission start:
- Log start time (UTC)
- Record initial position
- Document mission objectives
- Verify all systems operational
- Begin mission log with tracking number

5.2 Mission Completion

At mission end:
- Log completion time
- Record final position
- Document mission outcomes
- Prepare post-mission debrief
- Submit mission log for review


CHAPTER 6: POST-MISSION DEBRIEFING
-----------------------------------

6.1 Debrief Requirements

All missions require post-mission debrief covering:
- Timeline of significant events
- Comparison of planned vs actual actions
- Doctrine compliance review
- Lessons learned
- Recommendations for future operations

6.2 Lessons Learned Documentation

Document lessons learned including:
- What worked well
- What could be improved
- Doctrinal gaps identified
- Training recommendations
- Equipment performance issues
"""

        if output_path is None:
            output_path = DOCTRINES_DIR / "sample_naval_doctrine.txt"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(sample_doctrine)

        print(f"Sample doctrine created at: {output_path}")
        return output_path


if __name__ == "__main__":
    # Test the indexer
    indexer = DoctrineIndexer()

    # Create sample doctrine if none exists
    if not any(DOCTRINES_DIR.glob("*.txt")) and not any(DOCTRINES_DIR.glob("*.pdf")):
        print("No doctrine documents found. Creating sample...")
        indexer.create_sample_doctrine()

    # Index doctrines
    indexer.index_doctrines(force_reindex=True)

    # Test search
    results = indexer.search("What are the requirements for speed changes?")
    print("\n\nSearch Results:")
    for i, doc in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(doc.page_content[:300])
