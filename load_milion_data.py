import clickhouse_connect
import random
from datetime import datetime, timedelta

# 1. Połączenie z bazą (używamy danych z Twojego Docker Compose)
client = clickhouse_connect.get_client(
    host='localhost',
    port=8123,
    username='admin',
    password='admin'
)

print("Połączono z ClickHouse!")

# 2. Upewnij się, że tabela istnieje
client.command('''
CREATE TABLE IF NOT EXISTS million_test (
    id UInt64,
    val Float64,
    category String,
    timestamp DateTime
) ENGINE = MergeTree()
ORDER BY id
''')

# 3. Generowanie i wrzucanie miliona rekordów w paczkach
total_records = 1_000_000
batch_size = 100_000  # Optymalna wielkość paczki

print(f"Rozpoczynam ładowanie {total_records} rekordów...")

for i in range(0, total_records, batch_size):
    data = []
    for j in range(i, i + batch_size):
        data.append([
            j, 
            random.uniform(0, 1000), 
            random.choice(['A', 'B', 'C', 'D']),
            datetime.now() - timedelta(seconds=random.randint(0, 1000000))
        ])
    
    # Wrzucanie paczki
    client.insert('million_test', data, column_names=['id', 'val', 'category', 'timestamp'])
    print(f"Wrzucono: {j + 1}/{total_records}")

print("Sukces! Dane są w bazie.")