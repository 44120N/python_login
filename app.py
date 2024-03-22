import os, dotenv, hashlib
from flask import *
from flask_bcrypt import *
from flask_login import *
from flask_marshmallow import Marshmallow
from model import db, User

dotenv.load_dotenv()
app = Flask(__name__)
login_manager = LoginManager(app)

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

db.init_app(app)
with app.app_context():
    db.create_all()

ma = Marshmallow(app)
class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'username', 'password', 'level')
userSchema = UserSchema(many=True)

class LoginUser(UserMixin):
    def __init__(self, username):
        self.username = username
    def get_id(self):
        return self.username
    def is_authenticated(self):
        return False
    def is_admin(self):
        return False
    def is_operator(self):
        return False
    def is_player(self):
        return False

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(generate_password_hash(user.password), password) and user.level == "admin":
            admin = LoginUser(username)
            admin.is_authenticated=True
            admin.is_admin = True
            login_user(admin)
            return redirect(url_for("admin_panel"))
        elif user and check_password_hash(generate_password_hash(user.password), password) and user.level == "operator":
            operator = LoginUser(username)
            operator.is_authenticated=True
            operator.is_operator = True
            login_user(operator)
            return redirect(url_for("operator_panel"))
        elif user and check_password_hash(generate_password_hash(user.password), password) and user.level == "player":
            player = LoginUser(username)
            player.is_authenticated=True
            player.is_player = True
            login_user(player)
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password", "error")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@login_manager.user_loader
def load_user(user_id):
    return LoginUser(user_id)

@app.route("/")
def index():
    if not current_user.is_authenticated or not current_user.is_player:
        return redirect(url_for("login"))
    return render_template("index.html", user = User.query.filter(User.username==current_user.username).first())

@app.route("/admin")
@login_required
def admin_panel():
    if not current_user.is_authenticated or not current_user.is_admin:
        return redirect(url_for("login"))
    return render_template("admin.html", 
                        users = User.query.all(), 
                        user = User.query.filter(User.username==current_user.username).first())

@app.route("/operator")
@login_required
def operator_panel():
    if not current_user.is_authenticated or not current_user.is_operator:
        return redirect(url_for("login"))
    return render_template("operator.html", 
                        users = User.query.all(), 
                        user = User.query.filter(User.username==current_user.username).first())

@app.route("/api/get_users", methods=["GET"])
def get_users():
    users = User.query.all()
    result = userSchema.dump(users)
    return jsonify(result)

@app.route("/api/add_user")
def post_user_form():
    return render_template("add_user.html")

@app.route("/api/post_user", methods=["POST"])
def post_user():
    name = request.form.get("name")
    username = request.form.get("username")
    password = request.form.get("password")
    level = request.form.get("level")
    id = hashlib.sha256((name+username+password+level).encode()).hexdigest()
    
    try:
        new_user = User(id=id, name=name, username=username, password=password, level=level)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("admin_panel"))
    except Exception as e:
        db.session.rollback()
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/edit_user_form/<username>")
def edit_user_form(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return render_template("edit_user.html", user=user)
    else:
        return "User not found", 404

@app.route("/api/edit_user/<username>", methods=["POST"])
def edit_user(username):
    user = User.query.filter_by(username=username).first()
    if user:
        new_name = request.form.get("name")
        new_password = request.form.get("password")
        new_level = request.form.get("level")
        
        user.name = new_name
        user.password = new_password
        user.level = new_level
        
        try:
            db.session.commit()
            return redirect(url_for("admin_panel"))
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"message": f"User {username} not found."}), 404

@app.route("/api/delete_user_form/<username>")
def delete_user_form(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return render_template("delete_user.html", user=user)
    else:
        return "User not found", 404

@app.route("/api/delete_user/<username>", methods=["POST"])
def delete_user(username):
    user = User.query.filter_by(username=username).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for("admin_panel"))
    else:
        return jsonify({"message": f"User {username} not found."}), 404

@app.after_request
def after_request(response):
    if response.status_code >= 400:
        app.logger.error(f"Error in request: {response.status_code} - {response.data}")
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.getenv("PORT"), debug=False, load_dotenv=True)