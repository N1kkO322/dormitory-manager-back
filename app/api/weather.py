import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, status

from ..config import settings

router = APIRouter(prefix="/api/weather", tags=["weather"])

OPENWEATHERMAP_URL = "https://api.openweathermap.org/data/2.5/weather"
REQUEST_TIMEOUT_SECONDS = 10


@router.get("/")
def get_weather():
    if not settings.OPENWEATHERMAP_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenWeatherMap API key is not configured",
        )

    query = urlencode(
        {
            "units": "metric",
            "q": settings.OPENWEATHERMAP_CITY,
            "appid": settings.OPENWEATHERMAP_API_KEY,
            "lang": "ru",
        }
    )
    request = Request(f"{OPENWEATHERMAP_URL}?{query}")

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = "OpenWeatherMap request failed"
        try:
            error_payload = json.loads(exc.read().decode("utf-8"))
            detail = error_payload.get("message", detail)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

        raise HTTPException(status_code=exc.code, detail=detail) from exc
    except URLError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenWeatherMap service is unavailable",
        ) from exc
