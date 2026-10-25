
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

data = []

@app.route("/")
def main():
    return render_template("index.html", data=data)

@app.route("/add", methods=["POST"])
def add_comment():
    yourname = request.form.get("yourname")
    message = request.form.get("message")

    if yourname and message:
        data.append({
            "yourname": yourname,
            "message": message
        })

    return redirect(url_for("main"))

@app.route("/delete/<int:index>", methods=["POST"])
def delete_comment(index):
    if 0 <= index < len(data):
        data.pop(index)

    return redirect(url_for("main"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
