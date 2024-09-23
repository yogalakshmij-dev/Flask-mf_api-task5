from flask import Flask, request, render_template, redirect, url_for, session, flash
import requests
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = "yoga@sql"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Yoga_1010@SQL'
app.config['MYSQL_DB'] = 'Api_Mutual_fund'

mysql = MySQL(app)

def isloggedin():
    return "username" in session

url = "https://api.mfapi.in/mf/"
@app.route("/")
def home():
    userlist = []
    if isloggedin():
        username = session["username"]
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM user_info WHERE Name=%s", (username,))
        data = cur.fetchall()
        cur.close()

        for i in data:
            Id = i[0]
            Name = i[1]
            Funds = i[2]
            Invested_amount = float(i[3])  
            Units_held = float(i[4])       

            # API request to get mutual fund details
            completeurl = requests.get(url + str(Funds))
            if completeurl.status_code == 200:
                response_json = completeurl.json()

                # Create a dictionary for the user data
                dict = {
                    "Sno": Id,
                    "Name": Name,
                    "Fundname": response_json["meta"]["fund_house"],
                    "Invested": Invested_amount,
                    "unitsheld": Units_held,
                    "Nav": float(response_json["data"][0]["nav"]),
                    "Currentvalue": float(response_json["data"][0]["nav"]) * Units_held,
                    "Growth": (float(response_json["data"][0]["nav"]) * Units_held) - Invested_amount 
                }

                userlist.append(dict)
    return render_template("index.html", user_list=userlist)




@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        user_name = request.form["name"]
        funds_code = request.form["funds"]
        invested_amount = request.form["invest"]
        units_held = request.form["units"]

        # Validate that required fields are not empty
        if not user_name or not funds_code or not invested_amount or not units_held:
            flash("All fields are required!", "danger")
            return redirect(url_for("add"))

        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO user_info (Name, Funds, Invested_amount, Units_held) VALUES (%s, %s, %s, %s)",
                        (user_name, funds_code, invested_amount, units_held))
            mysql.connection.commit()
            cur.close()
            flash("User created successfully", "success")
        except Exception as e:
            mysql.connection.rollback()  # Rollback in case of error
            flash(f"Error creating user: {str(e)}", "danger")

        return redirect(url_for("home"))
    
    return render_template("add.html")



@app.route("/edit/<int:Id>", methods=["GET", "POST"])
def edit(Id):
    if request.method == "POST":
        user_name = request.form["name"]
        funds_code = request.form["funds"]
        invested_amount = request.form["invest"] 
        units_held = request.form["units"]

        cur = mysql.connection.cursor()
        cur.execute("UPDATE user_info SET Name=%s, Funds=%s, Invested_amount=%s, Units_held=%s WHERE Id=%s",
            (user_name, funds_code, invested_amount, units_held, Id))
        mysql.connection.commit()
        flash("User updated", "success")
        return redirect(url_for("home"))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM user_info WHERE Id=%s", (Id,))
    data = cur.fetchone()
    return render_template("edit.html", datas=data)

@app.route("/delete/<int:Id>", methods=["GET", "POST"])
def delete(Id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user_info WHERE Id=%s", (Id,))
    mysql.connection.commit()
    cur.close()
    flash("User deleted", "warning")
    return redirect(url_for("home"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']  # Ensure this retrieves the password

        # Make sure both fields are not empty
        if not username or not password:
            flash("Username and password are required!", "danger")
            return redirect(url_for('signup'))

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO signup (username, password) VALUES (%s, %s)", (username, password))
        mysql.connection.commit()
        cur.close()  
        flash("Signup successful", 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM signup WHERE username=%s AND password=%s", (username, password))
        data = cur.fetchone()
        cur.close()
        if data:
            session['username'] = username
            flash("Login successful", 'success')
            return redirect(url_for("add"))
        else:
            flash("Invalid credentials", 'danger')
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('username', None)  # Removes 'username' from session
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))  # Redirect to login page after logout


if __name__ == "__main__":
    app.run(debug=True)
