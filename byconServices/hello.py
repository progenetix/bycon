#!/usr/local/bin/python3

from flask import Flask
app=Flask(__name__)
@app.route('/hello')
def hello():
    return 'Hello World'
