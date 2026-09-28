# REG RAG

A Streamlit regulatory question-answering assistant. It retrieves relevant passages from an Arabic regulatory-document index with Hugging Face embeddings and generates grounded answers with Google Gemini.

## Architecture

```text
app.py       Streamlit chat interface and session-only conversation history
backend.py  Chroma retrieval, Hugging Face query embeddings, and Gemini generation
trails.ipynb OCR, cleaning, chunking, and creation of the local Chroma index
```

The app reads the `rag_db` collection from `./chromadatabase`. The vector index is generated data and is intentionally excluded from Git. Regulatory PDFs are also excluded because their redistribution may require permission.

## Setup

1. Install Python 3.10 or newer and the system tools required by OCR: Tesseract with Arabic language data and Poppler.
2. Create an environment and install the Python dependencies:

   ```bash
   python -m venv .venv
   .venv\\Scripts\\activate
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in `HF_TOKEN` and `GEMINI_API_KEY`. Set `araconfig` to the Tesseract configuration used by your machine.
4. Place authorized Arabic regulatory PDFs in `sources/` and run the cells in `trails.ipynb` to build or refresh `chromadatabase`.
5. Start the chat UI:

   ```bash
   streamlit run app.py
   ```

The application can be opened without rebuilding the index only when a compatible `chromadatabase` already exists locally.

## Security and data handling

Never commit `.env`, API keys, PDFs, or generated Chroma files. If credentials have ever been exposed outside your local machine, revoke and rotate them before publishing the repository. Conversation history is held in Streamlit session state and is not persisted by this project.

## License

No license is currently declared. Add a license before accepting external contributions or distributing the project.
