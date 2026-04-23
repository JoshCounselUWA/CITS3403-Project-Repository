from flask import Flask, render_template, request, redirect, url_for
from models import session, Inventory, Request, Account
from flask_cors import CORS

app = Flask(__name__, template_folder="../Pages", static_folder="../Static")
CORS(app)

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

#update inventory
@app.route('/inventory/<int:item_id>', methods=['POST'])
def update_inventory(item_id):
    item = session.query(Inventory).get(item_id)

    if item:
        if 'itemName' in request.form:
            item.itemName = request.form['itemName']
        if 'itemDescription' in request.form:
            item.itemDescription = request.form['itemDescription']
        if 'itemquantity' in request.form:
            item.itemquantity = request.form['itemquantity']
        if 'itemphoto' in request.form:
            item.itemphoto = request.form['itemphoto']

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
        requesterID=request.form['requesterID'],
        eventDateStart=request.form.get('eventDateStart'),
        eventDateEnd=request.form.get('eventDateEnd'),
        returnDate=request.form.get('returnDate')
    )

    session.add(new_request)
    session.commit()

    return redirect(url_for('requests_page'))

#delete request
@app.route('/requests/delete/<int:request_id>')
def delete_request(request_id):
    req = session.query(Request).get(request_id)

    if req:
        session.delete(req)
        session.commit()

    return redirect(url_for('requests_page'))

#update request
@app.route('/requests/<int:request_id>', methods=['POST'])
def update_request(request_id):
    req = session.query(Request).get(request_id)

    if req:
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

        session.commit()

    return redirect(url_for('requests_page'))

if __name__ == "__main__":
    app.run(debug=True)