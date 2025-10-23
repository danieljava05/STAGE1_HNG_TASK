# Strings API (FastAPI)

Implements endpoints:
1. POST /strings – Create string  
2. GET /strings/{string_value} – Get string  
3. GET /strings – Filtered listing  
4. GET /strings/filter-by-natural-language – Natural language filtering  
5. DELETE /strings/{string_value} – Delete string  

### Run Locally
```bash
pip install -r requirements.txt
uvicorn main:app --reload
