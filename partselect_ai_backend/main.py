# main.py
from fastapi import FastAPI
import os
from dotenv import load_dotenv
from routes.chat import chat_router
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()

app = FastAPI(
    title="PartSelect Chat Agent",
    description="Focused chat agent for Refrigerator and Dishwasher parts",
    version="1.0.0"
)


origins = [
    "http://localhost:3000",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,    
    allow_credentials=True,
    allow_methods=["*"],      
    allow_headers=["*"],      
)


@app.get("/")
def home():
    return {"message": "Welcome to Academate AI's API Layer! Navigate to /docs or /redocs to view the API UI layer"}


app.include_router(chat_router)

if __name__ == "__main__":
    DEBUG = os.getenv('DEBUG') == 'True'
    app.run(debug=DEBUG)
