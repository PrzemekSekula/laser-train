"""
Client that follows the original polling protocol but now automatically waits
5 seconds and retries whenever it fails to get a **valid** response from the
server (network error, timeout, non‑2xx status, or invalid JSON).
"""
import requests, time

SERVER_URL = "http://127.0.0.1:8000/rpc"
RETRY_DELAY = 5  # seconds to wait before trying again on failure

# ---------------------------------------------------------------------------
# Functions the client is willing to execute
# ---------------------------------------------------------------------------

def add(a, b):
    return a + b


def echo(msg):
    return msg


def sleep(seconds):
    time.sleep(seconds)
    return f"slept {seconds}s"


DISPATCH = {f.__name__: f for f in [add, echo, sleep]}

# ---------------------------------------------------------------------------
# Helper that POSTS and keeps retrying until it gets a usable JSON reply
# ---------------------------------------------------------------------------

def post_retry(action: str, **kw):
    """POST to SERVER_URL, returning the JSON body.
    If the request fails or the response is invalid, wait RETRY_DELAY seconds
    and try again. This satisfies the new requirement.
    """
    while True:
        try:
            resp = requests.post(
                SERVER_URL, json={"action": action, **kw}, timeout=30
            )
            resp.raise_for_status()
            return resp.json()  # may raise ValueError if body isn't JSON
        except (requests.exceptions.RequestException, ValueError) as err:
            print(f"⚠️  no valid response ({err}); retrying in {RETRY_DELAY}s")
            time.sleep(RETRY_DELAY)


# ---------------------------------------------------------------------------
# Main client loop following the 5‑step protocol
# ---------------------------------------------------------------------------

def main():
    while True:
        reply = post_retry("query")  # Step 3 – resilient query

        kind, args = reply.get("action"), reply.get("args", [])

        if kind == "wait":
            (n,) = args
            print(f"⏳ waiting {n}s")
            time.sleep(n)

        elif kind == "execute":
            func_name, func_args = args
            func = DISPATCH.get(func_name)
            if func is None:
                print(f"⚠️  unknown function '{func_name}' – skipping")
                time.sleep(1)
                continue

            print(f"▶️  executing {func_name}{tuple(func_args)}")
            try:
                result = func(*func_args)
            except Exception as ex:
                result = f"error: {ex!r}"

            # Step 4 & 5 – send the result and instantly get next directive
            reply = post_retry("response", result=result)
            # loop continues with the new reply on the next iteration

        else:
            print(f"⚠️  unknown directive: {reply}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nclient stopped")
