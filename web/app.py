from __future__ import absolute_import
from flask import (Flask, abort, flash, redirect, render_template,
                   request, url_for)
from tasks import fibonacci


app = Flask(__name__)
app.secret_key = "super secret key"


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('bg-form.html')

    # Calculate fibonacci in background
    if request.form['submit'] == 'Submit':
        try:
            number = int(request.form['number'])
            experiment = request.form['experiment']
            # send right away
            fibonacci.apply_async(args=[number, experiment])
            flash('Calculating fibonacci for {0}.'.format(number))
            return redirect(url_for('index'))
        except (KeyError, ValueError):
            abort(400)


if __name__ == '__main__':
    app.run(debug=True, port=5000,
            host='0.0.0.0')
