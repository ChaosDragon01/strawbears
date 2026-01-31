import asyncio
from pymongo import AsyncMongoClient

async def main():
    try:
        uri = "mongodb://localhost:27017/"
        client = AsyncMongoClient(uri)

        await client.admin.command("ping")
        print("Connected successfully")

        database = client["test_database"]        

        await database.create_collection("test_collection")

        await database.test_collection.insert_one({"name": "test", "value": 123})
            
        document = await database.test_collection.find_one({"name": "test"})
        print("Retrieved document:", document)


        await client.close()

    except Exception as e:
        raise Exception(
            "The following error occurred: ", e)

asyncio.run(main())