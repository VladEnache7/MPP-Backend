
# UDLLM News RAG Project Documentation

## 1. Introduction

### 1.1. Project Overview

The **UDLLM News RAG Project** is a comprehensive web application that leverages Retrieval-Augmented Generation (RAG) techniques to process and deliver news-related data. The project comprises two main components:

*   **Backend**: A Python-based system responsible for data scraping, processing, RAG implementation, and API services.
*   **Frontend**: A TypeScript and React-based user interface (Turbo Bassoon) for interactive news consumption and query.

The system gathers news articles from NBC News, indexes the content, and utilizes this knowledge base to provide accurate responses to user queries and generate news summaries.

### 1.2. Core Features

*   **Retrieval-Augmented Generation (RAG):**
    *   Combines retrieval with generative models for accurate, context-aware news summaries.
    *   Grounds generated content in reliable external news data.
*   **Comprehensive News Coverage:**
    *   Automated data collection from NBC News archives (2022-2025).
    *   Efficient storage and indexing for rapid article retrieval.
*   **Interactive User Interface:**
    *   Modern, responsive design for desktop and mobile.
    *   Intuitive search, filtering, and news navigation.
*   **Robust API Services:**
    *   RESTful endpoints for seamless frontend-backend communication.
    *   Optimized for efficient data transfer.
*   **Scalability:**
    *   Designed to handle significant data volumes and concurrent user requests.

## 2. System Architecture Diagram and Flows

This section provides a visual overview of the project's architecture and describes the key components and their interactions.

### 2.1. Architecture Diagram

![Diagram](diagram.jpeg)
*(The diagram illustrates the interaction between the Frontend, Backend (FastAPI App with its Core services, Vector Store, and Database), and external LLM services like Ollama and HuggingFace.)*

### 2.2. Component Breakdown and Flows

The system is broadly divided into Frontend and Backend components.

#### 2.2.1. Frontend

*   **Client:** The user-facing interface (e.g., a web browser running the Turbo Bassoon React application).
    *   **Function:** Initiates HTTP requests to the backend based on user interactions (e.g., submitting a query, requesting news summaries).

#### 2.2.2. Backend

The backend is built using FastAPI and orchestrates the RAG pipeline.

*   **FastAPI App:** The central application server that exposes API endpoints.
    *   **`/api/prompt`:** Handles user queries that require LLM processing and RAG.
    *   **`/api/system-prompts`:** Manages system-level prompts.
    *   **`/api/health`:** Provides a health check for the backend services.

*   **Core Services:**
    *   **`LLM Service`:** This is the brain of the RAG pipeline. It orchestrates the process: taking a user prompt, fetching relevant documents from the Vector Store, and then prompting the Ollama LLM with the original query and the retrieved context to generate a response. 
        *   **Why:** Centralizes the RAG logic, making the system more organized.
    *   **`Prompt Service`:** This service manages the system prompts, storing and retrieving them from a Database (PostgreSQL). It also handles user feedback like "likes/dislikes" on the LLM's responses, which is crucial for iterative improvement. Furthermore, it interfaces with Ollama/HuggingFace for accessing the LLM and embedding models.
        *   **Why:** Enables dynamic and adaptable LLM behavior and provides a mechanism for collecting user feedback to refine the system.

*   **Vector Store:**
    *   **Component:** `Qdrant` is used as the vector database to store an `Articles Collection`. These "articles" are documents that have been processed and converted into vector embeddings (numerical representations).
    *   **Function:** When a user prompt is received, its embedding is used to search Qdrant for articles with similar embeddings, thus finding the most relevant context.
    *   **Why Qdrant:** It's a specialized database optimized for fast and efficient similarity searches on large-scale vector data, which is essential for the "Retrieval" step in RAG.

*   **Database (Relational):**
    *   **Component:** `PostgreSQL`.
    *   **Function:** Used to store structured data such as the `System Prompts Table` and user `likes/dislikes`.
    *   **Why PostgreSQL:** A robust, open-source relational database well-suited for storing structured data, ensuring data integrity and supporting complex queries if needed.

*   **External AI Models & Tools:**
    *   **`Ollama LLM`:** The system uses a Large Language Model (e.g., "mistral" as specified in the code) served via Ollama. This model is responsible for generating the human-like text responses.
        *   **Why Ollama:** Allows you to run open-source LLMs locally or on your own infrastructure. This provides more control over the models, can be more cost-effective, and can enhance data privacy compared to relying solely on third-party LLM APIs.
    *   **`Embedding Model (Hugging Face)`:** A model like `BAAI/bge-large-en-v1.5` (from Hugging Face, as in the code) is used to create vector embeddings for both the articles in your database and the incoming user prompts.
        *   **Why Hugging Face Models:** Hugging Face is a leading platform for accessing a vast array of pre-trained NLP models, including high-quality embedding models critical for the effectiveness of the semantic search in RAG.

#### 2.2.3. Workflow for a User Prompt (Example for `/api/prompt`)

1.  **Request:** The **Client (Frontend)** sends a user's query (e.g., "What are the latest developments in AI?") to the `/api/prompt` endpoint of the **FastAPI App**.
2.  **Processing Trigger:** The `prompt_llm` function (or similar handler like `rag_query` in `main.py`) is triggered.
3.  **Embedding:** The user's query is converted into a vector embedding using the **Embedding Model (HuggingFace)**.
4.  **Retrieval:** This query embedding is used to search the **Articles Collection** in **Qdrant**. Qdrant returns the most semantically similar articles (or chunks of articles).
5.  **Augmentation & Generation:** The retrieved articles (context) are combined with the original user query. This augmented input, potentially including a system prompt retrieved by the **Prompt Service**, is then sent to the **Ollama LLM**.
6.  **Response Generation:** The **Ollama LLM** generates a response based on the query and the provided context. Metadata (like title and URL) from the retrieved source articles might also be extracted.
7.  **Response to Client:** The final response, along with any source article metadata, is sent back through the FastAPI App to the **Client**.

#### 2.2.4. Why This Architecture is Effective

*   **Enhanced Accuracy & Relevance:** The RAG approach grounds the LLM's responses in the specific data you provide (your Articles Collection), reducing the chances of "hallucination" and ensuring responses are relevant to your document set.
*   **Modularity & Scalability:** Separating concerns into different services (FastAPI for API, LLM Service for orchestration, Qdrant for vector search, PostgreSQL for relational data) makes the system easier to develop, test, maintain, and scale individual components.
*   **Flexibility with Models:** Using Ollama and Hugging Face models allows you to experiment with and switch out different LLMs and embedding models as new or better ones become available, adapting to the rapidly evolving AI landscape.
*   **Control & Customization:** Self-hosting models with Ollama and managing your own data in Qdrant gives you significant control over your AI pipeline, data privacy, and system behavior.
*   **Feedback Loop:** The planned likes/dislikes feature (managed by the Prompt Service and stored in PostgreSQL) is vital for creating an iterative improvement cycle, allowing the system to learn from user interactions and refine its performance over time.

## 3. Backend Details

### 3.1. Technology Stack

*   **Programming Language:** Python
*   **Frameworks/Libraries:**
    *   FastAPI (API Management)
    *   LlamaIndex (Core RAG orchestration, integrating vector stores and LLMs)
    *   Qdrant (Client library for vector database interaction)
    *   HuggingFace Transformers/Sentence-Transformers (for embedding models)
    *   Puppeteer (via Node.js for Web Scraping - executed as separate scripts)
    *   Pandas / NumPy (Data Processing)
*   **Database:** PostgreSQL (Relational Data: System Prompts, Feedback), Qdrant (Vector Data: Articles Collection)
*   **LLM Serving:** Ollama
*   **External LLM Interfaces:** Client libraries for Ollama, HuggingFace.

### 3.2. Data Collection & Processing

#### 3.2.1. Article Link Collection
Utilizes a Puppeteer script (`gather-article-links.js`) to scrape article URLs from NBC News archives.
*   **Output:** `nbc.json` (list of article URLs).
```javascript
// Key snippet from gather-article-links.js
import puppeteer from "puppeteer";
import fs from "fs";

const BASE_URL = "https://www.nbcnews.com/archive/articles";
const ARTICLE_TAG = ".MonthPage > a"; // CSS Selector for article links
// ... (rest of the script)
```

#### 3.2.2. Article Content Extraction
A second Puppeteer script (`scrape-article-content.js`) visits each collected URL to extract detailed content.
*   **Output:** `parsed_data_nbc.json` (structured article data). This raw text data is then processed by the **Embedding Model** to create vector embeddings, which are subsequently stored in the **Articles Collection** within **Qdrant**.
```javascript
// Key snippet from scrape-article-content.js
// ...
const title = await page.$(".article-hero-headline__htag");
const paragraphs = await page.$$(".body-graf");
const date = await page.evaluate(() => {
  const metaTag = document.querySelector('meta[property="article:published_time"]');
  return metaTag ? metaTag.getAttribute("content") : null;
});
// ...
```
*Data Structure (per article before embedding):*
```json
{
  "title": "Article headline text",
  "url": "https://www.nbcnews.com/article-path",
  "content": ["Paragraph 1", "Paragraph 2", "..."],
  "date": "2025-04-15T14:30:00Z"
}
```

### 3.3. API Endpoints (Summary)

*   **`POST /api/prompt`**: Main endpoint for user queries requiring RAG processing.
*   **`GET /api/system-prompts`**: Endpoint for managing system prompts (behavior might include POST/PUT/DELETE for full CRUD).
*   **`GET /api/health`**: Health check for the backend.

## 4. Frontend Details (Turbo Bassoon)

### 4.1. Technology Stack

*   **Programming Language:** TypeScript
*   **Frameworks/Libraries:**
    *   React (UI Development)
    *   Axios / Fetch API (API Communication)
    *   Tailwind CSS / Material-UI (Styling)
    *   React-Router (Navigation)
*   **Build Tools:** Vite / Webpack

### 4.2. Key Features

*   **Dynamic User Interface:** Seamless, interactive, and responsive.
*   **Backend Integration:** Efficiently communicates with backend APIs.
*   **Search and Filtering:** Client-side capabilities for enhanced user experience.
*   **Modern Styling:** Customizable themes and consistent UI.

### 4.3. API Integration

The frontend interacts with the backend API endpoints defined in section 2.2.2 and 3.3.

*   **Querying/Generating News (via `/api/prompt`):**
    ```typescript
    // Example: src/services/api.ts
    import axios from 'axios';
    const API_URL = process.env.REACT_APP_BACKEND_URL;

    export const submitPrompt = async (userQuery: string) => {
      const response = await axios.post(`${API_URL}/api/prompt`, { query: userQuery }); // Adjust payload as needed based on actual API definition in main.py
      return response.data; // Contains generated summary or relevant data
    };
    ```
*   **Managing System Prompts (via `/api/system-prompts`):** (Implementation would depend on UI for this)
