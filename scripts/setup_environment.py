from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for name in ['storage','data','artifacts']:
    (ROOT/name).mkdir(exist_ok=True)
print('Project directories checked.')
