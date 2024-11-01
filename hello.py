from flask import Flask, request, jsonify
from sms_parser import parse_sms_list
from flask_pymongo import PyMongo
from bson import ObjectId

app = Flask(__name__)

# Configure the MongoDB URI
app.config["MONGO_URI"] = "mongodb+srv://groceryadmin:YUHzVnS5UC1XqqA6@grocery-cluster.uwe15mr.mongodb.net/grocery-cluster?retryWrites=true&w=majority&appName=grocery-cluster"
mongo = PyMongo(app)

# Database connection check
def initialize_db():
    try:
        mongo.db.transactions.find_one()
        print("Connected to the database")
    except Exception as e:
        print(f"Error connecting to the database: {e}")

# Helper function to convert ObjectIds to strings
def json_serializer(data):
    if isinstance(data, list):
        for item in data:
            if "_id" in item:
                item["_id"] = str(item["_id"])
    elif "_id" in data:
        data["_id"] = str(data["_id"])
    return data

@app.route('/parse-sms', methods=['POST'])
def parse_sms():
    """Endpoint to parse and save SMS messages for a specific user."""
    try:
        data = request.json  # Expecting JSON with 'user_id' and 'sms_list'
        print("Received request data:", data)  # Log data for debugging

        if not data or 'user_id' not in data or 'sms_list' not in data:
            return jsonify({'error': 'Invalid input, expected user_id and sms_list'}), 400

        user_id = data['user_id']
        sms_list = data['sms_list']

        if not isinstance(sms_list, list):
            return jsonify({'error': '"sms_list" must be a list'}), 400

        # Parse the SMS data
        parsed_data = parse_sms_list(sms_list)

        # Add user_id to each SMS entry
        for sms in parsed_data:
            sms['user_id'] = user_id

        # Insert parsed data into MongoDB
        insert_result = mongo.db.transactions.insert_many(parsed_data)
        print("Inserted to DB:", parsed_data)

        # Update parsed_data with MongoDB IDs
        for record, insert_id in zip(parsed_data, insert_result.inserted_ids):
            record["_id"] = insert_id

        # Serialize ObjectIds for JSON response
        json_serialized_data = json_serializer(parsed_data)

        return jsonify(json_serialized_data), 200
    except Exception as e:
        print("Error in /parse-sms:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/user/<user_id>/transactions', methods=['GET'])
def get_user_transactions(user_id):
    """Fetch all transactions for a specific user."""
    try:
        transactions = list(mongo.db.transactions.find({"user_id": user_id}))
        if not transactions:
            return jsonify({'message': 'No transactions found for this user'}), 404
        # print("Transactions fetched:", transactions) 
        json_serialized_data = json_serializer(transactions)
        return jsonify(json_serialized_data), 200
    except Exception as e:
        print("Error in /user/<user_id>/transactions:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/print', methods=['GET'])
def print_hello():
    print("hello")
    return jsonify({"message": "Hello from Flask!"})

if __name__ == '__main__':
    initialize_db()
    app.run(debug=True, host='0.0.0.0', port=5001)

