import subprocess, sys
subprocess.run([sys.executable, '-m', 'uvicorn', 'backend.app.main:app', '--reload'], check=True)
