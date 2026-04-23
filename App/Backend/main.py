from flask import Flask, render_template, request, redirect, url_for, flash
from forms import LoginForm
from werkzeug.security import check_password_hash, generate_password_hash
from models import session, Inventory, Request, Account
from flask_cors import CORS

app = Flask(__name__, template_folder="../Pages", static_folder="../Static")
app.config['SECRET_KEY'] = 'need_to_change_this_later_secret_key'
CORS(app)

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
        itemphoto=request.form['itemphoto']
    )

    session.add(item)
    session.commit()

    return redirect(url_for('inventory'))

#delete inventory
@app.route('/inventory/delete/<int:item_id>')
def delete_inventory(item_id):
    item = session.query(Inventory).get(item_id)

    if item:
        session.delete(item)
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
        requesterID=request.form['requesterID']
    )

    session.add(new_request)
    session.commit()

    return redirect(url_for('requests_page'))

if __name__ == "__main__":
    app.run(debug=True)