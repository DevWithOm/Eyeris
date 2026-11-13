from pathlib import Path
root=Path(__file__).resolve().parents[1]
required=['README.md','.gitignore','frontend/package.json','backend/app/main.py','docs/integration_contract.md']
missing=[p for p in required if not (root/p).exists()]
if missing: raise SystemExit(f'Missing: {missing}')
print('Scaffold validation passed.')
