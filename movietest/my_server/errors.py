from my_server import app
from flask import render_template

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors.html', error_num = 404, error_text = 'File not found'), 404

@app.errorhandler(401)
def not_found_error(error):
    return render_template('errors.html', error_num = 401, error_text = 'Unauthorized request'), 401

@app.errorhandler(400)
def not_found_error(error):
    return render_template('errors.html', error_num = 400, error_text = 'Bad request'), 400
