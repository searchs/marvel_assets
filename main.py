from fastapi import FastAPI, HTTPException, Query

import httpx
import hashlib
import os
import time

from loguru import logger


app = FastAPI(title="Marvel API With FastAPI", version="1.0.0")

# Please replace these with your Marvel API keys obtained from developer.marvel.com
PUBLIC_KEY = os.environ.get("marvel_pubkey", None)
PRIVATE_KEY = os.environ.get("marvel_privkey", None)
BASE_URL = "https://gateway.marvel.com:443/v1/public"
BATCH_SIZE = 50  # Number of characters to retrieve per request - for manaaging respoinse size at least for now.


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
    return {
        "ts": ts,
        "apikey": PUBLIC_KEY,
        "hash": generate_marvel_hash(ts),
        "orderBy": "name",
    }


@app.get("/")
def base():
    """Base endpoint to confirm the API is running.

    Returns:
        dict: A message indicating the Marvel API app status and version.
    """
    return {"message": "Marvel API app", "version:": "0.0.1"}


@app.get("/characters")
async def get_characters_with_info(limit: int = 10, offset: int = 0):
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
        logger.info("looks like we did not get the right result.")
        raise HTTPException(
            status_code=response.status_code, detail="Failed to fetch characters"
        )

    return response.json()


# async def fetch_character_batch(limit: int, offset: int, name: str = None):
#     """Fetch a batch of characters from the Marvel API.

#     Args:
#         limit (int): The number of characters to fetch in this batch.
#         offset (int): The starting index for the batch.
#         name (str, optional): The name of the character to search for. Defaults to None.

#     Returns:
#         list: A list of characters with their name and comic count.
#     """
#     url = f"{BASE_URL}/characters"
#     params = get_auth_params()
#     params.update({"limit": limit, "offset": offset})
#     # TODO: use a wider search as some names have  extra info
#     if name:
#         params["name"] = name

#     async with httpx.AsyncClient() as client:
#         response = await client.get(url, params=params)

#     if response.status_code != 200:
#         raise HTTPException(
#             status_code=response.status_code,
#             detail="Failed to fetch characters",
#         )

#     data = response.json()
#     return [
#         {"name": char["name"], "comics_count": char["comics"]["available"]}
#         for char in data["data"]["results"]
#     ]

import re
from typing import List, Dict
from fastapi import FastAPI, HTTPException
import httpx


async def fetch_character_batch(
    limit: int, offset: int, name: str = None
) -> List[Dict]:
    """Fetch a batch of characters from the Marvel API with flexible name matching.

    Args:
        limit (int): The number of characters to fetch in this batch.
        offset (int): The starting index for the batch.
        name (str, optional): The name pattern to search for. Supports partial matches
            and ignores case and special characters. Defaults to None.

    Returns:
        list: A list of characters with their name and comic count.

    Example matches:
        - "spider" would match "Spider-Man", "Spider-Woman", "Spider-Girl"
        - "spider man" would match "Spider-Man", "Spider-Man (Ultimate)", etc.
        - "peter parker" would match "Peter Parker", "Peter Parker (Ultimate)", etc.
    """
    url = f"{BASE_URL}/characters"
    params = get_auth_params()
    params.update({"limit": limit, "offset": offset})

    if name:
        # Clean and prepare the search pattern
        search_term = name.split()[0]  # Take first word for API search

        # Create regex pattern:
        # 1. Escape special regex characters
        # 2. Replace spaces with flexible whitespace/separator pattern
        # 3. Make the pattern case insensitive
        pattern = re.escape(name)
        pattern = pattern.replace(r"\ ", r"[\s-]*")
        pattern = f"^{pattern}"
        regex = re.compile(pattern, re.IGNORECASE)

        # Use nameStartsWith for broader initial search
        params["nameStartsWith"] = search_term

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to fetch characters",
        )

    data = response.json()
    results = data["data"]["results"]

    # Filter results using regex if name pattern was provided
    if name and results:
        filtered_chars = [
            {"name": char["name"], "comics_count": char["comics"]["available"]}
            for char in results
            if regex.search(char["name"])
        ]
        return filtered_chars
    else:
        return [
            {"name": char["name"], "comics_count": char["comics"]["available"]}
            for char in results
        ]


# Example helper function to clean and standardize character names
def standardize_name(name: str) -> str:
    """Standardize character name for consistent matching.

    Args:
        name (str): The character name to standardize.

    Returns:
        str: Standardized name with consistent formatting.
    """
    # Remove parenthetical information
    name = re.sub(r"\s*\([^)]*\)", "", name)

    # Remove special characters except hyphen
    name = re.sub(r"[^\w\s-]", "", name)

    # Replace multiple spaces/separators with single space
    name = re.sub(r"[\s-]+", " ", name)

    return name.strip()


# Example usage:
async def search_characters(search_name: str, limit: int = 20) -> List[Dict]:
    """Search for characters with flexible name matching.

    Args:
        search_name (str): The name pattern to search for.
        limit (int, optional): Maximum number of results to return. Defaults to 20.

    Returns:
        List[Dict]: List of matching characters with their comic counts.
    """
    try:
        chars = await fetch_character_batch(limit=limit, offset=0, name=search_name)
        return chars
    except HTTPException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"Error searching for character: {e.detail}",
        )


@app.get("/characters_all")
async def get_all_characters_names(
    limit: int = Query(20, ge=1), offset: int = Query(0, ge=0)
):
    """Fetch characters and the quantity of comics in which they appear with pagination.

    Args:
        limit (int, optional): The maximum number of characters to retrieve. Defaults to 100.
        offset (int, optional): The starting index for retrieving characters. Defaults to 0.

    Returns:
        dict: A dictionary where each key is a character name, and the value is the number of comics they appear in.
    """
    characters_comics = {}
    total_retrieved = 0

    while total_retrieved < limit:
        batch_size = min(BATCH_SIZE, limit - total_retrieved)
        batch = await fetch_character_batch(batch_size, offset + total_retrieved)
        total_retrieved += len(batch)

        # Update the results dictionary with character comic count
        for character in batch:
            characters_comics[character["name"]] = character["comics_count"]

        if (
            len(batch) < BATCH_SIZE
        ):  # End loop if fewer items than requested are returned
            break

    return characters_comics


@app.get("/characters/search/{name}")
async def search_characters_endpoint(name: str, limit: int = 20):
    return await search_characters(name, limit)


@app.get("/characters/{character_name}")
async def get_character_by_name(
    character_name: str, limit: int = Query(10, ge=1), offset: int = Query(0, ge=0)
):
    """Fetch comic count for a specific character by name, with pagination.

    Args:
        character_name (str): The name of the character to search for.
        limit (int, optional): The maximum number of results to retrieve. Defaults to 10.
        offset (int, optional): The starting index for retrieving results. Defaults to 0.

    Returns:
        dict: A dictionary where the key is the character's name and the value is the number of comics they appear in.
    """
    characters = await fetch_character_batch(
        limit=limit, offset=offset, name=character_name
    )
    if not characters:
        raise HTTPException(
            status_code=404, detail=f"No character found with name {character_name}"
        )

    return {character["name"]: character["comics_count"] for character in characters}


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
