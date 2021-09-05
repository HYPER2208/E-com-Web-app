from flask import Flask, render_template, request, url_for, redirect, abort, session, Blueprint, flash
from flask_session import Session
from .models import *
import os


auth = Blueprint('auth',__name__)

@auth.route("/sign-up/", methods = ["POST", "GET"])
def signup():
    if request.method == "POST":
        data = request.form
        ok = add_user(data)
        if ok:
            return render_template("success_signup.html")
        return render_template("signup.html", ok=ok)
    return render_template("signup.html", ok=True)

@auth.route("/login/", methods=["POST", "GET"])
def login():
    if 'userid' in session:
        if session['type'] == 'Seller':
            return redirect(url_for('views.S_home'))
        else:
            return redirect(url_for('views.C_home'))
            
    if request.method == "POST":
        data = request.form
        #verify user
        userdat = auth_user(data)
        if userdat:
            session["userid"] = userdat[0]
            session["name"] = userdat[1]
            session["type"] = data["type"]
            if session["type"] == 'Customer':
                return redirect(url_for('views.C_home'))
            else:
                return redirect(url_for('views.S_home'))

        return render_template("login.html", err=True)
    return render_template("login.html", err=False)

@auth.route("/logout/")
def logout():
    session.pop('userid')
    session.pop('name')
    session.pop('type')
    return redirect(url_for('auth.login'))