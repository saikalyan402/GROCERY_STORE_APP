#importing libraries
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy

#initializing flask app
app = Flask(__name__)
#configuring the applications db using sqlalchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grocery_store.db'
app.secret_key = 'saka'
db = SQLAlchemy(app)


# Database Models

# creating User table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))

# creating Category table
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

# creating Product table
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    manufacture_date = db.Column(db.String(100))
    expiry_date = db.Column(db.String(100))
    rate = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    # extablishing relationship between Category and Product
    category = db.relationship('Category', backref=db.backref('products', lazy=True))

# creating  CartItem table
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)
    # extablishing relationship between User and CartItem
    user = db.relationship('User', backref=db.backref('cart_items', lazy=True))
    # extablishing relationship between Product and CartItem
    product = db.relationship('Product', backref=db.backref('cart_items', lazy=True))


# Routes

#main route
@app.route('/')
def home():
    print('main route called')
    # Displaying latest added products
    latest_products = Product.query.order_by(Product.id.desc()).limit(5).all()
    print('latest products printed succesfully')
    return render_template('index.html', latest_products=latest_products)


#before and after login search implementation 
@app.route('/search', methods=['POST', 'GET'])
def search():
    print('search route called')
    if 'user_id' not in session:
        return redirect('/')
 
    search_category = request.form.get('search_category')
    search_price = request.form.get('search_price')
    search_manufacture_date = request.form.get('search_manufacture_date')
    print('search_category')
    categories = Category.query.all()
    selected_category = None
    products = []
    
    if search_category:
        selected_category = Category.query.filter(Category.name.ilike(f'%{search_category}%')).first()
        print('search_category')
    elif search_price:
        products = Product.query.filter(Product.rate <= float(search_price)).all()
        print('products')

    elif search_manufacture_date:
        products = Product.query.filter(Product.manufacture_date >= search_manufacture_date).all()
        print('products')

    return render_template('home.html', categories=categories, selected_category=selected_category, products=products)


# user login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()

        if user:
            #print("username: " + user.username)
            session['user_name'] = user.username
            session['user_id'] = user.id
            session['user'] = {'id': user.id, 'username': user.username, 'password': user.password}
            print(session["user"])

            return redirect('/search')
        else:
            return render_template('login.html', error=True)

    return render_template('login.html', error=False)

#user logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

#category route
@app.route('/category/<int:category_id>', methods=['GET', 'POST'])
def category_products(category_id):
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity'))

        # Get the product from the database
        product = Product.query.get(product_id)

        # Check if the product exists and the quantity is valid
        if product and quantity > 0:
            # Initialize the cart in the session if it doesn't exist
            if 'cart' not in session:
                session['cart'] = []

            # Checking if the product is already in the cart
            for item in session['cart']:
                if item['product'].id == product.id:
                    item['quantity'] += quantity
                    break
            else:
                # Adding the product to the cart
                session['cart'].append({
                    'product': product,
                    'quantity': quantity
                })

    category = Category.query.get(category_id)
    if not category:
        return redirect('/')

    products = category.products
    return render_template('category_products.html', category=category, products=products)

#cart route
@app.route('/cart', methods=['GET'])
def cart():
    if 'user_id' not in session:
        return redirect('/login')

    if 'cart' not in session or not session['cart']:
        return render_template('cart.html', cart_items=[], total_price=0)

    cart_items = session['cart']
    print(cart_items)
    total_price = sum(item['rate'] * item['quantity'] for item in cart_items)
    print(total_price)
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)
    print('showing in cart successful')

#add to cart route
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        return redirect('/login')

    quantity = int(request.form.get('quantity'))

    product = Product.query.get(product_id)
    if not product or quantity <= 0:
        return redirect('/')

    cart_item = {
        'product_id': product.id,
        'name': product.name,
        'rate': product.rate,
        'quantity': quantity
    }
    print(cart_item)
    # Initialize the cart in the session if it doesn't exist
    if 'cart' not in session:
        session['cart'] = []

    # Check if the product is already in the cart
    for item in session['cart']:
        if item['product_id'] == product.id:
            item['quantity'] += quantity
            break
    else:
        # Appending the product to the cart
        session['cart'].append({
            'product_id': product.id,
            'quantity': quantity,
            'name': product.name,
            'rate': product.rate
        })
        print(session['cart'])
    # Updating the cart 
    session.modified = True   
    print('successfully updated')
    return redirect('/category/' + str(product.category_id))

#user purchse route
@app.route('/purchase_summary', methods=['GET'])
def purchase_summary():
    if 'user_id' not in session:
        return redirect('/login') 

    if 'cart' not in session or not session['cart']:
        return redirect('/cart')
    

    cart_items = session['cart']
    total_price = sum(item['rate'] * item['quantity'] for item in cart_items) 
    username = session['user_name']  
    print(session['cart'])
    session['cart'] = []
    print(session['cart'])
    return render_template('purchase_summary.html', username=username, total_price=total_price)

##########################################################################################
# Admin routes

#admin login route
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = User.query.filter_by(username=username, password=password, role='admin').first()
        print(admin)
        if admin:
            session['admin_id'] = admin.id
            print(session['admin_id'])
            return redirect('/admin/categories')
        else:
            return render_template('admin_login.html', error=True)

    return render_template('admin_login.html', error=False)

#admin logout route
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    return redirect('/admin/login')

#admin categories route
@app.route('/admin/categories')
def admin_categories():
    if 'admin_id' not in session:
        return redirect('/admin/login')

    categories = Category.query.all()
    print(categories)
    return render_template('admin_categories.html', categories=categories)

#admin crud operation route adding
@app.route('/admin/categories/add', methods=['GET', 'POST'])
def admin_add_category():
    if 'admin_id' not in session:
        return redirect('/admin/login')

    if request.method == 'POST':
        name = request.form['name']
        category = Category(name=name)
        print(category)
        db.session.add(category)
        db.session.commit()
        return redirect('/admin/categories')

    return render_template('admin_add_category.html')

#admin crud operation route editing
@app.route('/admin/categories/edit/<int:category_id>', methods=['GET', 'POST'])
def admin_edit_category(category_id):
    if 'admin_id' not in session:
        return redirect('/admin/login')

    category = Category.query.get(category_id)
    if not category:
        return redirect('/admin/categories')

    if request.method == 'POST':
        new_name = request.form['name']
        category.name = new_name
        print(category.name)
        db.session.commit()
        return redirect('/admin/categories')

    return render_template('admin_edit_category.html', category=category)

#admin crud operation route deleting
@app.route('/admin/categories/remove/<int:category_id>', methods=['GET', 'POST'])
def admin_remove_category(category_id):
    if 'admin_id' not in session:
        return redirect('/admin/login')

    category = Category.query.get(category_id)
    print(category)
    if not category:
        return redirect('/admin/categories')

    if request.method == 'POST':
        db.session.delete(category)
        db.session.commit()
        return redirect('/admin/categories')

    return render_template('admin_remove_category.html', category=category)

#admin products route
@app.route('/admin/products')
def admin_products():
    if 'admin_id' not in session:
        return redirect('/admin/login')

    products = Product.query.all()
    categories = Category.query.all()
    print(products)
    print(categories)

    return render_template('admin_products.html', products=products, categories=categories)

#admin crud operation on products route adding
@app.route('/admin/products/add', methods=['POST'])
def admin_add_product():
    if 'admin_id' not in session:
        return redirect('/admin/login')

    name = request.form['name']
    rate = float(request.form['rate'])
    quantity = int(request.form['quantity'])
    category_id = int(request.form['category'])
    category = Category.query.get(category_id)
    print(category)
    print(category_id)
    print(rate)
    print(quantity)
    print(name)
    
    if not category:
        return redirect('/admin/products')

    product = Product(name=name, rate=rate, quantity=quantity, category=category)
    print(product)
    db.session.add(product)
    db.session.commit()
    db.session.flush()
    return redirect('/admin/products')

#admin crud operation on products route editing
@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    if 'admin_id' not in session:
        return redirect('/admin/login')

    product = Product.query.get(product_id)
    if not product:
        return redirect('/admin/products')

    if request.method == 'POST':
        product.name = request.form['name']
        product.rate = float(request.form['rate'])
        product.quantity = int(request.form['quantity'])
        category_id = int(request.form['category'])
        category = Category.query.get(category_id)
        if category:
            product.category = category

        db.session.commit()
        return redirect('/admin/products')

    categories = Category.query.all()
    return render_template('admin_edit_product.html', product=product, categories=categories)

#admin crud operation on products route deleting
@app.route('/admin/products/remove/<int:product_id>')
def admin_remove_product(product_id):
    if 'admin_id' not in session:
        return redirect('/admin/login')

    product = Product.query.get(product_id)
    if not product:
        return redirect('/admin/products')

    db.session.delete(product)
    db.session.commit()

    return redirect('/admin/products')


#running the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False)
