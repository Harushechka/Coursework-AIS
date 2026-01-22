from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import uvicorn

app = FastAPI(
    title="API Gateway", 
    description="Unified API Gateway for Autosalon microservices",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs from environment
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8000")
FINANCING_SERVICE_URL = os.getenv("FINANCING_SERVICE_URL", "http://financing-service:8000")
INSURANCE_SERVICE_URL = os.getenv("INSURANCE_SERVICE_URL", "http://insurance-service:8000")
CUSTOMER_SERVICE_URL = os.getenv("CUSTOMER_SERVICE_URL", "http://customer-service:8000")
VEHICLE_SERVICE_URL = os.getenv("VEHICLE_SERVICE_URL", "http://vehicle-catalog-service:8000")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory-service:8000")
SALES_SERVICE_URL = os.getenv("SALES_SERVICE_URL", "http://sales-service:8000")
PRICING_SERVICE_URL = os.getenv("PRICING_SERVICE_URL", "http://pricing-discount-service:8000")

@app.get("/")
async def read_root():
    """Main endpoint"""
    return {
        "message": "Auto Dealership API Gateway",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "services": "/services",
            "auth": "/auth/*",
            "customers": "/customers/*",
            "vehicles": "/vehicles/*",
            "inventory": "/inventory/*",
            "orders": "/orders/*",
            "pricing": "/pricing/*",
            "payment": "/payment/*",
            "financing": "/financing/*",
            "insurance": "/insurance/*"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "api-gateway"}

@app.get("/services")
async def list_services():
    """List all available services"""
    services = {
        "auth": AUTH_SERVICE_URL,
        "payment": PAYMENT_SERVICE_URL,
        "financing": FINANCING_SERVICE_URL,
        "insurance": INSURANCE_SERVICE_URL,
        "customers": CUSTOMER_SERVICE_URL,
        "vehicles": VEHICLE_SERVICE_URL,
        "inventory": INVENTORY_SERVICE_URL,
        "sales": SALES_SERVICE_URL,
        "pricing": PRICING_SERVICE_URL,
    }
    
    # Проверяем доступность сервисов
    service_status = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in services.items():
            try:
                response = await client.get(f"{url}/health")
                service_status[name] = {
                    "url": url,
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "port": url.split(":")[-1] if ":" in url else "8000"
                }
            except:
                service_status[name] = {
                    "url": url,
                    "status": "unavailable",
                    "port": url.split(":")[-1] if ":" in url else "8000"
                }
    
    return {
        "gateway": "running",
        "services": service_status
    }

# Simple proxy endpoints
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_handler(request: Request, path: str):
    """Simple proxy handler for testing"""
    
    # Don't proxy health and services
    if path in ["health", "services", ""]:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Endpoint /{path} should be handled by gateway itself"}
        )
    
    # Map to services
    service_map = {
        "auth": AUTH_SERVICE_URL,
        "payment": PAYMENT_SERVICE_URL,
        "financing": FINANCING_SERVICE_URL,
        "insurance": INSURANCE_SERVICE_URL,
        "customers": CUSTOMER_SERVICE_URL,
        "vehicles": VEHICLE_SERVICE_URL,
        "inventory": INVENTORY_SERVICE_URL,
        "orders": SALES_SERVICE_URL,
        "sales": SALES_SERVICE_URL,
        "pricing": PRICING_SERVICE_URL,
    }
    
    # Find service
    target_service = None
    target_path = path
    
    for prefix, url in service_map.items():
        if path.startswith(prefix + "/") or path == prefix:
            target_service = url
            if path != prefix:
                target_path = path[len(prefix)+1:]  # Remove prefix
            else:
                target_path = ""
            break
    
    if not target_service:
        return JSONResponse(
            status_code=404,
            content={"detail": f"No service found for path: {path}"}
        )
    
    # Forward request
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            target_url = f"{target_service}/{target_path}" if target_path else target_service
            
            # Prepare headers
            headers = dict(request.headers)
            headers.pop("host", None)
            
            # Forward
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=await request.body(),
                params=request.query_params
            )
            
            return JSONResponse(
                status_code=response.status_code,
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                headers=dict(response.headers)
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=502,
            content={"detail": f"Service error: {str(e)}"}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)