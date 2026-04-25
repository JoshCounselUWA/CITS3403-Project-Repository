from flask import Flask, render_template, request, redirect, url_for, jsonify
from models import session, Inventory, Request, RequestItems, Account
from flask_cors import CORS
from flask import flash
import json

app = Flask(__name__, template_folder="../Pages", static_folder="../Static")
CORS(app)
app.secret_key = 'your-secret-key-here'

#view dashboard
@app.route('/dashboard')
def dashboard():
    items = session.query(Inventory).all()
    requests = session.query(Request).all()
    return render_template("dashboard.html", items=items, requests=requests)


#view inventory
@app.route('/inventory')
def inventory():
    items = session.query(Inventory).all()
    return render_template("inventory.html", items=items)

#inventory as json (for item picker)
@app.route('/inventory/json')
def inventory_json():
    items = session.query(Inventory).all()
    return jsonify({'items': [i.to_json() for i in items]})

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
        requesterID=request.form.get('requesterID')
    )

    session.add(new_request)
    session.commit()

    #save requested items
    items_json = request.form.get('itemsJSON')
    if items_json:
        try:
            items = json.loads(items_json)
            for entry in items:
                ri = RequestItems(
                    requestID=new_request.requestID,
                    itemID=entry['itemID'],
                    quantity=entry['quantity']
                )
                session.add(ri)
            session.commit()
        except Exception as e:
            print(f"Error saving request items: {e}")

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

        #update requested items - clear old ones and replace
        items_json = request.form.get('itemsJSON')
        if items_json is not None:
            try:
                session.query(RequestItems).filter_by(requestID=request_id).delete()
                items = json.loads(items_json)
                for entry in items:
                    ri = RequestItems(
                        requestID=request_id,
                        itemID=entry['itemID'],
                        quantity=entry['quantity']
                    )
                    session.add(ri)
            except Exception as e:
                print(f"Error updating request items: {e}")

        session.commit()

    return redirect(url_for('requests_page'))

#get items for a request (used by details modal)
@app.route('/requests/items/<int:request_id>', methods=['GET'])
def get_request_items(request_id):
    items = session.query(RequestItems).filter_by(requestID=request_id).all()
    result = []
    for ri in items:
        inv = session.query(Inventory).get(ri.itemID)
        result.append({
            'itemID': ri.itemID,
            'itemName': inv.itemName if inv else 'Unknown',
            'itemquantity': inv.itemquantity if inv else 0,
            'quantity': ri.quantity
        })
    return jsonify({'items': result})

if __name__ == "__main__":
    app.run(debug=True)