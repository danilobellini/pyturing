#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created on Tue Mar  4 11:05:12 2014
# MIT Licensed. See COPYING.TXT for more information.

from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Turing machine!"

if __name__ == "__main__":
    app.run(debug=True)