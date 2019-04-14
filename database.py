import sqlite3
import hashlib
import datetime

db_file_location = "database_file/all_tables.db"


def list_users():
    _conn = sqlite3.connect(db_file_location)
    _c = _conn.cursor()
    _c.execute("select username from users;")
    result = [x[0] for x in _c.fetchall()]
    _conn.close()
    
    return result


def verify(id, pw):
    _conn = sqlite3.connect(db_file_location)
    _c = _conn.cursor()
    _c.execute("select password from users where username = '" + id + "';")
    result = _c.fetchone()[0] == hashlib.sha256(pw.encode()).hexdigest()
    _conn.close()

    return result


def delete_user_from_db(id):
    _conn = sqlite3.connect(db_file_location)
    _c = _conn.cursor()
    _c.execute("delete from users where username = '" + id + "';")
    _conn.commit()
    _conn.close()

    # when we delete a user from database USERS, we also need to delete all his or her notes data from database NOTES
    _conn = sqlite3.connect(db_file_location)
    _c = _conn.cursor()
    _c.execute("delete from notes where user_id in (select id from users where username = '" + id + "');")
    _conn.commit()
    _conn.close()


    # when we delete a user from database USERS, we also need to delete all his or her queries data from database QUERIES
    _conn = sqlite3.connect(db_file_location)
    _c = _conn.cursor()
    _c.execute("delete from queries where user_id in (select id from users where username = '" + id + "');")
    _conn.commit()
    _conn.close()


def add_user_into_db(id, pw):
    _conn = sqlite3.connect(db_file_location)
    _c = _conn.cursor()
    _c.execute("insert into users (username, password) values(?, ?)", (id.upper(), hashlib.sha256(pw.encode()).hexdigest()))
    _conn.commit()
    _conn.close()


def read_query_from_db(id):
    _conn = sqlite3.connect(db_file_location)
    _c = _conn.cursor()
    command = "select q.query_id, q.time_stamp, q.query from queries q join users u on q.user_id = u.id where u.username = '" + id.upper() + "';"
    _c.execute(command)
    result = _c.fetchall()
    _conn.commit()
    _conn.close()

    return result


def read_note_from_db(id):
    _conn = sqlite3.connect(db_file_location)
    _c = _conn.cursor()
    command = "select n.note_id, n.time_stamp, note from notes n join users u on n.user_id = u.id where u.username = '" + id.upper() + "';"
    _c.execute(command)
    result = _c.fetchall()

    _conn.commit()
    _conn.close()

    return result


def match_user_id_with_note_id(note_id):
    # Given the note id, get username
    # to later confirm if the current user is the owner of the note which is being operated.
    _conn = sqlite3.connect(db_file_location)
    _c = _conn.cursor()

    command = "select u.username from notes n join users u on n.user_id = u.id where n.note_id = '" + note_id + "';"
    _c.execute(command)
    result = _c.fetchone()[0]

    _conn.commit()
    _conn.close()

    return result


def write_query_into_db(id, query_to_write):
    _conn = sqlite3.connect(db_file_location)
    _c = _conn.cursor()
    command = "select id from users where username = '" + id.upper() + "';"
    _c.execute(command)
    user_id = _c.fetchone()[0]
    _conn.commit()
    _conn.close()

    _conn = sqlite3.connect(db_file_location)
    _c = _conn.cursor()
    current_timestamp = str(datetime.datetime.now())
    _c.execute("insert into queries (query_id, user_id, time_stamp, query) values(?, ?, ?, ?)", (
        hashlib.sha1((str(user_id) + current_timestamp).encode()).hexdigest(),
        user_id,
        current_timestamp,
        query_to_write
    ))
    _conn.commit()
    _conn.close()


def write_note_into_db(id, note_to_write):
    _conn = sqlite3.connect(db_file_location)
    _c = _conn.cursor()
    command = "select id from users where username = '" + id.upper() + "';"
    _c.execute(command)
    user_id = _c.fetchone()[0]
    _conn.commit()
    _conn.close()

    _conn = sqlite3.connect(db_file_location)
    _c = _conn.cursor()
    current_timestamp = str(datetime.datetime.now())
    _c.execute("insert into notes (note_id, user_id, time_stamp, note) values(?, ?, ?, ?)", (
        hashlib.sha1((str(user_id) + current_timestamp).encode()).hexdigest(),
        user_id,
        current_timestamp,
        note_to_write
    ))
    _conn.commit()
    _conn.close()


def delete_note_from_db(note_id):
    _conn = sqlite3.connect(db_file_location)
    _c = _conn.cursor()

    command = "delete from notes where note_id = '" + note_id + "';"
    _c.execute(command)

    _conn.commit()
    _conn.close()


if __name__ == "__main__":
    print(list_users())