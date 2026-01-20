@echo off
echo Starting RAG Document Assistant...
echo.
echo Make sure you have configured your .env file with:
echo   - OPENAI_API_KEY
echo   - PINECONE_API_KEY
echo   - PINECONE_INDEX_NAME
echo.
call venv\Scripts\activate
python -m app.main
