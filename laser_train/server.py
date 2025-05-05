"""
Simple task‑server that speaks the 2‑action protocol:

- It waits for POST /rpc json={"action": "..."}
- Replies with {"action": "wait", "args": [seconds]}
  or     with {"action": "execute", "args": [func_name, func_args]}
"""
from flask import Flask, request, jsonify
import queue, threading, time
import random

app = Flask(__name__)

# --- demo state -------------------------------------------------------------
WORK_QUEUE: "queue.Queue[tuple[str, list]]" = queue.Queue()
DEFAULT_WAIT_SECONDS = 1                     # how long to tell idle clients to wait

# preload a couple of demo jobs so the first client sees something to do
#WORK_QUEUE.put(("send_mask", [1024]))
WORK_QUEUE.put(("read_acf", ['']))
#WORK_QUEUE.put(("send_mask", [500]))
WORK_QUEUE.put(("read_acf", ['']))
WORK_QUEUE.put(("read_acf", ['']))
WORK_QUEUE.put(("read_acf", ['']))
#WORK_QUEUE.put(("send_mask", [200]))
#WORK_QUEUE.put(("send_mask", [1000]))
#WORK_QUEUE.put(("send_mask", [50]))

# --- helpers ----------------------------------------------------------------
def next_job():
    """Return ("execute", [func, args]) or ("wait", [n])."""
    try:
        func_name, func_args = WORK_QUEUE.get_nowait()
        return "execute", [func_name, func_args]
    except queue.Empty:
        return "wait", [DEFAULT_WAIT_SECONDS]

# --- HTTP endpoint ----------------------------------------------------------
@app.post("/rpc")
def rpc():
    data = request.get_json(force=True) or {}
    action = data.get("action")

    if action == "query":
        kind, args = next_job()
        if args[0] == "send_mask":
            args[1] = [random.randint(0, args[1]) for _ in range(20)]
        res =  jsonify({"action": kind, "args": args})
        return res

    elif action == "response":
        # demo: just log the result that came back
        res = data.get("result")
        #app.logger.info("Client response received: %s", res)
        #print("Client response received: %s", res)
        print ('Result', type(res), len(res[0]), len(res[1]))
        # immediately decide what to do next
        kind, args = next_job()
        if args[0] == "send_mask":
            args[1] = [random.randint(0, 1023) for _ in range(20)]
        res =  jsonify({"action": kind, "args": args})
        return res

    else:
        return jsonify({"error": "unknown action"}), 400


# --- run it -----------------------------------------------------------------
if __name__ == "__main__":  
    # threaded=False means one request at a time – fine for a toy demo
    app.run(host="0.0.0.0", port=8000, threaded=False)
