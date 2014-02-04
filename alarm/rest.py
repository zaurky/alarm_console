# -*- coding: utf-8 -*-

import os
from flask import Flask, request, url_for, render_template
from alarm.shared import Action


app = Flask(__name__,
            static_url_path=os.path.dirname(os.path.dirname(__file__)))


@app.route('/')
def home():
    return app.send_static_file('/static/index.html')
#    return render_template(url_for('static', filename='index.html'))


@app.route("/alive")
def alive():
    return Action.alive()


@app.route("/photo")
def photo():
    return Action.photo()


@app.route("/status")
def status():
    return Action.status()


@app.route("/arm/<level>")
def arm(level=1):
    return Action.arm(level)


@app.route("/disarm")
def disarm():
    return Action.disarm()


@app.route("/mute")
def mute():
    return Action.mute()


@app.route("/logs")
def logs():
    return Action.logs()


@app.route("/droplogs")
def droplogs():
    return Action.droplogs()
