from fastapi import APIRouter, HTTPException, Depends
from app.core.auth import require_role, get_current_user
from typing import Dict, Any, List
import subprocess
import os
import psutil
from pathlib import Path

router = APIRouter()

BOT_PATHS = {
    "telegram": "telegram_bot",
    "whatsapp": "whatsapp_bot"
}

PID_DIR = Path("/tmp/telecom_bots")


def get_bot_status(bot_type: str) -> Dict[str, Any]:
    pid_file = PID_DIR / f"{bot_type}.pid"

    if not pid_file.exists():
        return {
            "type": bot_type,
            "status": "stopped",
            "pid": None,
            "running": False
        }

    try:
        pid = int(pid_file.read_text().strip())
        if psutil.pid_exists(pid):
            process = psutil.Process(pid)
            return {
                "type": bot_type,
                "status": "running",
                "pid": pid,
                "running": True,
                "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
                "cpu_percent": process.cpu_percent(interval=0.1),
                "started_at": process.create_time()
            }
        else:
            pid_file.unlink()
            return {
                "type": bot_type,
                "status": "stopped",
                "pid": None,
                "running": False
            }
    except Exception as e:
        return {
            "type": bot_type,
            "status": "error",
            "error": str(e),
            "running": False
        }


def get_project_root() -> str:
    current_file = Path(__file__)
    return str(current_file.parent.parent.parent.parent.parent)


def start_bot(bot_type: str) -> Dict[str, Any]:
    if bot_type not in BOT_PATHS:
        raise ValueError(f"Unknown bot type: {bot_type}")

    status = get_bot_status(bot_type)
    if status["running"]:
        raise HTTPException(status_code=400, detail=f"Bot {bot_type} is already running")

    project_root = get_project_root()
    bot_path = os.path.join(project_root, BOT_PATHS[bot_type])

    PID_DIR.mkdir(exist_ok=True)
    pid_file = PID_DIR / f"{bot_type}.pid"

    try:
        if bot_type == "telegram":
            process = subprocess.Popen(
                ["python3", "bot.py"],
                cwd=bot_path,
                stdout=open(os.path.join(bot_path, "bot.log"), "a"),
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
        elif bot_type == "whatsapp":
            process = subprocess.Popen(
                ["node", "bot.js"],
                cwd=bot_path,
                stdout=open(os.path.join(bot_path, "bot.log"), "a"),
                stderr=subprocess.STDOUT,
                start_new_session=True
            )

        pid_file.write_text(str(process.pid))

        return {
            "type": bot_type,
            "status": "started",
            "pid": process.pid,
            "message": f"Bot {bot_type} started successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start bot: {str(e)}")


def stop_bot(bot_type: str) -> Dict[str, Any]:
    status = get_bot_status(bot_type)

    if not status["running"]:
        raise HTTPException(status_code=400, detail=f"Bot {bot_type} is not running")

    try:
        pid = status["pid"]
        process = psutil.Process(pid)
        process.terminate()

        try:
            process.wait(timeout=5)
        except psutil.TimeoutExpired:
            process.kill()

        pid_file = PID_DIR / f"{bot_type}.pid"
        if pid_file.exists():
            pid_file.unlink()

        return {
            "type": bot_type,
            "status": "stopped",
            "message": f"Bot {bot_type} stopped successfully"
        }
    except psutil.NoSuchProcess:
        pid_file = PID_DIR / f"{bot_type}.pid"
        if pid_file.exists():
            pid_file.unlink()
        return {
            "type": bot_type,
            "status": "stopped",
            "message": f"Bot {bot_type} was already stopped"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop bot: {str(e)}")


@router.get("/bots")
async def list_bots(
    user: Dict[str, Any] = Depends(require_role(["admin", "supervisor"]))
) -> List[Dict[str, Any]]:
    bots = []
    for bot_type in BOT_PATHS.keys():
        status = get_bot_status(bot_type)
        bots.append(status)

    return bots


@router.get("/bots/{bot_type}/status")
async def get_bot_status_endpoint(
    bot_type: str,
    user: Dict[str, Any] = Depends(require_role(["admin", "supervisor"]))
) -> Dict[str, Any]:
    if bot_type not in BOT_PATHS:
        raise HTTPException(status_code=404, detail=f"Bot type {bot_type} not found")

    return get_bot_status(bot_type)


@router.post("/bots/{bot_type}/start")
async def start_bot_endpoint(
    bot_type: str,
    user: Dict[str, Any] = Depends(require_role(["admin"]))
) -> Dict[str, Any]:
    if bot_type not in BOT_PATHS:
        raise HTTPException(status_code=404, detail=f"Bot type {bot_type} not found")

    return start_bot(bot_type)


@router.post("/bots/{bot_type}/stop")
async def stop_bot_endpoint(
    bot_type: str,
    user: Dict[str, Any] = Depends(require_role(["admin"]))
) -> Dict[str, Any]:
    if bot_type not in BOT_PATHS:
        raise HTTPException(status_code=404, detail=f"Bot type {bot_type} not found")

    return stop_bot(bot_type)


@router.post("/bots/{bot_type}/restart")
async def restart_bot_endpoint(
    bot_type: str,
    user: Dict[str, Any] = Depends(require_role(["admin"]))
) -> Dict[str, Any]:
    if bot_type not in BOT_PATHS:
        raise HTTPException(status_code=404, detail=f"Bot type {bot_type} not found")

    status = get_bot_status(bot_type)
    if status["running"]:
        stop_bot(bot_type)
        import time
        time.sleep(1)

    return start_bot(bot_type)

