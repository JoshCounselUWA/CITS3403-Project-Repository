import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session as flask_session
from forms import LoginForm, RegistrationForm
from werkzeug.security import check_password_hash, generate_password_hash
from models import session, Inventory, Request, Account, RequestItems, Status, Department, Branding
from flask_cors import CORS
from flask import flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

app = Flask(__name__, template_folder="../Pages", static_folder="../Static")
app.config['SECRET_KEY'] = 'need_to_change_this_later_secret_key'
CORS(app)
login = LoginManager(app)
login.login_view = 'login'

@login.user_loader
def load_user(id):
    return session.query(Account).get(int(id))

def parse_datetime(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M")

#view dashboard
@app.route('/dashboard')
@login_required
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

    # ensure one branding row exists
    branding = session.query(Branding).first()
    if not branding:
        branding = Branding(logoURL=None)
        session.add(branding)
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

        login_user(user, remember=form.remember_me.data)
        flash(f'Welcome, {user.fName}!')
        return redirect(url_for('dashboard'))
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out succesfully')
    return redirect(url_for('login'))

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
@login_required
def inventory():
    items = session.query(Inventory).all()

    for item in items:
        outgoing_items = (
            session.query(RequestItems)
            .join(Request, RequestItems.requestID == Request.requestID)
            .filter(
                RequestItems.itemID == item.itemID,
                Request.status.in_([
                    Status.waiting,
                    Status.approved,
                    Status.loaned
                ])
            )
            .all()
        )

        quantity_outgoing = sum(ri.quantity for ri in outgoing_items)
        item.quantityAvailable = max(
            (item.itemquantity or 0) - quantity_outgoing,
            0
        )

    return render_template("inventory.html", items=items)

@app.route('/inventory/json')
@login_required
def inventory_json():
    items = session.query(Inventory).all()
    result = []

    for item in items:
        outgoing_items = (
            session.query(RequestItems)
            .join(Request, RequestItems.requestID == Request.requestID)
            .filter(
                RequestItems.itemID == item.itemID,
                Request.status.in_([
                    Status.waiting,
                    Status.approved,
                    Status.loaned
                ])
            )
            .all()
        )

        quantity_outgoing = sum(ri.quantity for ri in outgoing_items)
        quantity_available = max((item.itemquantity or 0) - quantity_outgoing, 0)

        result.append({
            "itemID": item.itemID,
            "itemName": item.itemName,
            "itemDescription": item.itemDescription,
            "itemquantity": quantity_available,
            "quantityOwned": item.itemquantity,
            "itemphoto": item.itemphoto
        })

    return jsonify({
        "items": result
    })

#add inventory
@app.route('/inventory/add', methods=['POST'])
@login_required
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
@login_required
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
@login_required
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
@login_required
def requests_page():
    requests = session.query(Request).all()
    return render_template("requests.html", requests=requests)

#make request
@app.route('/requests/add', methods=['POST'])
@login_required
def add_request():
    new_request = Request(
        requestTitle=request.form['requestTitle'],
        requestJustification=request.form['requestJustification'],
        eventDateStart=parse_datetime(request.form.get('eventDateStart')),
        eventDateEnd=parse_datetime(request.form.get('eventDateEnd')),
        returnDate=parse_datetime(request.form.get('returnDate')),
        requesterID=request.form['requesterID'],
        departmentID=request.form['departmentID']
    )

    session.add(new_request)
    session.commit()

    items_json = request.form.get('itemsJSON', '[]')

    try:
        selected_items = json.loads(items_json)
    except json.JSONDecodeError:
        selected_items = []

    for item in selected_items:
        request_item = RequestItems(
            requestID=new_request.requestID,
            itemID=item['itemID'],
            quantity=item['quantity']
        )
        session.add(request_item)

    session.commit()

    return redirect(url_for('requests_page'))

@app.route('/requests/items/<int:request_id>')
@login_required
def get_request_items(request_id):
    request_items = session.query(RequestItems).filter_by(requestID=request_id).all()

    items = []

    for request_item in request_items:
        inventory_item = session.query(Inventory).get(request_item.itemID)

        if inventory_item:
            outgoing_items = (
                session.query(RequestItems)
                .join(Request, RequestItems.requestID == Request.requestID)
                .filter(
                    RequestItems.itemID == inventory_item.itemID,
                    Request.status.in_([
                        Status.waiting,
                        Status.approved,
                        Status.loaned
                    ])
                )
                .all()
            )

            quantity_outgoing = sum(ri.quantity for ri in outgoing_items)
            quantity_available = max((inventory_item.itemquantity or 0) - quantity_outgoing, 0)

            items.append({
                "itemID": inventory_item.itemID,
                "itemName": inventory_item.itemName,
                "itemquantity": quantity_available + request_item.quantity,
                "quantityOwned": inventory_item.itemquantity,
                "quantity": request_item.quantity
            })

    return jsonify({
        "items": items
    })

#delete request
@app.route('/requests/delete/<int:request_id>')
@login_required
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
@login_required
def update_request(request_id):
    req = session.query(Request).get(request_id)

    if not req:
        flash('Request not found', 'error')
        return redirect(url_for('requests_page'))

    # update fields
    if 'requestTitle' in request.form:
        req.requestTitle = request.form['requestTitle']

    if 'requestJustification' in request.form:
        req.requestJustification = request.form['requestJustification']

    if 'eventDateStart' in request.form:
        req.eventDateStart = parse_datetime(request.form.get('eventDateStart'))

    if 'eventDateEnd' in request.form:
        req.eventDateEnd = parse_datetime(request.form.get('eventDateEnd'))

    if 'returnDate' in request.form:
        req.returnDate = parse_datetime(request.form.get('returnDate'))

    if 'overdue' in request.form:
        req.overdue = request.form['overdue']

    if 'approverID' in request.form:
        req.approverID = request.form['approverID']

    if 'departmentID' in request.form:
        req.departmentID = request.form['departmentID']

    from models import Status
    req.status = Status.waiting

    # delete old items
    session.query(RequestItems).filter_by(requestID=request_id).delete()


    # add updated items
    items_json = request.form.get('itemsJSON', '[]')

    try:
        selected_items = json.loads(items_json)
    except json.JSONDecodeError:
        selected_items = []

    for item in selected_items:
        request_item = RequestItems(
            requestID=request_id,
            itemID=item['itemID'],
            quantity=item['quantity']
        )
        session.add(request_item)

    session.commit()

    return redirect(url_for('requests_page'))

#approve
@app.route('/requests/approve/<int:request_id>', methods=['GET', 'POST'])
@login_required
def approve_request(request_id):
    req = session.query(Request).get(request_id)

    if not req:
        flash('Request not found', 'error')
        return redirect(url_for('requests_page'))
    
    from models import Status
    req.status = Status.approved
    session.commit()

    return redirect(url_for('requests_page'))

#decline
@app.route('/requests/decline/<int:request_id>', methods=['GET', 'POST'])
@login_required
def decline_request(request_id):
    req = session.query(Request).get(request_id)

    if not req:
        flash('Request not found', 'error')
        return redirect(url_for('requests_page'))
    
    from models import Status
    req.status = Status.rejected
    session.commit()
    
    return redirect(url_for('requests_page'))

#late return
@app.route("/requests/overdue")
@login_required
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
@login_required
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
@login_required
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

#calender
@app.route("/requests/calendar")
@login_required
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

@app.route('/appsettings')
def appsettings():
    departments = session.query(Department).all()
    users = session.query(Account).all()
    return render_template("appsettings.html", departments=departments, users=users)


@app.route('/appsettings/departments/add', methods=['POST'])
def add_department():
    name = request.form['departmentName']

    new_dept = Department(departmentName=name)
    session.add(new_dept)
    session.commit()

    return redirect(url_for('appsettings'))


@app.route('/appsettings/departments/delete/<int:dept_id>')
def delete_department(dept_id):
    dept = session.query(Department).get(dept_id)

    if dept:
        session.delete(dept)
        session.commit()

    return redirect(url_for('appsettings'))


@app.route('/appsettings/users/<int:user_id>', methods=['POST'])
def update_user(user_id):
    user = session.query(Account).get(user_id)

    if user:
        # update account type (always apply immediately)
        if 'accountType' in request.form:
            user.accountType = request.form['accountType']

        # check if department changed
        if 'departmentID' in request.form:
            new_department = int(request.form['departmentID'])

            if user.departmentID != new_department:
                user.departmentID = new_department
                user.inviteAccepted = False  # trigger invite

        session.commit()

    return redirect(url_for('appsettings'))


@app.route('/appsettings/branding', methods=['POST'])
def update_branding():
    url = request.form['logoURL'].strip()

    branding = session.query(Branding).first()

    if branding:
        branding.logoURL = url if url else None

    session.commit()

    return redirect(url_for('appsettings'))

@app.context_processor
def inject_branding():
    return dict(branding=session.query(Branding).first())

@app.route('/appsettings/departments/update/<int:dept_id>', methods=['POST'])
def update_department(dept_id):
    dept = session.query(Department).get(dept_id)

    if dept:
        dept.departmentName = request.form['departmentName']
        session.commit()

    return redirect(url_for('appsettings'))

if __name__ == "__main__":
    app.run(debug=True)