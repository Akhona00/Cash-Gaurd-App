from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import jwt
import datetime
from functools import wraps
import os


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cashgaurd.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
db = SQLAlchemy(app)
bycrypt = Bcrypt(app)

class Owner(db.Model):
    __tablename__ = 'owners'
    Owner_id = db.Column(db.integer, primary_key=True, autoincrement=True)
    Owner_name = db.Column(db.String(80), nullable=False)
    Owner_email = db.Column(db.String(50), nullable=False, unique=True)
    Owner_password = db.Column(db.LargeBinary, nullable=False)
    Created_at = db.Colum(db.DateTime, default=datetime.utcnow )

class Busines(db.Model):
    __tablename__ = 'businesses'
    Business_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Business_name = db.Column(db.String(80), nullable=False)
    City = db.Column(db.String(50), nullable=False)
    Area_code = db.Column(db.Integer, nullable=False)
    Owner_id = db.Column(db.Integer, db.ForeignKey('owners.owner_id'), nullable=False)
    Created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Staff(db.Model):
    __tablename__ = 'staff'
    Staff_if =db.Column(db.Integer, primary_key=True)
    Staff_name = db.Column(db.String(50), nullable=False)
    Staff_email = db.Column(db.String(50), nullable=False)
    Staff_password = db.Column(db.LargeBinary, nullale=False)
    Business_id = db.Column(db.Integer, db.ForeignKey('Businesses.business_id'), nullable=False)
    Created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Inventory(db.Model):
    __tablename__ = 'Inventory'
    Inventory_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Business_id = db.Column(db.Integer, db.ForeignKey('Businesses.business_id'))
    Item_name = db.Column(db.String(80), nullable=False)
    Quantity = db.Column(db.Integer, nullable=False)
    Price = db.Column(db.Numeric(10,2), nullable=False)
    Created_at = db.Column(db.DateTime, default=datetime.utcnow)
    Updated_at = db.Column(db.DateTime, default=datetime.utcnow, onpudate=datetime.utcnow)
    Barcode = db.Column(db.String, nullable=False)


class Sale(db.Model):
    __tablename__='sales'
    Sale_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Business_id = db.Column(db.Integer, db.ForeignKey('Businesses.business_id'))
    Staff_id = db.Column(db.Integer, db.ForeignKeyz('staff.staff_id'))
    Total_amount = db.Column(db.Numeric(10,2), nullable=False)
    Payment_method = db.Column(db.String(50), nullable=False)
    Sale_date = db.Column(db.DateTime, default=datetime.utcnow)


class SaleItem(db.Model):
    __tablename__ = 'saleitems'
    SaleItem_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Sale_id = db.Column(db.Integer, db.ForeignKey('sales.sales_id'), nullable=False)
    Inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.inventory_id'))
    Quantity = db.Column(db.Integer, nullable=False)
    Price = db.Column(db.Numeric(10,2), nullable=False)


class BusinessReport(db.Model):
    __tablename__ = 'businessreports'
    Report_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Business_id = db.Column(db.Integer, db.ForeignKey('businesses.business_id'))
    Report_date = db.Column(db.DateTime, default=datetime.utcnow)
    Total_sales = db.Column(db.Numeric(10,2), nullable=False)
    Total_profit = db.Column(db.Numeric(10,2), nullable=False)


#JWT Authentication Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({'message': "Token is missing!"}), 403
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = Owner.query.filter_by(owner_id=data['user_id']).first()
        except:
            return jsonify({'message': 'Toke is invalid!'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/register', methods =['POST'])
def register():
    data = request.get_json()
    hashed_password = bycrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = Owner(owner_name=data['name'], owner_email=data['email'], owner_passwprd=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Registered successfully'})


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = Owner.query.filter_by(owner_email=data['email']).first() 
    if user and bycrypt   .check_password_hash(user.owner_password, data['password']):
        token = jwt.encode({'iser_id': user.owner_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, app.config['SECRET_KEY'], algorithm="HS256")    
        return jsonify({'token' : token})   
    return jsonify({'message': 'Invalid credentials'}), 403

@app.route('/add_inventory', methods=['POST'])  
@token_required
def add_inventory(current_user):
    data = request.get_json()
    new_item = Inventory(business_id=data['business_id'], item_name=data['item_name'], quantity=data['quantity'], price=data['price'], barcode=data.get('barcode'))
    db.session.add(new_item)
    db.session.commit()
    return jsonify({'message': 'Item added to inventory'})

@app.route('/process_payment', methods=['POST'])
@token_required
def process_payment(current_user):
    data = request.get_jason()
    new_sale =Sale(business_id=data['business_id'], staff_is=current_user.owner_id, total_amount=data['total_amount'], payment_method=data['payment_method'])
    db.session.add(new_sale)
    db.session.commit()

    for item in data('items'):
        sale_item = SaleItem(sale_id=new_sale.sale_id, inventory_id=item['inventory_id'], quantity=item['quantity'], price=item['price'])
        db.session.add(sale_item)

        inventory_item = Inventory.query.filter_by(inventory_id=item['inventory_id']).first()
        inventory_item.quantity -= item['quantity']
    db.session.commit()
    return jsonify({'message': 'Payment processed successfully'})

@app.route('/report', methods=['GET'])
@token_required
def report(current_user):
    business_id = request.argd.get('business_id')
    reports = BusinessReport.query.filter_by(business_id=business_id).all()
    report_data = []
    for report in reports:
        report_data.append({
            'report_id': report.report_id,
            'report_date': report.report_date,
            'total_sale': report.total_sales,
            'total_profit': report.total_profit
        })
    return jsonify(report_data)


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)

