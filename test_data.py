import json
try:
    with open('data/live_report.json', 'r') as f:
        data = json.load(f)
    print('File loads successfully')
    print(f'Population: {data.get("population", {}).get("total_organisms", "N/A")}')
    print(f'Timestamp: {data.get("timestamp", "N/A")}')
    print(f'Keys: {list(data.keys())}')
except Exception as e:
    print(f'Error: {e}')
