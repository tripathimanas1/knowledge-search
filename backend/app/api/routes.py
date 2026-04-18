import subprocess
from fastapi import FastAPI

app = FastAPI(title="Knowledge Search API")

def get_git_commit():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, Exception):
        return "dev"

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "0.1.0",
        "commit": get_git_commit()
    }
