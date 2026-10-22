from fastapi import FastAPI

app = FastAPI(
    title="DayLoop Backend",
    description="API backend for the DayLoop Kalagedihena local tourism planner",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to DayLoop Backend API!"}