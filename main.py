#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created on Tue Mar  4 11:05:12 2014
# MIT Licensed. See COPYING.TXT for more information.
""" Main application file """

from flask import Flask, render_template, request
from turing import TuringMachine

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/", methods=["POST"])
def ajax_simulate():
    tm = TuringMachine(request.form["machine"])
    for el in range(3000):
      tm.move()
    return str(tm.tape)

if __name__ == "__main__":
    app.run(debug=True)
