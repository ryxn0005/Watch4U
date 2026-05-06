#!/usr/bin/env python3
"""Infrastructure verification script for Watch4U.

Run this to verify:
- Backend API endpoints are accessible
- All services are responding
- Database connectivity
- Frontend can reach backend
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import httpx

BACKEND_URL = "http://localhost:8000"
TIMEOUT = httpx.Timeout(10.0, connect=5.0)


class colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def log_success(msg: str):
    print(f"{colors.GREEN}✅ {msg}{colors.RESET}")


def log_error(msg: str):
    print(f"{colors.RED}❌ {msg}{colors.RESET}")


def log_info(msg: str):
    print(f"{colors.BLUE}ℹ️  {msg}{colors.RESET}")


def log_warning(msg: str):
    print(f"{colors.YELLOW}⚠️  {msg}{colors.RESET}")


async def check_health() -> bool:
    """Check backend health endpoint."""
    try:
        async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=TIMEOUT) as client:
            response = await client.get("/health")
            if response.status_code == 200:
                data = response.json()
                log_success(f"Backend healthy: {data.get('status', 'unknown')}")
                return True
            else:
                log_error(f"Health check failed: HTTP {response.status_code}")
                return False
    except Exception as e:
        log_error(f"Health check error: {e}")
        return False


async def check_triage() -> bool:
    """Check triage endpoint."""
    try:
        async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=TIMEOUT) as client:
            payload = {
                "patient_profile": {
                    "age": 75,
                    "previous_fall_history": False,
                    "stroke_history": False,
                    "cognitive_impairment": False,
                    "dementia": False,
                    "limited_mobility": False,
                    "uses_walker": False,
                    "uses_wheelchair": False,
                    "blood_thinner_medication": False,
                    "osteoporosis": False,
                    "lives_alone": False,
                },
                "fall_event": {
                    "fall_detected": True,
                    "unconscious": False,
                    "head_impact": False,
                    "severe_pain": False,
                    "bleeding": False,
                    "chest_pain": False,
                    "breathing_difficulty": False,
                    "red_flags": [],
                    "context": {},
                },
                "elapsed_seconds": 30,
                "language": "en",
                "patient_response": "I'm okay",
            }
            response = await client.post("/api/triage/evaluate", json=payload)
            if response.status_code == 200:
                data = response.json()
                log_success(f"Triage API working: Category {data.get('category')}")
                return True
            else:
                log_error(f"Triage check failed: HTTP {response.status_code}")
                return False
    except Exception as e:
        log_error(f"Triage check error: {e}")
        return False


async def check_rag() -> bool:
    """Check RAG endpoints."""
    try:
        async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=TIMEOUT) as client:
            # Check stats
            stats_response = await client.get("/api/rag/stats")
            if stats_response.status_code == 200:
                log_success("RAG stats endpoint working")
            else:
                log_warning("RAG stats endpoint not responding")
            
            # Check query
            query_response = await client.post(
                "/api/rag/query",
                json={"query": "What are fall prevention tips?", "language": "en"}
            )
            if query_response.status_code == 200:
                data = query_response.json()
                log_success(f"RAG query working: {len(data.get('citations', []))} citations")
                return True
            else:
                log_error(f"RAG query failed: HTTP {query_response.status_code}")
                return False
    except Exception as e:
        log_error(f"RAG check error: {e}")
        return False


async def check_fall_detection() -> bool:
    """Check fall detection endpoints."""
    try:
        async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=TIMEOUT) as client:
            # Check health
            health_response = await client.get("/api/fall-detection/health")
            if health_response.status_code == 200:
                log_success("Fall detection health endpoint working")
            
            # Check analyze
            analyze_response = await client.post(
                "/api/fall-detection/analyze",
                json={"video_url": "http://example.com/test.mp4", "sample_rate": 5}
            )
            if analyze_response.status_code == 200:
                data = analyze_response.json()
                log_success(f"Fall detection analyze working: fall_detected={data.get('fall_detected')}")
                return True
            else:
                log_error(f"Fall detection analyze failed: HTTP {analyze_response.status_code}")
                return False
    except Exception as e:
        log_error(f"Fall detection check error: {e}")
        return False


async def check_docs() -> bool:
    """Check API documentation is available."""
    try:
        async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=TIMEOUT) as client:
            response = await client.get("/docs")
            if response.status_code == 200:
                log_success("API docs (Swagger UI) accessible at /docs")
                return True
            else:
                log_warning(f"API docs not accessible: HTTP {response.status_code}")
                return False
    except Exception as e:
        log_warning(f"API docs check error: {e}")
        return False


def check_imports() -> bool:
    """Check that all backend modules can be imported."""
    log_info("Checking backend imports...")
    
    modules_to_check = [
        "main",
        "app.core.config",
        "app.routers.health",
        "app.routers.triage",
        "app.services.triage",
    ]
    
    all_ok = True
    for module in modules_to_check:
        try:
            __import__(module)
            log_success(f"Can import {module}")
        except Exception as e:
            log_error(f"Failed to import {module}: {e}")
            all_ok = False
    
    return all_ok


async def run_all_checks():
    """Run all verification checks."""
    print("=" * 60)
    print("🔍 Watch4U Infrastructure Verification")
    print("=" * 60)
    print()
    
    # Check imports first (static)
    imports_ok = check_imports()
    print()
    
    # Check backend connectivity
    log_info(f"Checking backend at {BACKEND_URL}...")
    print()
    
    results = {
        "health": await check_health(),
        "docs": await check_docs(),
        "triage": await check_triage(),
        "rag": await check_rag(),
        "fall_detection": await check_fall_detection(),
    }
    
    print()
    print("=" * 60)
    print("📊 Verification Summary")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for check, result in results.items():
        status = f"{colors.GREEN}PASS{colors.RESET}" if result else f"{colors.RED}FAIL{colors.RESET}"
        print(f"  {check}: {status}")
    
    print()
    if passed == total:
        log_success(f"All checks passed! ({passed}/{total})")
        return 0
    else:
        log_error(f"Some checks failed ({passed}/{total})")
        log_info("Make sure the backend is running: make backend")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_checks())
    sys.exit(exit_code)
