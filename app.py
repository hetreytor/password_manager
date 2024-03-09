from login import Login
from data import NoteData
from flask import Flask, render_template, redirect, url_for, request, session

app = Flask(__name__)
app.secret_key = 'my_secret_key'


@app.route("/")
def main():
    return render_template("main.html")


@app.route("/register", methods=["GET"])
def register():
    return render_template("register.html")


@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")


@app.route("/note_menu", methods=["GET"])
def note_menu():
    return render_template("note_menu.html")


@app.route("/add_note")
def add_note():
    return render_template('add_note.html')


@app.route("/get_note")
def get_note():
    try:
        return render_template('get_note.html',
                           names=NoteData.get_all_notes_name(session.get("username", None)))
    except TypeError:
        return render_template('get_note.html')


@app.route("/delete_note", methods=["GET"])
def delete_note():
    return redirect(url_for("delete_note"))


@app.route("/list_notes", methods=["GET"])
def list_notes():
    return redirect(url_for("list_notes"))


@app.route("/login", methods=["POST"])
def handle_login():
    username = request.form["username"]
    password = request.form["password"]
    session["username"] = username
    session["password"] = password
    if Login.check_credentials(username, password):
        return redirect(url_for("note_menu"))
    else:
        error_message = "The entered data is not correct."
        return render_template("login.html", error=error_message)


@app.route("/register", methods=["POST"])
def handle_registration():
    username = request.form["username"]
    password = request.form["password"]
    start_time = request.form["start_time"]
    end_time = request.form["end_time"]
    new_user = Login.AuthData(username=username, user_password=password, list_time_window=f"{start_time}-{end_time}")
    Login.input_in_database(auth_data=new_user)
    return redirect(url_for("main"))


@app.route("/add_note", methods=["POST"])
def handle_add_note():
    note_name = request.form["note_name"]
    login = request.form["login"]
    password = request.form["password"]
    description = request.form["description"]
    pincode = request.form["pincode"]
    start_time = request.form["start_time"]
    end_time = request.form["end_time"]
    new_note = NoteData.SecretData(user_name=session.get("username", None), note_name=note_name, login=login,
                                   password=password, description=description,
                                   list_time_window=f"{start_time}-{end_time}")
    NoteData.input_in_database(secret_data=new_note, pincode=pincode, master_key=session.get("password"))
    return redirect(url_for("note_menu"))


@app.route("/get_note", methods=["GET", "POST"])
def handle_get_note():
    name = request.form.get("list_box")
    pincode = request.form.get("pincode")
    data = NoteData.get_note(user_name=session.get("username"), note_name=name,
                             master_key=session.get("password"), pincode=pincode)
    return render_template('get_note.html',
                           names=NoteData.get_all_notes_name(session.get("username", None)), data=data)


app.run()
