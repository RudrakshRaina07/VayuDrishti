import mysql.connector

try:
    db = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="Rudraksh@1234",
        port=3306
    )

    print("✅ MySQL Connected Successfully!")

except Exception as e:
    print("❌ Error:", e)
