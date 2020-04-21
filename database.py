import pymongo as pymongo

client = pymongo.MongoClient("mongodb+srv://dbAdmin:dbAdminpass@cluster0-i7xdc.gcp.mongodb.net/test?retryWrites=true&w=majority")
db = client.main


Workers = db.Workers
Locations = db.Locations
Users = db.Users
History = db.History
CustomTables = db.CustomTables
Metadata = db.Metadata
TimeHandler = db.TimeHandler