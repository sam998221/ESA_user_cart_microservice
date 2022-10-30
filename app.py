from flask import Flask, jsonify, request
import requests
import json
from pymongo import MongoClient
from bson import json_util
import urllib

app = Flask(__name__)

test_users = [
    {
        "uuid": 1,
        "cart": []
    },
    {
        "uuid": 2,
        "cart": []
    },
    {
        "uuid": 3,
        "cart": []
    }
]


def get_database():
    CONNECTION_STRING = "mongodb+srv://sam:" + \
        urllib.parse.quote(
            "12340987") + "@cluster0.cfkt66x.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(CONNECTION_STRING)
    db = client['product_list']
    col = db["products"]

    return col


def parse_data(data):
    return json.loads(json_util.dumps(data))


def validate_user(uuid):
    try:
        return test_users[uuid-1]
    except IndexError as error:
        print(error)
        return None


def get_product(prod_id, product_list):
    for product in product_list:
        if product['productId'] == prod_id:
            return product

    return None


def add_to_user_cart(user, cart_obj):
    for obj in user["cart"]:
        if obj["productId"] == cart_obj["productId"]:
            obj["quantity"] = obj["quantity"] + cart_obj["quantity"]
            obj["amount"] = obj["amount"] + cart_obj["amount"]
            return obj
    user["cart"].append(cart_obj)
    return cart_obj


@app.route('/rest/v1/users/<uuid>/cart', methods=['PUT'])
def add_to_cart(uuid):
    data = json.loads(request.data)

    quantity = data["quantity"]

    if data is not None:

        user = validate_user(int(uuid))

        if user is not None:
            try:
                response = requests.get(
                    "http://127.0.0.1:5000/rest/v1/products")
                product_list = response.json()["products"]
                product = get_product(data["productId"], product_list)

                if product is not None:
                    if int(product["availableQuantity"]) >= quantity:
                        cart_obj = {
                            "productId": product["productId"],
                            "productName": product["productName"],
                            "quantity": quantity,
                            "amount": int(product["price"]) * quantity
                        }

                        product_db = get_database()
                        query = {"productId": product["productId"]}
                        updates_values = {
                            "$set": {
                                "availableQuantity": int(product["availableQuantity"]) - quantity
                            }
                        }
                        product_db.update_one(query, updates_values)
                        cart_obj = add_to_user_cart(user, cart_obj)
                        return jsonify(cart_obj)
                    else:
                        return jsonify({
                            "error": "quantity greater than available",
                            "available": product["availableQuantity"]
                        })

                else:
                    return jsonify({"error": "product not found"})

            except requests.RequestException as error:
                return jsonify({"error": error})
        else:
            return jsonify({"error": "user not found"})
    else:
        return jsonify({"error": "No data found"})


@app.route('/rest/v1/users/<uuid>/cart', methods=['GET'])
def get_cart(uuid):
    user = validate_user(int(uuid))

    if user is not None:
        cart_list = user["cart"]
        return jsonify({"cart": cart_list})
    else:
        return jsonify({"error": "user not found"})


if __name__ == '__main__':
    app.run(port=5555)
