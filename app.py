from flask import Flask, render_template, request, Markup,redirect,url_for
import numpy as np
import pandas as pd
import requests
import config
import pickle
import io
from PIL import Image
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
import csv

# Load ML model
#forest = pickle.load(open('models/yield_rf.pkl', 'rb'))  # yield
cr1 = pickle.load(open('models/RandomForest.pkl', 'rb')) #crop
# =========================================================================================

def weather_fetch(city_name):
    """
    Fetch and returns the temperature and humidity of a city
    :params: city_name
    :return: temperature, humidity
    """
    api_key = config.weather_api_key
    base_url = "http://api.openweathermap.org/data/2.5/weather?"

    complete_url = base_url + "appid=" + api_key + "&q=" + city_name
    response = requests.get(complete_url)
    x = response.json()
    print('vgj,hDS|m n')
    print(response)

    if x["cod"] != "404":
        y = x["main"]

        temperature = round((y["temp"] - 273.15), 2)
        humidity = y["humidity"]
        return temperature, humidity
    else:
        return None
  

connection = sqlite3.connect('user_data.db')
cursor = connection.cursor()

cursor.execute("create table if not exists admin(email TEXT, password TEXT)")
cursor.execute("create table if not exists former(name TEXT, phone TEXT, gender TEXT, email TEXT, password TEXT)")
cursor.execute("create table if not exists soilreport(email TEXT, n TEXT, k TEXT, ph TEXT, p TEXT)")

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/addformer')
def addformer():
    return render_template('adminlog.html')

@app.route('/Demandcheck')
def Demandcheck():
    return render_template('formerlog.html')

@app.route('/Suggestion')
def Suggestion():
    f = open('session.txt', 'r')
    email = f.readline()
    f.close()
    print(email)

    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()

    cursor.execute("SELECT n, k, ph, p FROM soilreport where email = '"+email+"'")
    result = cursor.fetchone()
    n, k, ph, p = result
    print(n, k, ph, p)
    return render_template('suggestion.html', n=n, k=k, ph=ph, p=p)

# render crop recommendation result page
@ app.route('/crop_predict', methods=['POST'])
def crop_predict():
    title = 'Crop Recommended'
    if request.method == 'POST':
        n = request.form['nitrogen']
        p = request.form['phosphorous']
        k = request.form['pottasium']
        ph = request.form['ph']
        rainfall = request.form['rainfall']
        state = request.form['stt']
        city = request.form['city']

        if weather_fetch(city) != None:
            temperature, humidity = weather_fetch(city)
            data = np.array([[n, p, k, temperature, humidity, ph, rainfall]])
            my_prediction = cr1.predict(data)
            final_prediction = my_prediction[0]
            print(final_prediction)

            # df = pd.read_csv('demand.csv')
            # yeald = int(df.loc[(df['crops'] == final_prediction)]['yield'].values)
            # govt_demand = int(df.loc[(df['crops'] == final_prediction)]['demand'].values)
            # print(yeald, govt_demand)
            # for row in df:
            #     print("R",row)
            # print("FIND",df.loc[df['crops']==final_prediction])
            yeald=''
            govt_demand=''
            with open('demand.csv', 'r') as f:          # Read lines separately
                reader = csv.reader(f, delimiter=',')
                for i, line in enumerate(reader):
                    if line[0].lower() == str(final_prediction).lower():
                        print("RETURNING")
            msg = 'you can grow {} in your form and demand is {}'.format(final_prediction, line[1])
            return render_template('suggestion.html', msg=msg, n=n, k=k, ph=ph, p=p)
        else:
            
            return render_template('suggestion.html', msg = 'Check your values Please try again', n=n, k=k, ph=ph, p=p)

@app.route('/remove/<mail>')
def remove(mail):
    print(mail)
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()

    cursor.execute("delete from former where email = '"+mail+"'")
    connection.commit()

    cursor.execute("delete from soilreport where email = '"+mail+"'")
    connection.commit()

    return redirect(url_for('formerlist'))

@app.route('/formerlist')
def formerlist():
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()

    query = "SELECT * FROM former"
    cursor.execute(query)
    result = cursor.fetchall()

    return render_template('formerlist.html', result=result)

@app.route('/demand', methods=['GET', 'POST'])
def demand():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        acres = int(request.form['acres'])
        crop = request.form['crop']

        print(acres, crop)

        df = pd.read_csv('demand.csv')
        yeald = int(df.loc[(df['crops'] == crop)]['yield'].values)
        govt_demand = int(df.loc[(df['crops'] == crop)]['demand'].values)
        print(yeald, govt_demand)

        Demand = acres*yeald
        if govt_demand > 0 and govt_demand > Demand:
            govt_demand = govt_demand - Demand
            gd = df.loc[(df['crops'] == crop), 'demand'] = str(govt_demand)
            df.to_csv('demand.csv', index=False)
            msg = 'you can grow {}, total demand {} for {} and total yield is {}'.format(crop, govt_demand, crop, Demand)
            return render_template('formerlog.html', msg = msg)
        else:
            msg1 = "total demand {} for {} and total yield is {}".format(govt_demand, crop, Demand)
            return render_template('formerlog.html', msg1=msg1)

    return render_template('formerlog.html')

@app.route('/adminlog', methods=['GET', 'POST'])
def adminlog():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        email = request.form['email']
        password = request.form['password']

        query = "SELECT * FROM admin WHERE email = '"+email+"' AND password= '"+password+"'"
        cursor.execute(query)

        result = cursor.fetchall()
        print(result)
        if len(result) == 0:
            return render_template('index.html', msg='Sorry, Incorrect Credentials Provided,  Try Again')
        else:
            return render_template('adminlog.html', msg='Successfully login')

    return render_template('index.html')

@app.route('/formerlog', methods=['GET', 'POST'])
def formerlog():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        email = request.form['email']
        password = request.form['password']

        query = "SELECT * FROM former WHERE email = '"+email+"' AND password= '"+password+"'"
        cursor.execute(query)

        result = cursor.fetchall()
    
        if len(result) == 0:
            return render_template('index.html', msg='Sorry, Incorrect Credentials Provided,  Try Again')
        else:
            f = open('session.txt', 'w')
            f.write(email)
            f.close()
            return render_template('formerlog.html', msg='Successfully login')

    return render_template('index.html')

@app.route('/formerinfo', methods=['GET', 'POST'])
def formerinfo():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        data = []
        for d in request.form.values():
            data.append(d)

        personal = []
        for d in data[:5]:
            personal.append(d)
        
        soilreport = [data[3]]
        for d in data[5:]:
            soilreport.append(d)

        print(personal)
        print(soilreport)

        cursor.execute("insert into former values(?,?,?,?,?)", personal)
        connection.commit()
        cursor.execute("insert into soilreport values(?,?,?,?,?)", soilreport)
        connection.commit()
        return render_template('adminlog.html', msg='Former added Successfully')
    return render_template('index.html')

@app.route('/logout')
def logout():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
