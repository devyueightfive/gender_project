from flask import Flask
from flask import jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
import pickle
import os



# SQLAlchemy
engine = create_engine("mysql://flask_user:password@localhost/ftp", echo=False)
connection = engine.connect()
# create a configured "Session" class
Session = sessionmaker(bind=engine)
# create a Session
session = Session()

#load predictive model
PATH_TO_DATA = './models/'
with open(os.path.join(PATH_TO_DATA, 'A.pkl'), mode = 'rb') as file:
    production_model = pickle.load(file)


# flask
app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/count/<string:session_id>/<string:category>', methods=['GET'])
def get_count(session_id, category):
    result = session.execute(
        "SELECT * FROM (SELECT session_id AS SESSION_ID, category_a AS CATEGORY, count(*) AS COUNT from product GROUP BY session_id, category_a " + \
        "UNION SELECT session_id, category_b, count(*) from product GROUP BY session_id, category_b " + \
        "UNION SELECT session_id, category_c, count(*) from product GROUP BY session_id, category_c " + \
        "UNION SELECT session_id, category_d, count(*) from product GROUP BY session_id, category_d) AS counter " + \
        "WHERE SESSION_ID = :val1 AND CATEGORY = :val2", {'val1': session_id, 'val2': category}).first()

    if result:
        response = {'SESSION_ID': result[0], 'CATEGORY': result[1], 'COUNT': result[2]}
    else:
        response = {'SESSION_ID': session_id, 'CATEGORY': category, 'COUNT': 0}
    return jsonify(response)


@app.route('/predict/<string:session_id>', methods=['GET'])
def get_prediction(session_id):
    return jsonify(get_prediction_response(session_id))


def get_category_sequence(array):
    #     print(type(array))
    return " ".join([" ".join(row[-4:]) for row in array])


def create_vector(session_id):
    result = []
    categories = session.execute("SELECT * FROM product " + \
                                 "WHERE session_id = :val1", {'val1': session_id}).fetchall()
    time_data = session.execute("SELECT * FROM session " + \
                                "WHERE session_id = :val1", {'val1': session_id}).first()
    if categories and time_data:
        categories = get_category_sequence(categories)
        result.append(time_data[1].day)
        result.append(pd.Timestamp(time_data[1]).dayofweek)
        result.append(time_data[1].hour)
        result.append(categories)
        duration = (time_data[2] - time_data[1]).seconds
        number_of_views = int(len(categories.split()) / 4)
        result.append(number_of_views)
        result.append(duration / number_of_views)
        columns = 'day dayofweek start_hour categories number_of_views average_time_per_view'.split()
        return pd.DataFrame(data=[result], columns=columns)
    else:
        return None


def get_prediction_response(session_id):
    mapping_answer = {0: 'female', 1: 'male'}
    vector = create_vector(session_id)
    if vector is not None:
        prediction = production_model.predict(vector)[0]
        answer = mapping_answer[prediction]
        response = {'SESSION_ID': session_id, 'PREDICTION': answer}
    else:
        response = {'SESSION_ID': session_id, 'PREDICTION': 'UNKNOWN_SESSION_ID'}
    return response



if __name__ == '__main__':
    app.run()
