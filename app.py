import os
import datetime
import hashlib
import re
import random
import pickle
import pandas as pd
from string import punctuation
from flask import Flask, session, url_for, redirect, render_template, request, abort, flash
from database import list_users, verify, delete_user_from_db, add_user_into_db
from database import read_note_from_db, write_note_into_db, delete_note_from_db, match_user_id_with_note_id, write_query_into_db, read_query_from_db
# from database import image_upload_record, list_images_for_user, match_user_id_with_image_uid, delete_image_from_db
from werkzeug.utils import secure_filename
import gensim
from collections import defaultdict

import config


app = Flask(__name__)
app.config.from_object('config')

model = gensim.models.KeyedVectors.load_word2vec_format(config.MODEL, binary=True)
english_vocab = pickle.load(open(config.ENGLISH_VOCAB, "rb"))
stopword = pickle.load(open(config.STOPWORD, "rb"))

word_vocab = model.vocab
word_vectors = model.wv

map_word_to_frequency = {}
for k, v in word_vocab.items():
    map_word_to_frequency[k] = v.count

small_vocab = {}
for k, v in map_word_to_frequency.items():
    if k in english_vocab:
        small_vocab[k] = v
new_vocab = {}
for k, v in small_vocab.items():
    new_vocab[k] = model.vocab[k]
model.vocab = new_vocab

TOP_N = 100
K = 10
regex = re.compile('[^a-zA-Z]')


def clean_result(res, no):
    cleaned = set()
    for k, v in res:
        k = k.replace('_', ' ').lower()
        merged = k.replace(' ', '')
        if merged.isalpha():
            cleaned.add(k.replace(' ', '_'))
        # if not k.isalpha():
        #     k = regex.sub('', k)
        # cleaned.add(k.replace('_', ' '))
    words = random.sample(cleaned, no)
    return words


def word2vec_predict_sentence(sentence):
    no_punc = sentence.translate(str.maketrans('', '', punctuation))
    processed = [word for word in no_punc.split() if word not in stopword]
    map_word_to_suggestions = defaultdict(list)
    key_words = []
    for word in processed:
        lower = word.lower()
        if word in model.vocab:
            key_words.append(word)
            result = model.most_similar(word, topn=TOP_N)
            words = clean_result(res=result, no=K)
            map_word_to_suggestions[word] = words
        elif lower in model.vocab:
            key_words.append(word)
            result = model.most_similar(lower, topn=TOP_N)
            words = clean_result(res=result, no=K)
            map_word_to_suggestions[lower] = words

    shuffled = []
    for suggestion in list(map_word_to_suggestions.values()):
        shuffled.append(random.sample(suggestion, len(suggestion)))
    random_com = []
    for i in range(10):
        this_com = [x[i] for x in shuffled]
        random_com.append(this_com)

    suggestion_df = pd.DataFrame(map_word_to_suggestions)
    df_html = suggestion_df.to_html(classes='table', escape=True, border=0, justify='center')
    return key_words, df_html, random_com



# def word2vec_predict_sentence(sentence):
#     map_word_to_suggestions = defaultdict(list)
#
#     for word in sentence.split():
#         if word in model.vocab:
#             result = model.most_similar(word, topn=100)
#             words = [x[0] for x in random.choices(result, k = 10)]
#             map_word_to_suggestions[word] = words
#
#     random_com = []
#     for i in range(10):
#         this_com = [x[i] for x in map_word_to_suggestions.values()]
#         random_com.append(this_com)
#
#     suggestion_df = pd.DataFrame(map_word_to_suggestions)
#     df_html = suggestion_df.to_html(classes='table', escape=True, border=0, justify='center')
#     return df_html, random_com


def word2vec_predict_simple(sentence):
    # titles = ['cat', 'hello']
    # rows = [['dog', 'hi'], ['lion', 'goodbye'], ['tiger', 'yo'], ['pig', 'welcome']]
    # return titles, rows
    # return {'cat': ['dog', 'lion', 'tiger', 'pig'], 'hello': ['hi', 'goodbye', 'yo', 'welcome']}
    df = pd.DataFrame({'cat': ['dog', 'lion', 'tiger', 'pig'],
                       'hello': ['hi', 'goodbye', 'yo', 'welcome'],
                       'christmas': ['xmas', 'holiday', 'Noel', 'Santa']})
    df_html = df.to_html(classes='table', escape=True, border=0, justify='center')
    random_com = [['dog', 'hi', 'xmas'], ['lion', 'goodbye', 'holiday']]
    return df_html, random_com




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
    if session.get('current_user'):
        write_query_into_db(session['current_user'], query)

    key_words, prediction_result, random_combinations = word2vec_predict_sentence(query)
    # prediction_result, random_combinations = word2vec_predict_simple(query)

    # return(render_template("prediction.html", titles=titles, rows=rows, query=query))

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
    return render_template("signup.html", id_to_add_is_duplicated=False, valid_pw=True)


@app.route("/signup_user_info", methods=["POST"])
def signup():
    id_submitted = request.form.get("inputName")
    pw_submitted = request.form.get("inputPassword")
    success = None
    # before we add the user, we need to ensure this doesn't exists in database.
    if id_submitted.upper() in list_users():
        return render_template("signup.html", id_to_add_is_duplicated=True, valid_pw=True)
    else:
        if len(pw_submitted) < 5:
            return render_template("signup.html", id_to_add_is_duplicated=False, valid_pw=False)
        else:
            add_user_into_db(id_submitted, pw_submitted)
            success = "You have successfully signed up"
            return redirect(url_for("home_page"))
            # return render_template("index.html", success=success)


@app.route("/login", methods=["POST"])
def login():
    # error = None
    # success = None
    id_submitted = request.form.get("id").upper()
    if id_submitted not in list_users():
        flash("User name not found", 'error')
        # error = "User name not found"
    else:
        if not verify(id_submitted, request.form.get("pw")):
            flash('Wrong password', 'error')
            # error = 'Wrong password'
        else:
            session['current_user'] = id_submitted
            # success = "You have successfully logged in"
            flash('You have successfully logged in')

    return redirect(url_for("home_page"))
    # return render_template("index.html", error=error, success=success)



@app.route("/logout/")
def logout():
    session.pop("current_user", None)
    # success = "You have successfully logged out"
    flash('You have successfully logged out')
    # return render_template("index.html", success=success)
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
