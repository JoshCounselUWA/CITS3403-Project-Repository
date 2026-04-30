from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from forms import LoginForm, RegistrationForm
from werkzeug.security import check_password_hash, generate_password_hash
from models import session, Inventory, Request, Account
from flask_cors import CORS
from flask import flash

app = Flask(__name__, template_folder="../Pages", static_folder="../Static")
app.config['SECRET_KEY'] = 'need_to_change_this_later_secret_key'
CORS(app)

#view dashboard
@app.route('/dashboard')
def dashboard():
    items = session.query(Inventory).all()
    requests = session.query(Request).all()
    return render_template("dashboard.html", items=items, requests=requests)

with app.app_context():
    existing = session.query(Account).filter_by(userName='testuser').first()
    if not existing:
        test_user = Account(
            fName='Test',
            lName='User',
            userName='testuser',
            password_hash=generate_password_hash('password123'),
            accountType='user'
        )
        session.add(test_user)
        session.commit()
  
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = session.query(Account).filter_by(userName=username).first()

        if user is None:
            flash('Invalid username')
            return redirect(url_for('login'))

        if not check_password_hash(user.password_hash, password):
            flash('Invalid password')
            return redirect(url_for('login'))

        flash(f'Welcome, {user.fName}!')
        return redirect(url_for('inventory'))

    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username is already taken or valid
        existing = session.query(Account).filter_by(userName=form.username.data).first()
        if existing:
            flash('Username already taken. Please try again.')
            return redirect(url_for('register'))

        # Create new account
        new_user = Account(
            fName=form.first_name.data,
            lName=form.last_name.data,
            userName=form.username.data,
            password_hash=generate_password_hash(form.password.data),
            accountType='user'
        )
        session.add(new_user)
        session.commit()

        flash('Account created! Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

#view inventory
@app.route('/inventory')
def inventory():
    items = session.query(Inventory).all()
    return render_template("inventory.html", items=items)

#add inventory
@app.route('/inventory/add', methods=['POST'])
def add_inventory():
    item = Inventory(
        itemName=request.form['itemName'],
        itemDescription=request.form['itemDescription'],
        itemquantity=request.form['itemquantity'],
        itemphoto=request.form['itemphoto'],
        departmentID=request.form['departmentID']
    )

    session.add(item)
    session.commit()

    return redirect(url_for('inventory'))

#delete inventory
@app.route('/inventory/delete/<int:item_id>')
def delete_inventory(item_id):
    item = session.query(Inventory).get(item_id)

    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('inventory'))
    else:
        session.delete(item)
        session.commit()

    return redirect(url_for('inventory'))

#update inventory
@app.route('/inventory/<int:item_id>', methods=['POST'])
def update_inventory(item_id):
    item = session.query(Inventory).get(item_id)

    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('inventory'))
    else:
        if 'itemName' in request.form:
            item.itemName = request.form['itemName']
        if 'itemDescription' in request.form:
            item.itemDescription = request.form['itemDescription']
        if 'itemquantity' in request.form:
            item.itemquantity = request.form['itemquantity']
        if 'itemphoto' in request.form:
            item.itemphoto = request.form['itemphoto']
        if 'departmentID' in request.form:
            item.departmentID = request.form['departmentID']

        session.commit()

    return redirect(url_for('inventory'))

#view requests
@app.route('/requests')
def requests_page():
    requests = session.query(Request).all()
    return render_template("requests.html", requests=requests)

#make request
@app.route('/requests/add', methods=['POST'])
def add_request():
    new_request = Request(
        requestTitle=request.form['requestTitle'],
        requestJustification=request.form['requestJustification'],
        eventDateStart=request.form.get('eventDateStart'),
        eventDateEnd=request.form.get('eventDateEnd'),
        returnDate=request.form.get('returnDate'),
        requesterID=request.form['requesterID'],
        departmentID=request.form['departmentID']
    )

    session.add(new_request)
    session.commit()

    return redirect(url_for('requests_page'))

#delete request
@app.route('/requests/delete/<int:request_id>')
def delete_request(request_id):
    req = session.query(Request).get(request_id)

    if not req:
        flash('Requset not found', 'error')
        return redirect(url_for('requests_page'))
    else:
        session.delete(req)
        session.commit()

    return redirect(url_for('requests_page'))

#update request
@app.route('/requests/<int:request_id>', methods=['POST'])
def update_request(request_id):
    req = session.query(Request).get(request_id)

    if not req:
        flash('Requset not found', 'error')
        return redirect(url_for('requests_page'))
    else:
        if 'requestTitle' in request.form:
            req.requestTitle = request.form['requestTitle']
        if 'requestJustification' in request.form:
            req.requestJustification = request.form['requestJustification']
        if 'status' in request.form:
            req.status = request.form['status']
        if 'eventDateStart' in request.form:
            req.eventDateStart = request.form['eventDateStart']
        if 'eventDateEnd' in request.form:
            req.eventDateEnd = request.form['eventDateEnd']
        if 'returnDate' in request.form:
            req.returnDate = request.form['returnDate']
        if 'overdue' in request.form:
            req.overdue = request.form['overdue']
        if 'approverID' in request.form:
            req.approverID = request.form['approverID']
        if 'departmentID' in request.form:
            req.departmentID = request.form['departmentID']

        session.commit()

    return redirect(url_for('requests_page'))

#late return
@app.route("/requests/overdue")
def get_overdue_requests():
    from datetime import datetime
    now = datetime.now()
    from models import Status
    overdue_requests = session.query(Request).filter(
        Request.returnDate < now,
        Request.status != Status.returned
    ).all()

    return jsonify([r.to_json() for r in overdue_requests])

#upcoming booking
@app.route("/requests/future")
def get_future_requests():
    from datetime import datetime
    now = datetime.now()
    from models import Status
    requests = session.query(Request).filter(
        Request.eventDateStart >= now,
        Request.status == Status.approved
    ).all()

    return jsonify([r.to_json() for r in requests])

#current loans
@app.route("/requests/current")
def get_current_requests():
    from datetime import datetime
    now = datetime.now()
    from models import Status
    current_requests = session.query(Request).filter(
        Request.eventDateStart <= now,
        Request.returnDate >= now,
        Request.status == Status.loaned
    ).all()

    return jsonify([r.to_json() for r in current_requests])

#calander
@app.route("/requests/calendar")
def get_calendar_events():
    from datetime import datetime
    now = datetime.now()
    from models import Status
    future = session.query(Request).filter(
        Request.eventDateStart >= now,
        Request.status == Status.approved
    ).all()

    current = session.query(Request).filter(
        Request.eventDateStart <= now,
        Request.returnDate >= now,
        Request.status == Status.loaned
    ).all()

    overdue = session.query(Request).filter(
        Request.returnDate < now,
        Request.status != Status.returned
    ).all()

    return jsonify({
        "future": [r.to_json() for r in future],
        "current": [r.to_json() for r in current],
        "overdue": [r.to_json() for r in overdue]
    })

if __name__ == "__main__":
    app.run(debug=True)