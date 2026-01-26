# Backend

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your Supabase credentials:
   
   <https://supabase.com/dashboard/project/hvaudmnxzqkllqmrbzab/settings/api-keys>
   ```   
   SUPABASE_URL is the project id url
   SUPABASE_KEY can be either Publishable Key or Secret Key
   Publishable can be used in the frontend and uses row-level security (RLS) 
   Secret Key can be used in the backend and bypasses RL
   ```
    An example is in `.env.example`


## Running the API

Start the FastAPI server:

```bash
uvicorn src.main:app --reload
```

The API will be available at http://localhost:8000
Interactive API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc



