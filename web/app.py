import os

from flask import Flask, render_template, abort
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId


app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
DB_NAME = os.getenv("DB_NAME", "ipa2026_db")

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
)

db = client[DB_NAME]
routers = db["routers"]


@app.route("/")
def index():
    router_list = list(
        routers.find({}, {"password": 0}).sort("ip", 1)
    )

    return render_template(
        "index.html",
        routers=router_list,
    )


@app.route("/router/<router_id>")
def router_detail(router_id):
    try:
        router = routers.find_one(
            {"_id": ObjectId(router_id)},
            {"password": 0},
        )
    except (InvalidId, TypeError):
        abort(404)

    if router is None:
        abort(404)

    interfaces = router.get("interfaces", [])
    history = router.get("history", [])

    # Support existing records that have current status
    # but do not yet have history.
    if not history and interfaces:
        history = [{
            "timestamp": router.get(
                "interface_status_updated_at"
            ),
            "interfaces": interfaces,
        }]

    history = history[:3]

    return render_template(
        "router_detail.html",
        router=router,
        interfaces=interfaces,
        history=history,
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080,
    )
