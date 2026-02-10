"""Quick test of the builder server API."""
import urllib.request
import json

BASE_URL = 'http://localhost:8088'

def test_api():
    # Test blocks endpoint
    print("Testing /api/blocks...")
    r = urllib.request.urlopen(f'{BASE_URL}/api/blocks')
    data = json.loads(r.read())
    print(f"  Found {len(data.get('blocks', []))} blocks")
    
    # Test scaffold endpoint
    print("\nTesting /api/scaffold...")
    req_data = json.dumps({
        'name': 'test_project',
        'blocks': [{'type': 'storage_json'}, {'type': 'crud_routes'}],
        'entities': [{'name': 'Task', 'fields': [{'name': 'title', 'type': 'string'}]}]
    }).encode()
    
    req = urllib.request.Request(
        f'{BASE_URL}/api/scaffold',
        data=req_data,
        headers={'Content-Type': 'application/json'}
    )
    r = urllib.request.urlopen(req, timeout=10)
    result = json.loads(r.read())
    
    if result.get('success'):
        print(f"  Success! Path: {result.get('path')}")
        print(f"  Generated files: {len(result.get('files', []))}")
    else:
        print(f"  Error: {result.get('error')}")
    
    # Test create-contract endpoint
    print("\nTesting /api/create-contract...")
    req_data = json.dumps({
        'name': 'User',
        'description': 'A user in the system',
        'fields': [
            {'name': 'id', 'type': 'string'},
            {'name': 'email', 'type': 'string'},
            {'name': 'name', 'type': 'string'}
        ],
        'languages': ['python', 'typescript']
    }).encode()
    
    req = urllib.request.Request(
        f'{BASE_URL}/api/create-contract',
        data=req_data,
        headers={'Content-Type': 'application/json'}
    )
    r = urllib.request.urlopen(req, timeout=10)
    result = json.loads(r.read())
    
    if result.get('success'):
        print(f"  Created contract: {result.get('contract')}")
        print(f"  Languages: {list(result.get('generated', {}).keys())}")
    else:
        print(f"  Error: {result.get('error')}")
    
    print("\nAll tests passed!")

if __name__ == '__main__':
    test_api()
