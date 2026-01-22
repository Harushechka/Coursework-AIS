from fastapi import FastAPI
import uvicorn

app = FastAPI(title="vehicle-catalog-service")

@app.get("/")
def read_root():
    return {"message": "vehicle-catalog-service is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "vehicle-catalog-service"}

# Тестовый эндпоинт
@app.get("/test")
def test():
    return {"test": "OK", "service": "vehicle-catalog-service"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
