import httpx

print("Testing V2 endpoints...")
try:
    print('GET /api/v1/version ->', httpx.get('http://localhost:8001/api/v1/version').status_code)
    print('GET /api/v2/version ->', httpx.get('http://localhost:8001/api/v2/version').text)
    r = httpx.get('http://localhost:8001/api/v2/collections?tenant=default_tenant&database=default_database')
    print('GET /api/v2/collections ->', r.status_code, r.text[:100])
except Exception as e:
    print(e)
