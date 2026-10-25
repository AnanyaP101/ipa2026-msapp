import time
from datetime import datetime

from database import get_routers
from producer import send_router


def main():
    run_number = 0

    while True:
        print(
            f"[{datetime.now()}] run #{run_number}",
            flush=True
        )

        try:
            routers = get_routers()

            if not routers:
                print("No router data found in MongoDB", flush=True)

            for router in routers:
                send_router(router)

        except Exception as error:
            print(f"Scheduler error: {error}", flush=True)

        run_number += 1
        time.sleep(10)


if __name__ == "__main__":
    main()
