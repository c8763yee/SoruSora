"""
This script copies all the data from Firestore to MongoDB.
"""

import asyncio
import sys

import firebase_admin
from firebase_admin import credentials
from google.cloud.firestore_v1 import AsyncClient

from motor.motor_asyncio import AsyncIOMotorClient


async def main():
    """
    Main function
    """

    if len(sys.argv) != 2:
        print("Usage: python firestore_to_mongo.py <path/to/service_account.json>")
        sys.exit(1)

    app = firebase_admin.initialize_app(credentials.Certificate(sys.argv[1]))
    firestore = AsyncClient(credentials=app.credential.get_credential(), project=app.project_id)

    mongo = AsyncIOMotorClient().get_database("SoruSora")

    async for firestore_collection in firestore.collections():
        docs = []
        async for doc in firestore_collection.stream():
            docs.append(doc.to_dict())

        await mongo.get_collection(firestore_collection.id).insert_many(docs)


if __name__ == "__main__":
    asyncio.run(main())