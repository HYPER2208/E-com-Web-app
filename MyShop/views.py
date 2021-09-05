from flask import Flask, render_template, request, url_for, redirect, abort, session, Blueprint
from flask_session import Session
from .models import *
import os

views = Blueprint('views',__name__)

@views.route('/')
def home():
    return redirect(url_for('auth.login'))

@views.route("/seller/", methods=["POST", "GET"])
def S_home():
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    if session["type"]=="Customer":
        abort(403)
    categories = get_categories(session["userid"])
    if request.method=="POST":
        data = request.form
        srchBy = data["search method"]
        category = None if srchBy=='by keyword' else data["category"]
        keyword = data["keyword"]
        results = search_myproduct(session['userid'], srchBy, category, keyword)
        return render_template('my_products.html', signedin=True, id=session['userid'], name=session['name'], type=session['type'], categories=categories, after_srch=True, results=results)
    return render_template("my_products.html", signedin=True, id=session['userid'], name=session['name'], type=session['type'], categories=categories, after_srch=False)

@views.route("/customer/", methods=["POST", "GET"])
def C_home():
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    if session['type']=="Seller":
        abort(403)
    if request.method=="POST":
        data = request.form
        srchBy = data["search method"]
        category = None if srchBy=='by keyword' else data["category"]
        keyword = data["keyword"]
        results = search_products(srchBy, category, keyword)
        return render_template('search_products.html', signedin=True, id=session['userid'], name=session['name'], type=session['type'], after_srch=True, results=results)
    return render_template('search_products.html', signedin=True, id=session['userid'], name=session['name'], type=session['type'], after_srch=False)

#for my profile
@views.route("/viewprofile/<id>/")
def view_profile(id):
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    userid = session["userid"]
    type = session["type"]
    my = True if userid==id else False
    if not my: profile_type = "Customer" if type=="Seller" else "Seller"
    else: profile_type = type

    det, categories = fetch_details(id, profile_type)   #details
    if len(det)==0:
        abort(404)
    det = det[0]
    return render_template("view_profile.html",
                            signedin=True, 
                            id=session['userid'], 
                            type=profile_type,
                            name=det[1],
                            email=det[2],
                            phone=det[3],
                            area=det[4],
                            locality=det[5],
                            city=det[6],
                            state=det[7],
                            country=det[8],
                            zip=det[9],
                            category=(None if profile_type=="Customer" else categories),
                            my=my)

#for view of diffrent profile
@views.route("/viewprofile/", methods=["POST", "GET"])
def profile():
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    type = "Seller" if session['type']=="Customer" else "Customer"
    if request.method=="POST":
        search = request.form['search']
        results = search_users(search, type)
        found = len(results)
        return render_template('profiles.html', type=type, after_srch=True, found=found, results=results)

    return render_template('profiles.html', id=session['userid'], type=type, after_srch=False)

@views.route("/viewprofile/<id>/sellerproducts/")
def seller_products(id):
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    if session["type"]=="Seller":
        abort(403)
    det, categories = fetch_details(id, "Seller")   #details
    if len(det)==0:
        abort(404)
    det = det[0]
    name=det[1]
    res = get_seller_products(id)
    return render_template('seller_products.html', name=name, id=id, results=res)

@views.route("/editprofile/", methods=["POST", "GET"])
def edit_profile():
    if 'userid' not in session:
        return redirect(url_for('auth.login'))

    if request.method=="POST":
        data = request.form
        update_details(data, session['userid'], session['type'])
        return redirect(url_for('views.view_profile', id=session['userid']))

    if request.method=="GET":
        userid = session["userid"]
        type = session["type"]
        det, _ = fetch_details(userid, type)
        det = det[0]
        return render_template("edit_profile.html", 
                                signedin=True, 
                                id=session['userid'],
                                type=type,
                                name=det[1],
                                email=det[2],
                                phone=det[3],
                                area=det[4],
                                locality=det[5],
                                city=det[6],
                                state=det[7],
                                country=det[8],
                                zip=det[9])

@views.route("/changepassword/", methods=["POST", "GET"])
def change_password():
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    check = True
    equal = True
    if request.method=="POST":
        userid = session["userid"]
        type = session["type"]
        old_psswd = request.form["old_psswd"]
        new_psswd = request.form["new_psswd"]
        cnfrm_psswd = request.form["cnfrm_psswd"]
        check = check_psswd(old_psswd, userid, type)
        if check:
            equal = (new_psswd == cnfrm_psswd)
            if equal:
                set_psswd(new_psswd, userid, type)
                if session['type'] == 'Seller':
                    return redirect(url_for('views.S_home'))
                else:
                    return redirect(url_for('views.C_home'))

    return render_template("change_password.html",
                             signedin=True, 
                             id=session['userid'], 
                             name=session['name'], 
                             type=session['type'], 
                             check=check, 
                             equal=equal)

@views.route("/sell/addproducts/", methods=["POST", "GET"])
def add_products():
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    if session["type"]=="Customer":
        abort(403)
    if request.method=="POST":
        data = request.form
        add_prod(session['userid'],data)
        return redirect(url_for('views.S_home'))
    return render_template("add_products.html", 
                            signedin=True, 
                            id=session['userid'], 
                            name=session['name'], 
                            type=session['type'])

@views.route("/viewproduct/<id>/")
def view_product(id):
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    type = session["type"]
    ispresent, tup = get_product_info(id)
    if not ispresent:
        abort(404)
    (prod_name, quantity, category, cost_price, sell_price, sellID, desp, sell_name) = tup
    if type=="Seller" and sellID!=session['userid']:
        abort(403)
    return render_template('view_product.html',
                            signedin=True, 
                            type=type, 
                            prod_name=prod_name, 
                            quantity=quantity, 
                            category=category, 
                            cost_price=cost_price, 
                            sell_price=sell_price, 
                            id=session['userid'], 
                            name=sell_name, 
                            desp=desp, 
                            prod_id=id)

@views.route("/viewproduct/<id>/edit/", methods=["POST", "GET"])
def edit_product(id):
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    if session['type']=="Customer":
        abort(403)
    ispresent, tup = get_product_info(id)
    if not ispresent:
        abort(404)
    (name, quantity, category, cost_price, sell_price, sellID, desp, sell_name) = tup
    if sellID!=session['userid']:
        abort(403)
    if request.method=="POST":
        data = request.form
        update_product(data, id)
        return redirect(url_for('views.view_product', id=id))
    return render_template('edit_product.html', 
                            id=sellID, 
                            name=sell_name, 
                            signedin=True, 
                            type=session['type'], 
                            prodID=id, prod_name=name, 
                            qty=quantity, 
                            category=category, 
                            price=cost_price, 
                            desp=desp)

@views.route("/buy/<id>/", methods=['POST', 'GET'])
def buy_product(id):
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    if session['type']=="Seller":
        abort(403)
    ispresent, tup = get_product_info(id)
    if not ispresent:
        abort(404)
    (prod_name, quantity, category, cost_price, sell_price, sellID, desp, sell_name) = tup
    if request.method=="POST":
        data = request.form
        total = int(data['qty'])*float(sell_price)
        return redirect(url_for('views.buy_confirm', total=total, quantity=data['qty'], id=id))
    return render_template('buy_product.html',
                            signedin=True, 
                            name=sell_name, 
                            type=session['type'], 
                            id=session['userid'], 
                            prod_name=prod_name, 
                            category=category, 
                            desp=desp, 
                            quantity=quantity, 
                            price=sell_price)

@views.route("/buy/<id>/confirm/", methods=["POST", "GET"])
def buy_confirm(id):
    if 'userid' not in session:
        return redirect(url_for('home'))
    if session['type']=="Seller":
        abort(403)
    ispresent, tup = get_product_info(id)
    if not ispresent:
        abort(404)
    (prod_name, quantity, category, cost_price, sell_price, sellID, desp, sell_name) = tup
    if 'total' not in request.args or 'quantity' not in request.args:
        abort(404)
    total = request.args['total']
    qty = request.args['quantity']
    if request.method=="POST":
        choice = request.form['choice']
        if choice=="PLACE ORDER":
            place_order(id, session['userid'], qty)
            return redirect(url_for('views.my_orders'))
        elif choice=="CANCEL":
            return redirect(url_for('views.buy_product', id=id))
    items = ((prod_name, qty, total),)
    return render_template('buy_confirm.html', 
                            signedin=True, 
                            id=session['userid'], 
                            name=sell_name, 
                            type=session['type'], 
                            items=items, total=total)

@views.route("/buy/myorders/")
def my_orders():
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    if session['type']=="Seller":
        abort(403)
    res = cust_orders(session['userid'])
    return render_template('my_orders.html', 
                            id=session['userid'], 
                            name=session['name'], 
                            type=session['type'], 
                            orders=res, 
                            signedin=True)

@views.route("/cancel/<orderID>/")
def cancel_order(orderID):
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    res = get_order_details(orderID)
    if len(res)==0:
        abort(404)
    custID = res[0][0]
    sellID = res[0][1]
    status = res[0][2]
    if session['type']=="Seller" and sellID!=session['userid']:
        abort(403)
    if session['type']=="Customer" and custID!=session['userid']:
        abort(403)
    if status!="PLACED":
        abort(404)
    change_order_status(orderID, "CANCELLED")
    return redirect(url_for('views.my_orders')) if session['type']=="Customer" else redirect(url_for('views.new_orders'))

@views.route("/dispatch/<orderID>/")
def dispatch_order(orderID):
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    if session['type']=="Customer":
        abort(403)
    res = get_order_details(orderID)
    if len(res)==0:
        abort(404)
    custID = res[0][0]
    sellID = res[0][1]
    status = res[0][2]
    if session['userid']!=sellID:
        abort(403)
    if status!="PLACED":
        abort(404)
    change_order_status(orderID, "DISPACHED")
    return redirect(url_for('views.new_orders'))

@views.route("/recieve/<orderID>/")
def recieve_order(orderID):
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    if session['type']=="Seller":
        abort(403)
    res = get_order_details(orderID)
    if len(res)==0:
        abort(404)
    custID = res[0][0]
    sellID = res[0][1]
    status = res[0][2]
    if session['userid']!=custID:
        abort(403)
    if status!="DISPACHED":
        abort(404)
    change_order_status(orderID, "RECIEVED")
    return redirect(url_for('views.my_purchases'))

@views.route("/buy/purchases/")
def my_purchases():
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    if session['type']=="Seller":
        abort(403)
    res = cust_purchases(session['userid'])
    return render_template('my_purchases.html', 
                            signedin=True, 
                            id=session['userid'], 
                            name=session['name'], 
                            type=session['type'], 
                            purchases=res)

@views.route("/sell/neworders/")
def new_orders():
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    if session['type']=="Customer":
        abort(403)
    res = sell_orders(session['userid'])
    return render_template('new_orders.html', 
                            signedin=True, 
                            id=session['userid'], 
                            name=session['name'], 
                            type=session['type'], 
                            orders=res)

@views.route("/sell/sales/")
def my_sales():
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    if session['type']=="Customer":
        abort(403)
    res = sell_sales(session['userid'])
    return render_template('my_sales.html', 
                            signedin=True, 
                            id=session['userid'], 
                            name=session['name'], 
                            type=session['type'], 
                            orders=res)


@views.route("/buy/cart/", methods=["POST", "GET"])
def my_cart():
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    if session['type']=="Seller":
        abort(403)
    cart = get_cart(session['userid'])
    if request.method=="POST":
        data = request.form
        qty = {}
        for i in data:
            if i.startswith("qty"):
                qty[i[3:]]=data[i]      #qty[prodID]=quantity
        update_cart(session['userid'], qty)
        return redirect("/buy/cart/confirm/")
    return render_template('my_cart.html', 
                            signedin=True, 
                            id=session['userid'], 
                            name=session['name'], 
                            type=session['type'], 
                            cart=cart)

@views.route("/buy/cart/confirm/", methods=["POST", "GET"])
def cart_purchase_confirm():
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    if session['type']=="Seller":
        abort(403)
    if request.method=="POST":
        choice = request.form['choice']
        if choice=="PLACE ORDER":
            cart_purchase(session['userid'])
            return redirect(url_for('views.my_orders'))
        elif choice=="CANCEL":
            return redirect(url_for('views.my_cart'))
    cart = get_cart(session['userid'])
    items = [(i[1], i[3], float(i[2])*float(i[3])) for i in cart]
    total = 0
    for i in cart:
        total += float(i[2])*int(i[3])
    return render_template('buy_confirm.html', 
                            signedin=True, 
                            id=session['userid'], 
                            name=session['name'], 
                            type=session['type'], 
                            items=items, 
                            total=total)

@views.route("/buy/cart/<prodID>/")
def add_to_cart(prodID):
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    if session['type']=="Seller":
        abort(403)
    add_product_to_cart(prodID, session['userid'])
    return redirect(url_for('views.view_product', id=prodID))

@views.route("/buy/cart/delete/")
def delete_cart():
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    if session['userid']=="Seller":
        abort(403)
    empty_cart(session['userid'])
    return redirect(url_for('views.my_cart'))

@views.route("/buy/cart/delete/<prodID>/")
def delete_prod_cart(prodID):
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    if session['userid']=="Seller":
        abort(403)
    remove_from_cart(session['userid'], prodID)
    return redirect(url_for('views.my_cart'))
