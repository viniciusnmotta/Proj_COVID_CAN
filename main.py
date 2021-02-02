from flask import Flask, render_template, url_for, redirect, request, Response
# from flask_bootstrap import Bootstrap
from datetime import datetime
import requests
import pandas as pd
import io
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.dates as mdates



app = Flask(__name__)
# app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
# Bootstrap(app)

prname = "Canada"
province_list = ['Ontario', 'British Columbia', 'Canada', 'Quebec', 'Alberta', 'Saskatchewan',
 'Manitoba', 'New Brunswick', 'Newfoundland and Labrador', 'Nova Scotia',
 'Prince Edward Island', 'Northwest Territories', 'Nunavut', 'Yukon']

@app.route("/message", methods=['GET', "POST"])
def home():
    if request.method == 'POST':
        return render_template('message.html')
    return redirect(url_for('plot'))

@app.route("/", methods=['GET', 'POST'])
def plot():
    global prname
    prname = 'Canada'
    year = datetime.now().year

    response = requests.get('https://health-infobase.canada.ca/src/data/covidLive/covid19.csv')
    df = pd.read_csv(io.StringIO(response.text), parse_dates=['date'], dayfirst=True)
    quebec = df.loc[df['prname'] == prname]
    past_days = quebec[['date', 'prname', 'numtoday', 'numdeathstoday']].tail(7)
    past_days.columns=['Date', 'Province', 'Num of Cases', 'Num of Deaths']

    if request.method == "POST":
        if request.form['region'] != "" and request.form['region'] in province_list:
            prname = request.form['region']
            quebec = df.loc[df['prname'] == prname]
            past_days = quebec[['date', 'prname','numtoday','numdeathstoday']].tail(7)
            past_days.columns = ['Date', 'Province', 'Num of Cases', 'Num of Deaths']
            return render_template('index.html', df=past_days.to_html(classes='last-days', index=False),year=year)
        else:
            return render_template('index.html', is_wrong=True, year=year)

    return render_template('index.html', df=past_days.to_html(classes='last-days', index=False), is_wrong=False, year=year)



@app.route("/plot.png", methods=['GET','POST'])
def make_plot():
    now2 = datetime.now().strftime("%b %d, %Y")
    global prname
    province = prname

    response = requests.get('https://health-infobase.canada.ca/src/data/covidLive/covid19.csv')
    df = pd.read_csv(io.StringIO(response.text), parse_dates=['date'], dayfirst=True)
    quebec = df.loc[df['prname'] == province]
    quebec['rolling_cases'] = quebec['numtoday'].rolling(window=7).mean()
    quebec['rolling_deaths'] = quebec['numdeathstoday'].rolling(window=7).mean()


    fig = Figure()
    # fig.set_figheight(5)
    # fig.set_figwidth(8)
    ax1 = fig.gca()
    ax2 = ax1.twinx()
    ax1.plot(quebec['date'], quebec['rolling_cases'], color='blue', label='cases')
    ax2.plot(quebec['date'], quebec['rolling_deaths'], color='crimson', label='deaths', linestyle='--')

    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax1.tick_params(axis='x', labelrotation=90, labelsize=7)
    ax1.tick_params(axis="y", labelcolor='blue')
    ax2.tick_params(axis='y', labelcolor='crimson')
    ax1.set_ylabel('Number of Cases', color='blue')
    ax2.set_ylabel('Number of Deaths', color='crimson')
    ax1.set_title(f"COVID-19 Data for {province} as of {now2}")
    ax1.legend(bbox_to_anchor=(0.19, 1), frameon=False)#bbox_to_anchor=(0.2, 1)
    ax2.legend(bbox_to_anchor=(0.2, 0.95), frameon=False)#,bbox_to_anchor=(0.1, 0.1)

    output = io.BytesIO()
    FigureCanvasAgg(fig).print_png(output)
    return Response(output.getvalue(), mimetype="image/png")


if __name__ == "__main__":
    app.run(debug=True)
