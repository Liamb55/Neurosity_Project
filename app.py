from datetime import datetime
import os

from flask import Flask, flash, render_template, redirect, request, send_file, session, url_for
from sqlalchemy import func, text
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import User, DatasetInfo, Subscription, Comment, db
from distutils.log import debug
from fileinput import filename
import pandas as pd
import matplotlib.pyplot as plt
 


app = Flask(__name__)
app.config.from_object('config')  # Load configuration from config.py

login_manager = LoginManager(app)
login_manager.login_view = "login_page"
login_manager.login_message = "Please login here to access EEG datasets."
    
with app.app_context():
    db.init_app(app)
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
@login_required
def index():
    return render_template("index.html", djuser=current_user)

@app.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register_action():
    username = request.form["username"]
    password = request.form["password"]
    if User.query.filter_by(username=username).first():
        flash(f"The username '{username}' is already taken")
        return redirect(url_for("register_page"))

    user = User(username=username, password=password)
    
    db.session.add(user)
    db.session.commit()

    login_user(user)
    flash(f"Welcome {username}!")
    return redirect(url_for("index"))

@app.route("/neurosity")
def neurosity():
    return render_template("neurosity.html")

@app.route("/kinesis")
def kinesis():
    return render_template("kinesis.html")


@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_action():
    username = request.form["username"]
    password = request.form["password"]
    user = User.query.filter_by(username=username).first()
    if not user:
        flash(f"No such user '{username}'")
        return redirect(url_for("login_page"))
    if password != user.password:
        flash(f"Invalid password for the user '{username}'")
        return redirect(url_for("login_page"))

    login_user(user)
    flash(f"Welcome back, {username}!")
    return redirect(url_for("index"))


@app.route("/logout", methods=["GET"])
@login_required
def logout_page():
    return render_template("logout.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout_action():
    logout_user()
    flash("You have been logged out")
    return redirect(url_for("index"))

@app.route("/search", methods=["GET"])
@login_required
def searchDatasets():
    datasets = db.session.execute(text('SELECT ds_id, Name, owner_id, owner_username, path, description, (SELECT count(ds_id) FROM subscriptions WHERE user_id = ' + str(current_user.user_id) + ' AND ds_id = datasets.ds_id) AS issubscribed FROM datasets WHERE owner_id <> ' + str(current_user.user_id)))
    return render_template("searchDatasets.html", djdatasets=datasets)

@app.route("/subscribe/<ds_id>", methods=["GET"])
@login_required
def subscribe(ds_id):
    subscription = Subscription(current_user.user_id, ds_id)
    db.session.add(subscription)
    db.session.commit()
    return redirect(url_for("searchDatasets"))

@app.route("/unsubscribe/<ds_id>", methods=["GET"])
@login_required
def unsubscribe(ds_id):
    db.session.query(Subscription).filter(Subscription.user_id==current_user.user_id, Subscription.ds_id==ds_id).delete()
    db.session.commit()
    return redirect(url_for("searchDatasets"))

@app.route("/add_comment/<ds_id>", methods=["POST"])
@login_required
def add_comment(ds_id):
    comment_text = request.form["comment"]
    comment = Comment(current_user.user_id, ds_id, current_user.username, comment_text)
    
    db.session.add(comment)
    db.session.commit()

    return redirect(url_for("showData", ds_id=ds_id))

@app.route('/upload', methods=['GET', 'POST'])
def uploadFile():
    if request.method == 'POST':
        description = request.form["description"]
        data_filename = ""
        f = request.files.get('file')
 
        data_filename = secure_filename(f.filename)
        
        if data_filename:
            new_filename = str(current_user.user_id) + '_' + data_filename

            f.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
    
            session['uploaded_data_file_path'] = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)

            ds_name = data_filename.replace('.csv', '')
            ds_owner_id = current_user.user_id
            ds_owner_username = current_user.username
            ds_path = session['uploaded_data_file_path']
            ds_desc = description
            datasetInfo = DatasetInfo(ds_name, ds_owner_id, ds_owner_username, ds_path, ds_desc)

            db.session.add(datasetInfo)
            db.session.commit()

            flash("Upload Successful")
        else:
            flash("No file selected")

    return redirect(url_for("index"))
 
@app.route('/download_file/<ds_id>')
def download_file(ds_id):
    ds_info = DatasetInfo.query.get(int(ds_id))

    return send_file(
        ds_info.path,
        mimetype='text/csv',
        download_name = ds_info.name + ".csv",
        as_attachment=True
    )
@app.route('/delete_file/<ds_id>') 
def delete_file(ds_id):
    ds_info = DatasetInfo.query.get(int(ds_id))
    
    os.remove(ds_info.path)                                                     # Delete csv file
    db.session.query(Subscription).filter(Subscription.ds_id==ds_id).delete()   # Delete subscriptions
    db.session.query(Comment).filter(Comment.ds_id==ds_id).delete()             # Delete comments
    db.session.delete(ds_info)                                                  # Delete dataset info

    db.session.commit()
    flash('Dataset deleted successfully.')
    return redirect(url_for("index"))

@app.route('/show_data/<ds_id>')
def showData(ds_id):
    ds_info = DatasetInfo.query.get(int(ds_id))

    uploaded_df = pd.read_csv(ds_info.path, encoding='unicode_escape')

    data = {"labels":[], "CP3":[], "C3":[], "F5":[], "PO3":[], "PO4":[], "F6":[], "C4":[], "CP4":[]}

    IsFirstRub = True

    for index, row in uploaded_df.iterrows():
        if IsFirstRub:
            time_offset = float(format(row[10], '.8f'))
            IsFirstRub = False
    
        data["labels"].append(format(float(format(row[10], '.8f'))-time_offset, '.2f'))
        data["CP3"].append(format(row[1], '.3f'))
        data["C3"].append(format(row[2], '.3f'))
        data["F5"].append(format(row[3], '.3f'))
        data["PO3"].append(format(row[4], '.3f'))
        data["PO4"].append(format(row[5], '.3f'))
        data["F6"].append(format(row[6], '.3f'))
        data["C4"].append(format(row[7], '.3f'))
        data["CP4"].append(format(row[8], '.3f'))

    return render_template('show_csv_data.html', ds_info=ds_info, user=current_user, data=data)


@app.route("/update_desc/<ds_id>", methods=["POST"])
@login_required
def update_desc(ds_id):
    desc_text = request.form["description"]
    ds_info = DatasetInfo.query.get(int(ds_id))

    ds_info.description = desc_text
    db.session.commit()

    return redirect(url_for("showData", ds_id=ds_id))



if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8000)

