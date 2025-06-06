"""Test script for user module."""

import asyncio

import pytest

from src.mongo import db, get_document, get_documents, has_document, set_document

collection = db.get_collection("test-user")


async def setup_async() -> None:
    """Execute before start running any tests."""
    await collection.drop()
    assert await collection.count_documents({}) == 0


@pytest.fixture(autouse=True)
def setup_module() -> None:
    """Execute before start running any tests."""
    asyncio.get_event_loop().run_until_complete(setup_async())


def _get_doc() -> dict:
    return {"doc_id": 777}


def _get_docs() -> list[dict]:
    return [
        {"doc_id": 777},
        {"doc_id": 778},
        {"doc_id": 779},
    ]


@pytest.mark.asyncio
async def test_has_document() -> None:
    """Test has_document() function."""
    assert not await has_document(collection, _get_doc())

    await collection.insert_one(_get_doc())

    assert await has_document(collection, _get_doc())


@pytest.mark.asyncio
async def test_get_document() -> None:
    """Test get_document() function."""
    assert await get_document(collection, _get_doc()) is None

    await collection.insert_one(_get_doc())

    result: dict = await get_document(collection, _get_doc())
    result.pop("_id")

    assert result == _get_doc()


@pytest.mark.asyncio
async def test_get_documents() -> None:
    """Test get_documents() function."""
    assert await get_document(collection, _get_doc()) is None

    await collection.insert_many(_get_docs())

    results = await get_documents(collection, {})
    for result in results:
        result.pop("_id")

    assert results == _get_docs()


@pytest.mark.asyncio
async def test_set_document() -> None:
    """Test set_document function."""
    new_doc = _get_doc()
    new_doc["new"] = True

    await set_document(collection, _get_doc(), new_doc)

    result: dict = await collection.find_one(_get_doc())
    result.pop("_id")

    assert result == new_doc


if __name__ == "__main__":
    pytest.main()
