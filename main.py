from fastapi import FastAPI, HTTPException
import httpx
import hashlib
import os
import time

app = FastAPI(title="Marvel API With FastAPI", version="1.0.0")

# Please replace these with your Marvel API keys obtained from developer.marvel.com
PUBLIC_KEY = os.environ.get("marvel_pubkey", None)
PRIVATE_KEY = os.environ.get("marvel_privkey", None)
BASE_URL = "https://gateway.marvel.com:443/v1/public"


def generate_marvel_hash(ts: str) -> str:
    """Generate a hash for Marvel API authentication.

    Args:
        ts (str): The timestamp for the request.

    Returns:
        str: The generated MD5 hash based on the timestamp, private key, and public key.
    """
    to_hash = f"{ts}{PRIVATE_KEY}{PUBLIC_KEY}"
    return hashlib.md5(to_hash.encode()).hexdigest()


def get_auth_params():
    """Generate authentication parameters for the Marvel API.

    Returns:
        dict: A dictionary with the timestamp, API key, and hash required for authentication.
    """
    ts = str(time.time())
    return {"ts": ts, "apikey": PUBLIC_KEY, "hash": generate_marvel_hash(ts)}


@app.get("/")
def base():
    """Base endpoint to confirm the API is running.

    Returns:
        dict: A message indicating the Marvel API app status and version.
    """
    return {"message": "Marvel API app", "version:": "0.0.1"}


@app.get("/characters")
async def get_characters(limit: int = 10, offset: int = 0):
    """Fetch a list of Marvel characters in async fashion.

    Args:
        limit (int, optional): Number of characters to return. Defaults to 10.
        offset (int, optional): The starting index for the list of characters. Defaults to 0.

    Returns:
        dict: The JSON response containing the list of characters.

    Raises:
        HTTPException: If the request to the Marvel API fails.
    """
    url = f"{BASE_URL}/characters"
    params = get_auth_params()
    params.update({"limit": limit, "offset": offset})

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Failed to fetch characters"
        )

    return response.json()


@app.get("/characters/{character_id}")
async def get_character(character_id: int):
    """Fetch details about a specific Marvel character by ID.

    Args:
        character_id (int): The unique ID of the character.

    Returns:
        dict: The JSON response containing the character's details.

    Raises:
        HTTPException: If the request to the Marvel API fails.
    """
    url = f"{BASE_URL}/characters/{character_id}"
    params = get_auth_params()

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Failed to fetch character"
        )

    return response.json()


@app.get("/comics")
async def get_comics(limit: int = 10, offset: int = 0):
    """Fetch a list of Marvel comics.

    Args:
        limit (int, optional): Number of comics to return. Defaults to 10.
        offset (int, optional): The starting index for the list of comics. Defaults to 0.

    Returns:
        dict: The JSON response containing the list of comics.

    Raises:
        HTTPException: If the request to the Marvel API fails.
    """
    url = f"{BASE_URL}/comics"
    params = get_auth_params()
    params.update({"limit": limit, "offset": offset})

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Failed to fetch comics"
        )

    return response.json()


@app.get("/series")
async def get_series(limit: int = 10, offset: int = 0):
    """Fetch a list of Marvel series.

    Args:
        limit (int, optional): Number of series to return. Defaults to 10.
        offset (int, optional): The starting index for the list of series. Defaults to 0.

    Returns:
        dict: The JSON response containing the list of series.

    Raises:
        HTTPException: If the request to the Marvel API fails.
    """
    url = f"{BASE_URL}/series"
    params = get_auth_params()
    params.update({"limit": limit, "offset": offset})

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Failed to fetch series"
        )

    return response.json()