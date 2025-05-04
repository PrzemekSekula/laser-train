"""
Client that follows the original polling protocol but now automatically waits
5 seconds and retries whenever it fails to get a **valid** response from the
server (network error, timeout, non‑2xx status, or invalid JSON).
"""
import sys
import requests
import time
import argparse


sys.path.append('../laser_train')
from tools import parse_with_config_file

# ---------------------------------------------------------------------------
# Functions the client is willing to execute
# ---------------------------------------------------------------------------


from mock import send_mask, read_acf


DISPATCH = {f.__name__: f for f in [send_mask, read_acf]}

# ---------------------------------------------------------------------------
# Helper that POSTS and keeps retrying until it gets a usable JSON reply
# ---------------------------------------------------------------------------

def post_retry(args, action, **kw):
    """POST to SERVER_URL, returning the JSON body.
    If the request fails or the response is invalid, wait RETRY_DELAY seconds
    and try again. This satisfies the new requirement.
    """
    while True:
        try:
            resp = requests.post(
                args.server_url, json={"action": action, **kw}, timeout=30
            )
            resp.raise_for_status()
            return resp.json()  # may raise ValueError if body isn't JSON
        except (requests.exceptions.RequestException, ValueError) as err:
            print(f"⚠️  no valid response ({err}); retrying in {args.retry_delay}s")
            time.sleep(args.retry_delay)


# ---------------------------------------------------------------------------
# Main client loop following the 5‑step protocol
# ---------------------------------------------------------------------------

def main(args):
    while True:
        reply = post_retry(args, "query") 
        kind, server_args = reply.get("action"), reply.get("args", [])

        if kind == "wait":
            (n,) = server_args
            if args.verbose:
                print(f"⏳ waiting {n}s")
            time.sleep(n)
            reply = post_retry(args, "query") 

        elif kind == "execute":
            func_name, func_args = server_args
            func = DISPATCH.get(func_name)
            if func is None:
                if args.verbose:
                    print(f"⚠️  unknown function '{func_name}' – skipping")
                time.sleep(1)
                continue

            if args.verbose:
                print(f"▶️  executing {func_name}{tuple(func_args)}")
            try:
                result = func(*func_args)
            except Exception as ex:
                result = f"error: {ex!r}"

            # Step 4 & 5 – send the result and instantly get next directive
            reply = post_retry(args, "response", result=result)
            # loop continues with the new reply on the next iteration

        else:
            if args.verbose:
                print(f"⚠️  unknown directive: {reply}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Trains the quantum matrix transformer. Defaults are '
        'loaded from configs.yaml, from the defaults section.'
        )
    parser.add_argument(
        "--configs", 
        nargs="+", 
        help="List of named configs from configs.yaml to load."
    )

    try:
        main(parse_with_config_file(parser, defaults_name="defaults"))
    except KeyboardInterrupt:
        print("\nclient stopped")
