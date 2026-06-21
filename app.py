# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "fastapi",
#   "uvicorn",
#   "pandas",
# ]
# ///

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import List, Optional

app = FastAPI(title="Student Data API")

# Enable CORS for any origin (as required)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Allow requests from anywhere
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the CSV once when the server starts
df = pd.read_csv("students.csv")   # ← change filename if needed

@app.get("/api")
async def get_students(
    class_: Optional[List[str]] = Query(None, alias="class")
):
    data = df.copy()
    
    if class_:
        # Filter by one or more classes
        data = data[data["class"].isin(class_)]
    
    # Return in original CSV order
    students = data.to_dict(orient="records")
    
    return {"students": students}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)