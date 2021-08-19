import hmac
import datetime
import sys
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt import JWT, jwt_required, current_identity
import sqlite3


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

def jdata(cursor, row):
    jd = {}
    for idx, col in enumerate(cursor.description):
        jd[col[0]] = row[idx]
    return jd


def fetch_users():
    with sqlite3.connect('UTA_Enrollment') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users_data = cursor.fetchall()

        new_data = []

        for data in users_data:
            new_data.append(User(data[0], data[5], data[6]))

        return new_data


# creating table for users
def init_user_table():
    conn = sqlite3.connect('UTA_Enrollment')
    print("Database Access Granted")

    conn.execute("CREATE TABLE IF NOT EXISTS user (user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "email TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()


init_user_table()
users = fetch_users()


# creating table for the products
def init_products_table():
    with sqlite3.connect('UTA_Enrollment') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS cart (product_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "item_name TEXT NOT NULL,"
                     "description TEXT NOT NULL,"
                     "quantity TEXT NOT NULL,"
                     "price TEXT NOT NULL,"
                     "type TEXT NOT NULL, "
                     "total TEXT NOT NULL)")
    print("UTA_Enrollment table created successfully")


init_products_table()

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'POPI-secret-key'
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)
CORS(app)
jwt = JWT(app, authenticate, identity)


@app.route('/', methods=["GET"])
def welcome():
    response = {}
    if request.method == "GET":
        response["message"] = "WELCOME TO UTA"
        response["status_code"] = 201
        return response


@app.route('/user/', methods=["POST", "GET", "PATCH"])
def user_registration():
    response = {}

    # This is used to get all users
    if request.method == "GET":
        with sqlite3.connect("UTA_Enrollment") as conn:
            conn.row_factory = jdata
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user")
            users = cursor.fetchall()

        response['status_code'] = 200
        response['data'] = users
        return response

    # This is used to perform a login
    if request.method == "PATCH":
        email = request.json["email"]
        password = request.json["password"]

        with sqlite3.connect("UTA_Enrollment") as conn:
            conn.row_factory = jdata
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE email=? AND password=?", (email, password,))
            user = cursor.fetchone()

        response['status_code'] = 200
        response['data'] = user
        return response

    # REGISTER
    if request.method == "POST":
        try:
            first_name = request.json['first_name']
            last_name = request.json['last_name']
            email = request.json['email']
            password = request.json['password']

            with sqlite3.connect("UTA_Enrollment") as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO user("
                               "first_name,"
                               "last_name,"
                               "email,"
                               "password) VALUES(?, ?, ?)", (first_name, last_name, email, password))
                conn.commit()
                response["message"] = "New user successfully added to database"
                response["status_code"] = 201
            return response
        except ValueError:
            response["message"] = "Error, please try again"
            response["status_code"] = 209
            return response


@app.route('/user/<int:user_id>', methods=["GET"])
def get_user(user_id):
    response = {}
    with sqlite3.connect("UTA_Enrollment") as conn:
        conn.row_factory = jdata
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE user_id=" + str(user_id))

        user = cursor.fetchone()

    response['status_code'] = 200
    response['data'] = user
    return response


@app.route('/product/', methods=["POST", "GET"])
def products():
    response = {}

    # GETTING ALL THE PRODUCTS
    if request.method == "GET":
        with sqlite3.connect("UTA_Enrollment") as conn:
            conn.row_factory = jdata
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products")
            users = cursor.fetchall()

        response['status_code'] = 200
        response['data'] = users
        return response

    # PRODUCT GENERATER
    if request.method == "POST":
        try:
            user_id = request.json['user_id']
            title = request.json['title']
            description = request.json['description']
            image = request.json['image']
            price = request.json['price']

            with sqlite3.connect("UTA_Enrollment") as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO products("
                               "user_id, "
                               "title, "
                               "description, "
                               "image, "
                               "price) VALUES(?, ?, ?, ?, ?)", (user_id, title, description, image, price))
                conn.commit()
                response["message"] = "New product successfully added to database"
                response["status_code"] = 201
            return response
        except ValueError:
            response["message"] = "Failed to create new product"
            response["status_code"] = 209
            return response


@app.route('/product/<int:user_id>', methods=["GET"])
def get_user_products(user_id):
    response = {}

    # GET ALL PRODUCTS
    if request.method == "GET":
        with sqlite3.connect("UTA_Enrollment") as conn:
            conn.row_factory = jdata
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE user_id=" + str(user_id))
            user_products = cursor.fetchall()

        response['status_code'] = 200
        response['data'] = user_products
        return response


if __name__ == '__main__':
    app.run()
