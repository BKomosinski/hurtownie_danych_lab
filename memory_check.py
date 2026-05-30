import clickhouse_connect

client = clickhouse_connect.get_client(host='localhost', port=8123, username='admin', password='admin')

# --- ANALIZA ZAJĘTOŚCI DYSKU ---
print("\n--- ZAJĘTOŚĆ DYSKU (CLICKHOUSE) ---")
query = """
SELECT 
    table,
    formatReadableSize(sum(data_uncompressed_bytes)) AS uncompressed_size,
    formatReadableSize(sum(data_compressed_bytes)) AS compressed_size_on_disk,
    round(sum(data_uncompressed_bytes) / sum(data_compressed_bytes), 2) AS compression_ratio
FROM system.parts 
WHERE table = 'final_table' 
GROUP BY table
"""
result = client.query(query)
print(f"Tabela: {result.result_rows[0][0]}")
print(f"Rozmiar przed kompresją: {result.result_rows[0][1]}")
print(f"Rozmiar na dysku (skompresowane): {result.result_rows[0][2]}")
print(f"Współczynnik kompresji: {result.result_rows[0][3]}x")