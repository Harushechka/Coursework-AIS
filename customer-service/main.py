from fastapi import FastAPI
import uvicorn

app = FastAPI(title="customer-service")

@app.get("/")
def read_root():
    return {"message": "customer-service is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "customer-service"}

# Тестовый эндпоинт
@app.get("/test")
def test():
    return {"test": "OK", "service": "customer-service"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
