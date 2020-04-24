import pymongo as pymongo

client = pymongo.MongoClient("mongodatabase_link")
db = client.main

Workers = db.Workers
Locations = db.Locations
History = db.History
TimeHandler = db.TimeHandler
