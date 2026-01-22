from fastapi import FastAPI
import uvicorn

app = FastAPI(title="inventory-service")

@app.get("/")
def read_root():
    return {"message": "inventory-service is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "inventory-service"}


@app.get("/test")
def test():
    return {"test": "OK", "service": "inventory-service"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
