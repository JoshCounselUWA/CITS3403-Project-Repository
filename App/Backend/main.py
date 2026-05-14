import json
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session as flask_session
from forms import LoginForm, RegistrationForm
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from models import session, Inventory, Request, Account, RequestItems, Status, Department, Branding, AccountType, Membership, MembershipRole, MembershipStatus
from flask_cors import CORS
from flask import flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder="../Pages", static_folder="../Static")
app.config['SECRET_KEY'] = 'need_to_change_this_later_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join( os.path.dirname(__file__), '..', 'Static','uploads')
CORS(app)
login = LoginManager(app)
login.login_view = 'login'
login.login_message = None

def save_uploaded_image(file):
    filename = secure_filename(file.filename)
    upload_dir = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)

    path = os.path.join(upload_dir, filename)
    file.save(path)

    return f"/Static/uploads/{filename}"

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@login.user_loader
def load_user(id):
    return session.query(Account).get(int(id))

def parse_datetime(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M")

def business_admin_required(f):
    @wraps(f)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.accountType != "business_admin":
            abort(403)
        return f(*args, **kwargs)
    return wrapped

def dept_admin_required(f):
    @wraps(f)
    @login_required
    def wrapped(*args, **kwargs):
        dept_id = kwargs.get('dept_id') or kwargs.get('department_id')
        if current_user.accountType == "business_admin":
            return f(*args, **kwargs)
        if dept_id is None or not current_user.is_admin_of(dept_id):
            abort(403)
        return f(*args, **kwargs)
    return wrapped

#view dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    items = session.query(Inventory).all()
    requests = session.query(Request).all()
    pending_invites = (session.query(Membership).filter_by(userID=current_user.userID, status=MembershipStatus.pending).all())
    return render_template("dashboard.html", items=items, requests=requests, pending_invites=pending_invites)

with app.app_context():
    existing = session.query(Account).filter_by(userName='testuser').first()
    if not existing:
        test_user = Account(
            fName='Test',
            lName='User',
            userName='testuser',
            password_hash=generate_password_hash('password123'),
            accountType="business_admin"
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
        flash(f'Welcome, {user.fName}!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/account/password', methods=['POST'])
@login_required
def change_password():
    current_pw = request.form.get('current_password', '')
    new_pw = request.form.get('new_password', '')
    confirm_pw = request.form.get('confirm_password', '')

    # check current password
    if not check_password_hash(current_user.password_hash, current_pw):
        return jsonify({'error': 'Current password is incorrect'}), 400

    if new_pw != confirm_pw:
        return jsonify({'error': 'New passwords do not match'}), 400

    if len(new_pw) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    current_user.password_hash = generate_password_hash(new_pw)
    session.commit()

    return jsonify({'success': True}), 200

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
            accountType="user"
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

    if current_user.accountType == "business_admin":
        items = session.query(Inventory).all()
    else:
        dept_ids = [
            m.departmentID for m in current_user.memberships
            if m.status.value == "accepted"
        ]
        items = session.query(Inventory).filter(
            Inventory.departmentID.in_(dept_ids)
        ).all()

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

    if current_user.accountType == "business_admin":
        user_departments = session.query(Department).all()
    else:
        user_departments = [
            m.department for m in current_user.memberships
            if m.status.value == "accepted" and m.role.value == "admin"
        ]

    return render_template("inventory.html", items=items, user_departments=user_departments)

@app.route('/inventory/json')
@login_required
def inventory_json():

    if current_user.accountType == "business_admin":
        items = session.query(Inventory).all()
    else:
        dept_ids = [
            m.departmentID for m in current_user.memberships
            if m.status.value == "accepted"
        ]
        items = session.query(Inventory).filter(
            Inventory.departmentID.in_(dept_ids)
        ).all()

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
            "itemphoto": item.itemphoto,
            "departmentID": item.departmentID
        })

    return jsonify({"items": result})

def save_uploaded_image(file):
    filename = secure_filename(file.filename)
    if not filename:
        return None
    timestamp = datetime.now().strftime('%Y%m%d%M')
    filename = f"{timestamp}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return url_for('static', filename=f'uploads/{filename}')

#add inventory
@app.route('/inventory/add', methods=['POST'])
@login_required
def add_inventory():


    if current_user.accountType != "business_admin":
        if not any(
            m.role.value == "admin" and m.status.value == "accepted"
            for m in current_user.memberships
        ):
            abort(403)


    image_url = request.form.get('itemphoto')
    image_file = request.files.get('itemphoto_file')
    if image_file and image_file.filename:
        image_url = save_uploaded_image(image_file)

    item = Inventory(
        itemName=request.form['itemName'],
        itemDescription=request.form.get('itemDescription'),
        itemquantity=request.form.get('itemquantity'),
        itemphoto=image_url,
        departmentID=request.form.get('departmentID')
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

    if current_user.accountType != "business_admin" and not current_user.is_admin_of(item.departmentID):
        abort(403)

    # remove item from all requests first
    session.query(RequestItems).filter_by(itemID=item_id).delete()

    session.delete(item)
    session.commit()

    return redirect(url_for('inventory'))

#update inventory
@app.route('/inventory/<int:item_id>', methods=['POST'])
@login_required
def update_inventory(item_id):

    
    if current_user.accountType != "business_admin":
        if not any(
            m.role.value == "admin" and m.status.value == "accepted"
            for m in current_user.memberships
        ):
            abort(403)


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

        image_url = request.form.get('itemphoto')
        image_file = request.files.get('itemphoto_file')
        if image_file and image_file.filename:
            image_url = save_uploaded_image(image_file)
        if image_url is not None:
            item.itemphoto = image_url

        if 'departmentID' in request.form:
            item.departmentID = request.form['departmentID']

        session.commit()

    return redirect(url_for('inventory'))

#view requests
@app.route('/requests')
@login_required
def requests_page():

    if current_user.accountType == "business_admin":
        requests = session.query(Request).all()
    else:
        dept_ids = [
            m.departmentID for m in current_user.memberships
            if m.status.value == "accepted"
        ]
        requests = session.query(Request).filter(
            Request.departmentID.in_(dept_ids)
        ).all()

    # auto-mark overdue
    now = datetime.now()
    changed = False
    for req in requests:
        if (req.returnDate
                and req.returnDate < now
                and req.status == Status.loaned):
            req.status = Status.overdue
            changed = True

    if changed:
        session.commit()

    if current_user.accountType == "business_admin":
        user_departments = session.query(Department).all()
    else:
        user_departments = [
            m.department for m in current_user.memberships
            if m.status.value == "accepted"
        ]

    return render_template("requests.html", requests=requests, user_departments=user_departments)

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
        requesterID=current_user.userID,
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

    #permission check
    if current_user.accountType != "business_admin" and not current_user.is_admin_of(req.departmentID):
        abort(403)

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

    #permission check
    if current_user.accountType != "business_admin" and not current_user.is_admin_of(req.departmentID):
        abort(403)

    req.status = Status.declined
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

# resubmit request
@app.route('/requests/resubmit/<int:request_id>', methods=['POST'])
@login_required
def resubmit_request(request_id):
    req = session.query(Request).get(request_id)

    if not req:
        flash('Request not found', 'error')
        return redirect(url_for('dashboard'))

    # only requester OR admin OR dept head
    if (current_user.userID != req.requesterID and
        current_user.accountType != "business_admin" and
        not current_user.is_admin_of(req.departmentID)):
        abort(403)

    # only allow if declined
    if req.status.value.lower() != "declined":
        flash('Only declined requests can be resubmitted', 'error')
        return redirect(url_for('dashboard'))

    req.status = Status.waiting
    session.commit()

    flash('Request resubmitted', 'success')
    return redirect(url_for('dashboard'))

# delete declined request
@app.route('/requests/delete_declined/<int:request_id>', methods=['POST'])
@login_required
def delete_declined_request(request_id):
    req = session.query(Request).get(request_id)

    if not req:
        flash('Request not found', 'error')
        return redirect(url_for('dashboard'))

    # only requester OR admin OR dept head
    if (current_user.userID != req.requesterID and
        current_user.accountType != "business_admin" and
        not current_user.is_admin_of(req.departmentID)):
        abort(403)

    # only allow delete if declined
    if req.status.value.lower() != "declined":
        flash('Only declined requests can be deleted', 'error')
        return redirect(url_for('dashboard'))

    session.delete(req)
    session.commit()

    flash('Request deleted', 'success')
    return redirect(url_for('dashboard'))


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

# mark request as returned
@app.route('/requests/return/<int:request_id>', methods=['POST'])
@login_required
def return_request(request_id):
    req = session.query(Request).get(request_id)

    if not req:
        flash('Request not found', 'error')
        return redirect(url_for('dashboard'))

    # permission check
    if (current_user.accountType != "business_admin"
            and not current_user.is_admin_of(req.departmentID)
            and current_user.userID != req.requesterID):
        abort(403)

    # only allow if loaned or overdue
    if req.status.value.lower() not in ['loaned', 'overdue']:
        flash('Only loaned or overdue requests can be returned', 'error')
        return redirect(url_for('dashboard'))

    req.status = Status.returned
    session.commit()

    flash('Item returned successfully', 'success')
    return redirect(url_for('dashboard'))

# mark request as loaned
@app.route('/requests/loan/<int:request_id>', methods=['POST'])
@login_required
def loan_request(request_id):
    req = session.query(Request).get(request_id)

    if not req:
        flash('Request not found', 'error')
        return redirect(url_for('dashboard'))

    # permission check
        
    if (current_user.accountType != "business_admin"
            and not current_user.is_admin_of(req.departmentID)
            and current_user.userID != req.requesterID):
        abort(403)


    # only allow if request is approved
    if req.status.value.lower() != "approved":
        flash('Request must be approved first', 'error')
        return redirect(url_for('dashboard'))

    # update status
    req.status = Status.loaned
    session.commit()

    flash('Loan recorded successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/appsettings')
@business_admin_required
def appsettings():
    departments = session.query(Department).all()
    users = session.query(Account).all()
    return render_template("appsettings.html", departments=departments, users=users)


@app.route('/appsettings/departments/add', methods=['POST'])
@business_admin_required
def add_department():
    name = request.form['departmentName']

    new_dept = Department(departmentName=name)
    session.add(new_dept)
    session.commit()

    return redirect(url_for('appsettings'))


@app.route('/appsettings/departments/delete/<int:dept_id>')
@business_admin_required
def delete_department(dept_id):
    dept = session.query(Department).get(dept_id)

    if not dept:
        flash('Department not found', 'error')
        return redirect(url_for('appsettings'))

    # delete all requests for this department
    requests_to_delete = session.query(Request).filter_by(departmentID=dept_id).all()
    for req in requests_to_delete:
        session.delete(req)

    # delete all inventory for this department
    items_to_delete = session.query(Inventory).filter_by(departmentID=dept_id).all()
    for item in items_to_delete:
        session.delete(item)

    # delete the department itself
    session.delete(dept)
    session.commit()

    flash('Department and all associated data deleted', 'success')
    return redirect(url_for('appsettings'))


@app.route('/appsettings/users/<int:user_id>', methods=['POST'])
@business_admin_required
def update_user(user_id):
    user = session.query(Account).get(user_id)

    if user:
        # update account type (always apply immediately)
        if 'accountType' in request.form:
            user.accountType = request.form['accountType']

        session.commit()

    return redirect(url_for('appsettings'))


@app.route('/appsettings/branding', methods=['POST'])
@business_admin_required
def update_branding():
    url = request.form['logoURL'].strip()

    branding = session.query(Branding).first()

    if branding:
        branding.logoURL = url if url else None

    session.commit()

    return redirect(url_for('appsettings'))

@app.context_processor
def inject_globals():
    return dict(
        branding=session.query(Branding).first(),
        AccountType=AccountType
    )

@app.route('/appsettings/departments/update/<int:dept_id>', methods=['POST'])
@business_admin_required
def update_department(dept_id):
    dept = session.query(Department).get(dept_id)

    if dept:
        dept.departmentName = request.form['departmentName']
        session.commit()

    return redirect(url_for('appsettings'))

@app.route('/departments/<int:dept_id>')
@dept_admin_required
def department_detail(dept_id):
    dept = session.query(Department).get(dept_id)
    if not dept:
        flash('Department not found', 'error')
        return redirect(url_for('department_detail', dept_id=dept_id))
    
    members = (session.query(Membership).filter_by(departmentID=dept_id, status=MembershipStatus.accepted).all())
    pending = (session.query(Membership).filter_by(departmentID=dept_id, status=MembershipStatus.pending).all())
    declined = (session.query(Membership).filter_by(departmentID=dept_id, status=MembershipStatus.declined).all())
    
    return render_template('department_detail.html', dept=dept, members=members, pending=pending, declined=declined)

@app.route('/departments/<int:dept_id>/invite', methods=['POST'])
@dept_admin_required
def invite_user(dept_id):
    username = request.form.get('username', '').strip()
    role_str = request.form.get('role', 'member')
    
    if not username:
        flash('Username is required', 'error')
        return redirect(url_for('department_detail', dept_id=dept_id))
    
    invitee = session.query(Account).filter_by(userName=username).first()
    if not invitee:
        flash(f'No user found with username -> {username}', 'error')
        return redirect(url_for('department_detail', dept_id=dept_id))
    
    try:
        role = MembershipRole(role_str)
    except ValueError:
        flash('Invalid role', 'error')
        return redirect(url_for('department_detail', dept_id=dept_id))
    
    existing = session.query(Membership).filter_by(userID=invitee.userID, departmentID=dept_id).first()
    
    if existing:
        if existing.status == MembershipStatus.accepted:
            flash(f'{username} is already a member of this department', 'error')
            return redirect(url_for('department_detail', dept_id=dept_id))
        if existing.status == MembershipStatus.pending:
            flash(f'{username} has not accepted pending invite', 'error')
            return redirect(url_for('department_detail', dept_id=dept_id))
        # status == declined → re-invite
        existing.status = MembershipStatus.pending
        existing.role = role
    else:
        session.add(Membership(userID=invitee.userID, departmentID=dept_id, role=role, status=MembershipStatus.pending,))
    
    session.commit()
    flash(f'Invitation sent to {username}', 'success')
    return redirect(url_for('department_detail', dept_id=dept_id))

@app.route('/invitations/<int:membership_id>/accept', methods=['POST'])
@login_required
def accept_invitation(membership_id):
    m = session.query(Membership).get(membership_id)
    if not m or m.userID != current_user.userID or m.status != MembershipStatus.pending:
        abort(403)
    m.status = MembershipStatus.accepted
    session.commit()
    flash(f'Joined {m.department.departmentName}', 'success')
    return redirect(request.referrer or url_for('dashboard'))


@app.route('/invitations/<int:membership_id>/decline', methods=['POST'])
@login_required
def decline_invitation(membership_id):
    m = session.query(Membership).get(membership_id)
    if not m or m.userID != current_user.userID or m.status != MembershipStatus.pending:
        abort(403)
    m.status = MembershipStatus.declined
    session.commit()
    flash('Invitation declined', 'success')
    return redirect(url_for('dashboard'))

@app.route('/appsettings/users/delete/<int:user_id>')
@business_admin_required
def delete_user(user_id):
    user = session.query(Account).get(user_id)

    if not user:
        flash('User not found', 'error')
        return redirect(url_for('appsettings'))

    if user.userID == current_user.userID:
        flash('You cannot delete your own account', 'error')
        return redirect(url_for('appsettings'))

    session.delete(user)
    session.commit()

    flash('Account deleted', 'success')
    return redirect(url_for('appsettings'))

@app.route('/departments/<int:dept_id>/remove/<int:membership_id>')
@dept_admin_required
def remove_member(dept_id, membership_id):
    m = session.query(Membership).get(membership_id)

    if not m or m.departmentID != dept_id:
        flash('Member not found', 'error')
        return redirect(url_for('department_detail', dept_id=dept_id))

    session.delete(m)
    session.commit()

    flash('Member removed', 'success')
    return redirect(url_for('department_detail', dept_id=dept_id))

@app.route('/departments/<int:dept_id>/member/<int:membership_id>/role', methods=['POST'])
@dept_admin_required
def update_member_role(dept_id, membership_id):
    m = session.query(Membership).get(membership_id)

    if not m or m.departmentID != dept_id:
        flash('Member not found', 'error')
        return redirect(url_for('department_detail', dept_id=dept_id))

    role_str = request.form.get('role', 'member')

    try:
        m.role = MembershipRole(role_str)
        session.commit()
        flash('Role updated', 'success')
    except ValueError:
        flash('Invalid role', 'error')

    return redirect(url_for('department_detail', dept_id=dept_id))

@app.route('/account/update', methods=['POST'])
@login_required
def update_account():
    current_user.fName = request.form.get('fName', current_user.fName)
    current_user.lName = request.form.get('lName', current_user.lName)

    new_username = request.form.get('userName', '').strip()
    if new_username and new_username != current_user.userName:
        existing = session.query(Account).filter_by(userName=new_username).first()
        if existing:
            flash('Username already taken', 'error')
            return redirect(request.referrer or url_for('dashboard'))
        current_user.userName = new_username

    session.commit()
    flash('Account updated', 'success')
    return redirect(request.referrer or url_for('dashboard'))

if __name__ == "__main__":
    app.run(debug=True)