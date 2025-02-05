
from apify_client import ApifyClient

import os
import duckdb
import polars as pl

from dotenv import load_dotenv

load_dotenv()

dataset_id = 'gNcf77u0UikBXXtf7'

client = ApifyClient()

items = client.dataset(dataset_id).get_items_as_bytes()
dataset = pl.read_json(items)

# db = duckdb.read_json(items.decode('utf-8'))
# df = pl.read(items.decode('utf-8'))

# print(dataset)
# print(duckdb.sql("SELECT * FROM dataset").fetchall())
print(duckdb.sql("SELECT * FROM dataset WHERE city = 'Arverne'").fetchall())

print(duckdb.sql("SELECT COUNT(*) FROM dataset").fetchall())