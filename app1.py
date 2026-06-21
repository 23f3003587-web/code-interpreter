# app1.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Batch Sentiment Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SentimentRequest(BaseModel):
    sentences: List[str]

class SentimentResult(BaseModel):
    sentence: str
    sentiment: str

class SentimentResponse(BaseModel):
    results: List[SentimentResult]

def determine_sentiment(sentence: str) -> str:
    text = " " + sentence.lower() + " "
    
    # Strong positive words
    happy_words = [
        "love", "loving", "great", "happy", "good", "excellent", "wonderful", "fantastic", 
        "amazing", "awesome", "best", "perfect", "joy", "delight", "excited", "pleased", 
        "glad", "nice", "beautiful", "brilliant", "outstanding", "superb", "terrific", 
        "fabulous", "incredible", "marvelous", "enjoy", "like", "adore"
    ]
    
    # Strong negative words
    sad_words = [
        "sad", "terrible", "bad", "awful", "horrible", "hate", "worst", "poor", 
        "disappoint", "angry", "upset", "miserable", "frustrated", "annoy", "depress",
        "suck", "pain", "horrific", "disgusting", "pathetic", "useless", "trash", 
        "stupid", "idiot", "hated", "cry", "angrily"
    ]
    
    happy_score = sum(1 for word in happy_words if " " + word in text)
    sad_score = sum(1 for word in sad_words if " " + word in text)
    
    # Bonus for common patterns
    if any(word in text for word in ["can't", "not good", "not great", "not happy", "don't like"]):
        sad_score += 2
    
    if happy_score > sad_score:
        return "happy"
    elif sad_score > happy_score:
        return "sad"
    else:
        # Tie-breaker using more subtle indicators
        if any(word in text for word in ["excellent", "amazing", "love", "happy", "great"]):
            return "happy"
        if any(word in text for word in ["terrible", "bad", "hate", "sad", "worst"]):
            return "sad"
        return "neutral"

@app.get("/")
async def root():
    return {"status": "ok", "message": "Sentiment API is running"}

@app.post("/")
async def sentiment_root(request: SentimentRequest):
    return await analyze_sentiment(request)

@app.post("/sentiment", response_model=SentimentResponse)
async def analyze_sentiment(request: SentimentRequest):
    if not request.sentences:
        raise HTTPException(status_code=400, detail="sentences list cannot be empty")
    
    results = [SentimentResult(sentence=s, sentiment=determine_sentiment(s)) for s in request.sentences]
    return SentimentResponse(results=results)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)