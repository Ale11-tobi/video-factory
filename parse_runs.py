import json
with open('runs.json', 'r', encoding='utf-8-sig') as f:
    d = json.load(f)
if not d.get('workflow_runs'):
    print("No runs found")
else:
    run = d['workflow_runs'][0]
    print(f"ID: {run['id']}, Status: {run['status']}, Conclusion: {run['conclusion']}")
