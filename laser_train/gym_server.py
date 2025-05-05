# remote_mask_env.py
"""
Gymnasium environment *and* Flask server in one file.

step(action)
    ├─ puts ("send_mask", [action]) into task_q
    ├─ …blocks until client POSTs {"action":"response", "result": …}
    └─ returns (obs=result, reward=0, terminated=False, truncated=False, info={})

The Flask route keeps answering client /rpc calls with either
    {"action":"wait", "args":[1]}          or
    {"action":"execute", "args":["send_mask", [action]]}
exactly like your previous server.py.
"""
from __future__ import annotations
import threading, queue, time, json
from typing import Any

import numpy as np
import gymnasium as gym
from gymnasium import spaces
from flask import Flask, request, jsonify
import random

import sys
sys.path.append('../laser')
from data_processing.py import vec_to_mask

# ──────────────────────────────────────────────────────────────────────────
#  Environment
# ──────────────────────────────────────────────────────────────────────────
class RemoteMaskEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self,
                 host: str = "0.0.0.0",
                 port: int = 8000,
                 default_wait: int = 1):
        """Start the Flask server in a background thread and expose a Gym env."""
        super().__init__()

        # Simple scalar observation; refine to suit your task
        self.observation_space = spaces.Box(0, 1023, shape=(20,),
                                            dtype=np.int)
        self.action_space = spaces.Discrete(100)      # mask index 0‑99, say

        self._task_q: "queue.Queue[tuple[str, list[Any]]]" = queue.Queue()
        self._result_q: "queue.Queue[Any]" = queue.Queue()
        self._DEFAULT_WAIT = default_wait

        # ------------------------------------------------------------------
        # Build the Flask app and launch it
        # ------------------------------------------------------------------
        app = Flask(__name__)

        @app.post("/rpc")
        def rpc():
            data = request.get_json(force=True) or {}
            act = data.get("action")

            if act == "query":
                # Does the env have a task ready for the client?
                try:
                    func_name, func_args = self._task_q.get_nowait()
                    return jsonify({"action": "execute",
                                    "args": [func_name, func_args]})
                except queue.Empty:
                    return jsonify({"action": "wait",
                                    "args": [self._DEFAULT_WAIT]})

            elif act == "response":
                res = data.get("result")
                # Push result back to the waiting step()
                self._result_q.put(res)
                # Tell client to wait a moment before next poll
                return jsonify({"action": "wait",
                                "args": [self._DEFAULT_WAIT]})
            else:
                return jsonify({"error": "unknown action"}), 400

        # run() blocks, so put it in a daemon thread
        self._server_thread = threading.Thread(
            target=app.run,
            kwargs=dict(host=host, port=port, threaded=False),
            daemon=True,
        )
        self._server_thread.start()
        # Give the server a moment to bind the port
        time.sleep(0.5)

    # ------------------------------------------------------------------
    # Gymnasium API
    # ------------------------------------------------------------------
    def reset(self, *, seed: int | None = None, options=None):
        super().reset(seed=seed)
        # Nothing to do on the server side for a reset; just return dummy obs
        self._last_obs = 0.0
        return np.array([self._last_obs], dtype=np.float64), {}


    def step(self, action):
        """
        1. Enqueue the task (“send_mask” with the given action as its arg).
        2. Block until the client POSTs a response.
        3. Return that response as the observation.
        """
        # 1. Tell the client what to do
        self._task_q.put(("send_mask", action))

        # 2. Wait for the client's result (this **blocks**)
        _ = self._result_q.get()


        # Read the ACF (probably current state)
        self._task_q.put(("read_acf", ['']))
        # 2. Wait for the client's result (this **blocks**)
        result = self._result_q.get()

        # 3. Build Gymnasium‑style return values
        obs = np.array([result], dtype=np.float64)
        reward = 0.0                 # put your own logic here
        terminated = False
        truncated = False
        info = {"mask": int(action)}

        return obs, reward, terminated, truncated, info

    # (Optional) tidy shutdown if you ever close the env explicitly
    def close(self):
        super().close()
        # The Flask dev server stops when the main program exits, so nothing
        # special is required here.


# ──────────────────────────────────────────────────────────────────────────
#  Quick manual test
# ──────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    env = RemoteMaskEnv()
    obs, info = env.reset()
    print("RESET  →", obs)

    for step_id in range(4):             # will queue 4 send_mask jobs
        action = [random.randint(0, 1023) for _ in range(20)]
        print(f"STEP {step_id}: waiting for client…")
        obs, r, term, trunc, info = env.step(action)
        print("   result from client →", obs, info)
