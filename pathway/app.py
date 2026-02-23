import pathway as pw
from pathway.debug import table_to_pandas


# 1️⃣ Define a schema
class TrafficSchema(pw.Schema):
    road_id: str
    vehicle_count: int


# 2️⃣ Create a dummy data stream
traffic_stream = pw.debug.table_from_rows(
    schema=TrafficSchema,
    rows=[
        ("NH-48", 10),
        ("NH-48", 15),
        ("MG-Road", 7),
        ("MG-Road", 12),
    ],
)


# 3️⃣ Simple transformation (business logic)
# Example: flag high traffic roads
processed = traffic_stream.select(
    traffic_stream.road_id,
    traffic_stream.vehicle_count,
    is_congested=traffic_stream.vehicle_count > 10,
)


# 4️⃣ Output (for now, just print)
print(table_to_pandas(processed))


# 5️⃣ Run Pathway
pw.run()
