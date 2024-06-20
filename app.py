from flask import Flask, render_template, jsonify, session
from flask_socketio import SocketIO, send, emit
from datetime import datetime, timedelta
import random
import sqlite3
import threading
import time

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
app.config["SESSION_TYPE"] = "filesystem"
socketio = SocketIO(app)

# Fruit names for random usernames
FRUITS = [
    "Apple",
    "Banana",
    "Cherry",
    "Date",
    "Elderberry",
    "Fig",
    "Grape",
    "Honeydew",
    "Kiwi",
    "Lemon",
    "Mango",
    "Nectarine",
    "Orange",
    "Papaya",
    "Quince",
    "Raspberry",
    "Strawberry",
    "Tomato",
    "Ugli",
    "Watermelon",
]

# Path to SQLite database
DATABASE = "chat.db"


def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            message TEXT,
            timestamp TEXT
        )
    """
    )
    conn.commit()
    conn.close()


def cleanup_db():
    while True:
        time.sleep(60)  # Run cleanup every minute
        cutoff_time = datetime.now() - timedelta(hours=2)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM messages WHERE timestamp < ?",
            (cutoff_time.strftime("%Y-%m-%d %H:%M:%S"),),
        )
        conn.commit()
        conn.close()


@app.route("/")
def index():
    if "username" not in session:
        session["username"] = generate_random_name()
    return render_template("index.html")


@app.route("/messages", methods=["GET"])
def get_messages():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT username, message, timestamp FROM messages")
    messages = cursor.fetchall()
    conn.close()
    return jsonify(messages)


@socketio.on("message")
def handle_message(msg):
    username = session.get("username")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO messages (username, message, timestamp) VALUES (?, ?, ?)
    """,
        (username, msg, timestamp),
    )
    conn.commit()
    conn.close()

    message_data = {"username": username, "message": msg, "timestamp": timestamp}
    emit("message", message_data, broadcast=True)


def generate_random_name():
    return random.choice(FRUITS)


if __name__ == "__main__":
    init_db()
    cleanup_thread = threading.Thread(target=cleanup_db)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    socketio.run(app, host="0.0.0.0", port=5000)
