from flask import Flask
app = Flask(__name__)

@app.route('/print', methods=['GET'])
def print_hello():
    print("hello")
    return jsonify({"message": "Hello from Flask!"})

if __name__ == "__main__":
    app.run()
