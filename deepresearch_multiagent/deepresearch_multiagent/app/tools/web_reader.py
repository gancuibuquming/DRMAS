from typing import Optional

import httpx


async def fetch_text(url: str, *, timeout: int = 20) -> Optional[str]:
    """Very small web reader placeholder.

    For production use, replace this with readability extraction, PDF parsing,
    browser rendering, boilerplate removal, and content caching.
    """
    if url.startswith("mock://") or url.startswith("kb://"):
        return None

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            ctype = response.headers.get("content-type", "")
            if "text" not in ctype and "html" not in ctype and "json" not in ctype:
                return None
            return response.text[:20000]
    except Exception:
        return None
