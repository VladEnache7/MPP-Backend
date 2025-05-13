
# UDLLM News RAG Project Documentation

## 1. Introduction

### 1.1. Project Overview

The **UDLLM News RAG Project** is an advanced web application leveraging Retrieval-Augmented Generation (RAG) to process and deliver news-related data, now with dual capabilities for standard news and satirical content. The project comprises:

*   **Backend**: A Python-based system managing data scraping, processing, a sophisticated RAG pipeline with distinct paths for factual and satirical content, API services, and real-time event handling via Kafka.
*   **Frontend**: A TypeScript and React-based user interface (Turbo Bassoon) for interactive news consumption, satirical content interaction, and user feedback.

The system gathers news articles (factual and satirical), indexes them in specialized vector stores, and utilizes this knowledge base to provide contextually accurate and appropriately toned responses.

### 1.2. Core Features

*   **Dual-Mode Retrieval-Augmented Generation (RAG):**
    *   Separate RAG pipelines for factual news and satirical content, ensuring appropriate context and tone.
    *   Grounds generated content in reliable external news data or curated satirical sources.
*   **Comprehensive Content Coverage:**
    *   Automated data collection from NBC News archives (2022-2025) and potentially other sources for satirical content.
    *   Efficient storage and indexing in distinct vector collections for rapid and context-specific retrieval.
*   **Event-Driven Architecture with Kafka:**
    *   Real-time processing of user feedback.
    *   Asynchronous handling of potentially intensive tasks like satirical content generation.
    *   Enhanced system decoupling and scalability.
*   **Interactive User Interface:**
    *   Modern, responsive design for desktop and mobile.
    *   Intuitive search, filtering, news navigation, and satirical content interaction.
    *   Integrated user feedback mechanism.
*   **Robust and Specialized API Services:**
    *   RESTful endpoints for seamless frontend-backend communication, including dedicated endpoints for satirical prompts and feedback.
*   **Scalability & Modularity:**
    *   Designed to handle significant data volumes and concurrent user requests, with services that can be scaled independently.

## 2. System Architecture

This section provides a visual overview of the project's architecture and describes the key components and their interactions.

### 2.1. Architecture Diagram

![image](https://github.com/user-attachments/assets/9bc42709-5462-462b-9bcc-6de99f89679c)

*(The diagram illustrates the interaction between the Frontend, Backend (FastAPI App with its Core services including Kafka, specialized LLM services, Vector Stores, and Database), Kafka Broker, and external LLM services like Ollama.)*

### 2.2. Component Breakdown

The system is broadly divided into Frontend, Backend, and Messaging Layer components.

#### 2.2.1. Frontend

*   **Client:** The user-facing React application (Turbo Bassoon).
    *   **Function:** Initiates HTTP requests to the backend for:
        *   Standard news queries (`/api/prompt`).
        *   Satirical content queries (`/api/satirical-prompt`).
        *   Submitting user feedback (`/api/feedback`).
        *   System health checks (`/api/health`).
        *   Managing system prompts (`/api/system-prompts`).

#### 2.2.2. Backend

Built using FastAPI, orchestrating diverse RAG pipelines and services.

*   **FastAPI App:** Central application server exposing API endpoints:
    *   **`POST /api/prompt`:** Handles user queries for standard news, requiring RAG processing via the `LLM Service`.
    *   **`POST /api/satirical-prompt`:** Handles user queries for satirical content, engaging the `Satirical LLM Service`.
    *   **`POST /api/feedback`:** Receives user feedback (e.g., likes/dislikes), which is then typically published to the `Kafka Broker` for asynchronous processing.
    *   **`GET /api/system-prompts`:** Manages (CRUD) system-level prompts via the `Prompt Service`.
    *   **`GET /api/health`:** Provides a health check, potentially interacting with the `Config Service`.

*   **Core Services:**
    *   **`LLM Service`:** The brain for the standard news RAG pipeline.
        *   **Function:** Takes a user prompt, fetches relevant documents from the `Articles Collection` in Qdrant, and prompts an `Ollama LLM` with the original query and retrieved context to generate a factual response.
        *   **Interactions:** `FastAPI App`, `Vector Store (Articles Collection)`, `Ollama LLM`, `Prompt Service` (for system prompts), `Config Service`.
    *   **`Satirical LLM Service`:** Dedicated service for generating satirical content.
        *   **Function:** Handles requests from `/api/satirical-prompt`. It retrieves relevant satirical articles/context from the `Satirical Articles Collection` in Qdrant, constructs prompts using specialized strategies, and interacts with an `Ollama LLM` (potentially a different model or configuration optimized for creative/satirical text). May operate asynchronously with Kafka.
        *   **Interactions:** `FastAPI App`, `Vector Store (Satirical Articles Collection)`, `Ollama LLM`, `Kafka Service` (for async tasks), `Prompt Service`, `Config Service`.
    *   **`Prompt Service`:** Manages prompt engineering and user feedback lifecycle.
        *   **Function:**
            *   Handles CRUD operations for the `System Prompts Table` in PostgreSQL.
            *   Processes structured user feedback (likes/dislikes from `/api/feedback`, likely received via Kafka) and stores it in PostgreSQL. This feedback is crucial for iterative improvement of prompt strategies or model fine-tuning.
            *   Provides prompts to both `LLM Service` and `Satirical LLM Service`.
        *   **Interactions:** `FastAPI App`, `LLM Service`, `Satirical LLM Service`, `Database (PostgreSQL)`, `Kafka Service` (for consuming feedback events), `Config Service`.
    *   **`Kafka Service`:** Facilitates event-driven communication and asynchronous processing.
        *   **Function:** Acts as a producer and consumer for Kafka topics. Publishes events (e.g., new feedback received) and consumes events for tasks like processing feedback by the `Prompt Service` or managing asynchronous generation by the `Satirical LLM Service`.
        *   **Interactions:** `FastAPI App` (publishing feedback), `Prompt Service` (consuming feedback), `Satirical LLM Service` (consuming generation tasks, publishing results), `Kafka Broker`, `Config Service`.
    *   **`Config Service`:** Centralized configuration management.
        *   **Function:** Provides configuration settings (e.g., API keys, model parameters, Kafka topics, feature flags) to all backend services.
        *   **Why:** Separates configuration from code, simplifying management across different environments.
        *   **Interactions:** All other Core Services, `FastAPI App`.

*   **Vector Store (Qdrant):**
    *   **`Articles Collection`:** Stores vector embeddings of standard news articles for factual RAG.
    *   **`Satirical Articles Collection`:** Stores vector embeddings of curated satirical content for humorous RAG.
    *   **Function:** Enables efficient semantic similarity search for retrieving relevant context for both factual and satirical queries.
    *   **Why Qdrant:** Specialized for fast, scalable similarity searches on large vector datasets.

*   **Database (Relational - PostgreSQL):**
    *   **`System Prompts Table`:** Stores predefined system prompts for guiding LLM behavior.
    *   **`likes/dislikes Table`:** Stores structured user feedback on generated responses.
    *   **Why PostgreSQL:** Robust, open-source RDBMS for structured data, ensuring data integrity.

*   **External AI Models & Tools:**
    *   **`Ollama LLM`:** Serves Large Language Models (e.g., "mistral"). Used by both `LLM Service` and `Satirical LLM Service`, potentially with different models or configurations tailored to the task (factual vs. satirical).
        *   **Why Ollama:** Enables local/self-hosted deployment of open-source LLMs for control, cost-effectiveness, and data privacy.
    *   **`Embedding Model (e.g., from Hugging Face)`:** (Implicitly used) Models like `BAAI/bge-large-en-v1.5` are used to convert text (articles and user queries) into vector embeddings for storage and search in Qdrant.
        *   **Why Hugging Face Models:** Access to a wide array of high-quality pre-trained embedding models.

#### 2.2.3. Messaging Layer

*   **`Kafka Broker`:** The central message bus for the event-driven aspects of the architecture.
    *   **Function:** Receives messages (events) from producers (e.g., `FastAPI App` upon feedback submission, `Kafka Service`) and delivers them to consumers (e.g., `Kafka Service` for `Prompt Service` or `Satirical LLM Service`).
    *   **Why Kafka:** Enables decoupling of services, asynchronous processing, improved fault tolerance, and scalability for real-time data streams.

### 2.3. Key Workflows

#### 2.3.1. Standard News Query Workflow (`/api/prompt`)

1.  **Request:** Client sends a query to `/api/prompt`.
2.  **Routing:** FastAPI routes to `LLM Service`.
3.  **Embedding:** Query is converted to a vector embedding.
4.  **Retrieval:** `LLM Service` queries `Articles Collection` in Qdrant for relevant articles.
5.  **Augmentation & Generation:** Retrieved context + original query (and system prompt from `Prompt Service`) are sent to an `Ollama LLM`.
6.  **Response:** LLM generates a factual response; metadata is extracted.
7.  **Return:** Response and sources are returned to the Client.

#### 2.3.2. Satirical Content Query Workflow (`/api/satirical-prompt`)

1.  **Request:** Client sends a query to `/api/satirical-prompt`.
2.  **Routing:** FastAPI routes to `Satirical LLM Service`.
3.  **Embedding:** Query is converted to a vector embedding.
4.  **Retrieval:** `Satirical LLM Service` queries `Satirical Articles Collection` in Qdrant.
5.  **Prompting & Generation (potentially asynchronous via Kafka):**
    *   Retrieved satirical context + query (and specialized system prompt) are sent to an `Ollama LLM` (optimized for satire).
    *   If asynchronous: Task might be published to Kafka by `Satirical LLM Service`, processed by a worker consuming from Kafka, then result sent back or notified.
6.  **Response:** LLM generates a satirical response.
7.  **Return:** Satirical response is returned to the Client.

#### 2.3.3. User Feedback Workflow (`/api/feedback`)

1.  **Request:** Client submits feedback (e.g., like/dislike) to `/api/feedback`.
2.  **Publish Event:** FastAPI (or `Kafka Service` directly) publishes a feedback event to a specific topic in `Kafka Broker`.
3.  **Consume Event:** `Kafka Service` consumes the feedback event.
4.  **Process & Store:** The consumed event is passed to the `Prompt Service`, which processes the feedback (e.g., aggregates ratings) and stores it in the `likes/dislikes` table in PostgreSQL.
5.  **Future Improvement:** This stored feedback can be used for analyzing response quality, refining prompts, or even fine-tuning models.

### 2.4. Why This Enhanced Architecture is Effective

*   **Specialized Content Handling:** Dedicated services and data stores for factual vs. satirical content ensure appropriate tone, context, and quality for diverse user needs.
*   **Improved Responsiveness & Scalability with Kafka:** Asynchronous processing for feedback and potentially complex generation tasks prevents blocking API calls and allows services to scale independently.
*   **Enhanced Accuracy & Relevance:** RAG grounds LLM responses in curated data, minimizing hallucinations and tailoring outputs.
*   **Robust Feedback Loop:** Structured feedback collection via Kafka and PostgreSQL enables continuous improvement of the system's performance and content quality.
*   **Modularity & Maintainability:** Clear separation of concerns into microservices makes the system easier to develop, test, deploy, and maintain.
*   **Flexibility with Models:** Ollama and Hugging Face integration allows for easy experimentation and swapping of LLMs and embedding models.
*   **Control & Customization:** Self-hosting models and managing data provides significant control over the AI pipeline and data privacy.

## 3. Backend Details

### 3.1. Technology Stack

*   **Programming Language:** Python
*   **Frameworks/Libraries:**
    *   FastAPI (API Management)
    *   LlamaIndex (Core RAG orchestration)
    *   Qdrant Client (Vector database interaction)
    *   HuggingFace Transformers/Sentence-Transformers (Embedding models)
    *   `confluent-kafka-python` or `kafka-python` (Kafka client library)
    *   Puppeteer (via Node.js for Web Scraping - if still applicable for both content types)
    *   Pandas / NumPy (Data Processing)
*   **Databases:**
    *   PostgreSQL (Relational Data: System Prompts, Feedback)
    *   Qdrant (Vector Data: Articles Collection, Satirical Articles Collection)
*   **Messaging:** Apache Kafka (Kafka Broker)
*   **LLM Serving:** Ollama
*   **External LLM Interfaces:** Client libraries for Ollama.

### 3.2. Data Collection & Processing


#### 3.2.1. Article Link Collection
Utilizes a Puppeteer script (`gather-article-links.js`) to scrape article URLs from NBC News archives.
*   **Output:** `nbc.json` (list of article URLs).
```javascript
// Key snippet from gather-article-links.js
import puppeteer from "puppeteer";
import fs from "fs";

const BASE_URL = "https://www.nbcnews.com/archive/articles"; // "https://www.theonion.com"
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
  "date": "2025-04-15T14:30:00Z",
  "type": "factual or satirical"
}
```

### 3.3. API Endpoints (Summary)

*   **`POST /api/prompt`**: Main endpoint for factual RAG queries.
*   **`POST /api/satirical-prompt`**: Endpoint for satirical RAG queries.
*   **`POST /api/feedback`**: Endpoint for submitting user feedback.
*   **`GET /api/system-prompts`**: (And `POST`, `PUT`, `DELETE`) For CRUD operations on system prompts.
*   **`GET /api/health`**: Health check for the backend.

## 4. Frontend Details 

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
*   **Querying Satirical Content (via `/api/satirical-prompt`):**
    ```typescript
    // Example: src/services/api.ts
    export const submitSatiricalPrompt = async (userQuery: string) => {
      const response = await axios.post(`${API_URL}/api/satirical-prompt`, { query: userQuery });
      return response.data;
    };
    ```
*   **Submitting Feedback (via `/api/feedback`):**
    ```typescript
    // Example: src/services/api.ts
    export const submitUserFeedback = async (feedbackData: { responseId: string; liked: boolean; comment?: string }) => {
      const response = await axios.post(`${API_URL}/api/feedback`, feedbackData);
      return response.data;
    };
    ```
*   **Managing System Prompts (via `/api/system-prompts`):** (Implementation would depend on UI for this)
