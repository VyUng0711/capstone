from flask import Flask, session, url_for, redirect, render_template, request, abort, flash
from model import word2vec_predict_sentence_with_fixed_keywords, change_vocab
from database import list_users, verify, delete_user_from_db, add_user_into_db
from database import read_note_from_db, write_note_into_db, delete_note_from_db, match_user_id_with_note_id
from database import write_query_into_db, read_query_from_db
import gensim

import config


app = Flask(__name__)
app.config.from_object('config')

model = gensim.models.KeyedVectors.load_word2vec_format(config.MODEL, binary=True)
change_vocab(model)


@app.errorhandler(401)
def error_401(error):
    return render_template("page_401.html"), 401

@app.errorhandler(403)
def error_403(error):
    return render_template("page_403.html"), 403



@app.route("/")
def home_page():
    return render_template("index.html")

@app.route("/public/")
def get_public():
    return render_template("about.html")

@app.route("/help/")
def get_help():
    return render_template("help.html")

@app.route("/private/")
def get_private():
    if "current_user" in session.keys():
        notes_list = read_note_from_db(session['current_user'])
        queries_list = read_query_from_db(session['current_user'])

        notes_table = zip([x[0] for x in notes_list],\
                          [x[1] for x in notes_list],\
                          [x[2] for x in notes_list],\
                          ["/delete_note/" + x[0] for x in notes_list])
        queries_table = zip([x[0] for x in queries_list], \
                          [x[1] for x in queries_list], \
                          [x[2] for x in queries_list])
                          # ["/delete_note/" + x[0] for x in notes_list])

        return render_template("private_page.html", notes=notes_table, queries=queries_table) #, images=images_table)
    else:
        return abort(401)


@app.route("/admin/")
def get_admin():
    if session.get("current_user", None) == "ADMIN":
        user_list = list_users()
        user_table = zip(range(1, len(user_list)+1),\
                        user_list,\
                        [x + y for x, y in zip(["/delete_user/"] * len(user_list), user_list)])
        return render_template("admin.html", users=user_table)
    else:
        return abort(401)


@app.route("/", methods=["POST"])
def get_predictions():
    query = request.form.get("query")
    fix_keywords = request.form.get("fix_keywords")

    if session.get('current_user'):
        write_query_into_db(session['current_user'], query)
    key_words, prediction_result, random_combinations = word2vec_predict_sentence_with_fixed_keywords(
        query,
        fix_keywords,
        model
    )
    return(render_template(
        "prediction.html",
        prediction_result=prediction_result,
        query=query,
        random_combinations=random_combinations,
        key_words=key_words
    ))


@app.route("/write_note", methods=["POST"])
def write_note():
    text_to_write = request.form.get("text_note_to_take")

    write_note_into_db(session['current_user'], text_to_write)
    return redirect(url_for("get_private"))


@app.route("/delete_note/<note_id>", methods=["GET"])
def delete_note(note_id):
    # Ensure the current user is NOT operating on other users' note.
    if session.get("current_user", None) == match_user_id_with_note_id(note_id):
        delete_note_from_db(note_id)
    else:
        return abort(401)
    return redirect(url_for("get_private"))


@app.route("/signup/")
def get_signup():
    return render_template("signup.html")
    # return render_template("signup.html", id_to_add_is_duplicated=False, valid_pw=True)


@app.route("/signup_user_info", methods=["POST"])
def signup():
    id_submitted = request.form.get("inputName")
    pw_submitted = request.form.get("inputPassword")
    # before we add the user, we need to ensure this doesn't exists in database.
    if id_submitted.upper() in list_users():
        flash("The account name already exists.", "error")
        return redirect(url_for("get_signup"))
    elif " " in id_submitted or "'" in id_submitted:
        flash("The account name is invalid. Account name must not contain space or apostrophe", "error")
        return redirect(url_for("get_signup"))
    else:
        # TODO: Add more requirements for password
        if len(pw_submitted) < 5:
            flash("Password must contain at least 5 characters.", "error")
            return redirect(url_for("get_signup"))
        else:
            add_user_into_db(id_submitted, pw_submitted)
            flash("You have successfully signed up")
            return redirect(url_for("home_page"))



@app.route("/login", methods=["POST"])
def login():
    id_submitted = request.form.get("id").upper()
    if id_submitted not in list_users():
        flash("User name not found", 'error')
    else:
        if not verify(id_submitted, request.form.get("pw")):
            flash('Wrong password', 'error')
        else:
            session['current_user'] = id_submitted
            flash('Welcome back! You have successfully logged in')

    return redirect(url_for("home_page"))



@app.route("/logout/")
def logout():
    session.pop("current_user", None)
    flash('You have successfully logged out')
    return redirect(url_for("home_page"))


@app.route("/delete_user/<id>/", methods=['GET'])
def delete_user(id):
    if session.get("current_user", None) == "ADMIN":
        if id == "ADMIN":   # ADMIN account can't be deleted.
            return abort(403)

        delete_user_from_db(id)
        return redirect(url_for("get_admin"))
    else:
        return abort(401)


@app.route("/add_user", methods=["POST"])
def add_user():
    if session.get("current_user", None) == "ADMIN": # only Admin should be able to add user.
        # before we add the user, we need to ensure this doesn't exist in database. We also need to ensure the id is valid.
        if request.form.get('id').upper() in list_users():
            user_list = list_users()
            user_table = zip(range(1, len(user_list)+1),\
                            user_list,\
                            [x + y for x, y in zip(["/delete_user/"] * len(user_list), user_list)])
            return render_template("admin.html", id_to_add_is_duplicated=True, users=user_table)
        if " " in request.form.get('id') or "'" in request.form.get('id'):
            user_list = list_users()
            user_table = zip(range(1, len(user_list)+1),\
                            user_list,\
                            [x + y for x, y in zip(["/delete_user/"] * len(user_list), user_list)])
            return render_template("admin.html", id_to_add_is_invalid=True, users=user_table)
        else:
            add_user_into_db(request.form.get('id'), request.form.get('pw'))
            return redirect(url_for("get_admin"))
    else:
        return abort(401)


if __name__ == "__main__":

    app.run(debug=True, host="0.0.0.0")
