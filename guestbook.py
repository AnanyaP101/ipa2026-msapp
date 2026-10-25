
from flask import Flask, render_template, request

guestbook = Flask(__name__)

@guestbook.route("/", methods=["GET", "POST"])
def main():
    yourname = ""
    message = ""

    if request.method == "POST":
        yourname = request.form.get("yourname", "")
        message = request.form.get("message", "")

    return render_template(
        "index.html",
        yourname=yourname,
        message=message
    )

if __name__ == "__main__":
    guestbook.run(host="0.0.0.0", port=8080)
