#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created on Tue Mar  4 11:05:12 2014
# MIT Licensed. See COPYING.TXT for more information.
""" Main application file """

from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
