from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import pty
import asyncio
import logging
import signal
import json
import fcntl
import termios
import struct

# Timestamped logging for production debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
async def get_index():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.websocket("/ws")
async def terminal_websocket(websocket: WebSocket):
    await websocket.accept()

    (child_pid, fd) = pty.fork()

    if child_pid == 0:
        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        if os.path.exists("/workspace"):
            os.chdir("/workspace")
        os.execvpe("/bin/bash", ["/bin/bash"], env)
    else:
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue()

        def on_pty_read():
            try:
                data = os.read(fd, 16384)
                if data:
                    queue.put_nowait(data)
                else:
                    queue.put_nowait(None)
            except OSError as e:
                # Ignore EIO (errno=5) — normal PTY closure
                if e.errno != 5:
                    logger.error(f"PTY read error: {e}")
                loop.remove_reader(fd)
                queue.put_nowait(None)

        loop.add_reader(fd, on_pty_read)

        async def send_to_websocket():
            try:
                while True:
                    data = await queue.get()
                    if data is None:
                        break

                    # Coalesce multiple chunks to reduce frame count
                    chunks = [data]
                    while not queue.empty():
                        extra = queue.get_nowait()
                        if extra is None:
                            queue.put_nowait(None)
                            break
                        chunks.append(extra)

                    await websocket.send_bytes(b"".join(chunks))
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected during send")
            except Exception as e:
                logger.error(f"Error sending to websocket: {e}")
            finally:
                logger.info("WebSocket sender task ending")

        sender_task = asyncio.create_task(send_to_websocket())

        try:
            while True:
                message = await websocket.receive()

                if message.get("bytes") is not None:
                    os.write(fd, message["bytes"])
                elif message.get("text") is not None:
                    try:
                        data = json.loads(message["text"])
                        if data.get("type") == "resize":
                            rows = data.get("rows", 24)
                            cols = data.get("cols", 80)
                            size = struct.pack("HHHH", rows, cols, 0, 0)
                            fcntl.ioctl(fd, termios.TIOCSWINSZ, size)
                            logger.info(f"Resized terminal to {cols}x{rows}")
                    except json.JSONDecodeError:
                        logger.warning(f"Non-JSON text: {message['text']}")
                elif message.get("type") == "websocket.disconnect":
                    break
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"Error in websocket loop: {e}")
        finally:
            loop.remove_reader(fd)
            sender_task.cancel()
            try:
                await sender_task
            except asyncio.CancelledError:
                pass
            try:
                os.close(fd)
            except OSError:
                pass
            try:
                os.kill(child_pid, signal.SIGTERM)
                await asyncio.sleep(0.1)
                os.kill(child_pid, signal.SIGKILL)
                os.waitpid(child_pid, 0)
            except OSError:
                pass
            logger.info(f"Cleaned up process {child_pid}")
