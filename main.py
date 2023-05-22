from fastapi import FastAPI, BackgroundTasks, Body
import asyncio
import subprocess
import uvicorn
import os

app = FastAPI()
script_path = os.path.join(os.path.dirname(__file__), "spider")
process_script = []
script_list = []

@app.get("/")
async def index():
    return {"message": "Hello World"}


@app.get("/script_list")
async def get_script():
    global script_list
    script_list = []
    for root, dirs, files in os.walk(script_path):
        for file in files:
            if file.endswith(".py"):
                script_list.append({"file_path": os.path.join(root, file), "file_name": file})
    script_list_name = [item["file_name"] for item in script_list]
    return script_list_name


@app.post("/run_script")
async def run_script(file_name: str = Body(..., embed=True), background_tasks: BackgroundTasks = BackgroundTasks()):
    try:
        for item in script_list:
            if item["file_name"] == file_name:
                file_path = item["file_path"]
                background_tasks.add_task(run, file_path)
                return {"message": "脚本启动成功"}
        return {"message": "脚本不存在"}
    except Exception as e:
        return {"message": "脚本执行出错", "error": str(e)}


async def run(file_path):
    try:
        # 启动脚本并捕获输出
        process = await asyncio.create_subprocess_shell(
            f"python {file_path}", stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        process_script.append({"file_path": file_path, "process": process, "status": "running", "returncode": None, "output": None})
        await wait_for_script_completion(file_path, process)
    except Exception as e:
        return {"message": "脚本执行出错", "error": str(e)}


async def wait_for_script_completion(file_path: str, process: asyncio.subprocess.Process):
    stdout, stderr = await process.communicate()
    if stdout:
        output = stdout.decode()
    elif stderr:
        output = stderr.decode()
    else:
        output = ""
    await update_script_status(file_path, process.returncode, output)


async def update_script_status(file_path: str, returncode: int, output: str):
    for item in process_script:
        if item["file_path"] == file_path:
            item["status"] = "done"
            item["returncode"] = returncode
            item["output"] = output
            break


@app.get("/status")
async def get_status(file_path: str = Body(..., embed=True)):
    for item in process_script:
        if item["file_path"] == file_path:
            return {"status": item["status"], "returncode": item["returncode"], "output": item["output"]}
    return {"message": "脚本未执行"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
