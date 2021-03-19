from flask import Flask, render_template, url_for
app = Flask(__name__)


stocks_data = [{'Stock': 'A',
        'Mean_Profit_Ratio': '1',
        'Std_Profit_Ratio': '2',
        'Sum_Profit_Ratio': '3'},

        {'Stock': 'B',
        'Mean_Profit_Ratio': '4',
        'Std_Profit_Ratio': '5',
        'Sum_Profit_Ratio': '6'},

        {'Stock': 'C',
        'Mean_Profit_Ratio': '7',
        'Std_Profit_Ratio': '8',
        'Sum_Profit_Ratio': '9'}]


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', stocks_data=stocks_data)


# @app.route("/about")
# def about():
# 	return render_template('about.html', title = 'About')


if __name__ == '__main__':
	app.run(debug=True)

