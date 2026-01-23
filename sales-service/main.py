from fastapi import FastAPI
import uvicorn

app = FastAPI(title="sales-service")

@app.get("/")
def read_root():
    return {"message": "sales-service is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "sales-service"}

# Тестовый эндпоинт
@app.get("/test")
def test():
    return {"test": "OK", "service": "sales-service"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
