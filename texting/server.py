import datetime
import re
import jwt
import bcrypt
import pymysql
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'top_secret'

# def dbConnect():
#     mydb = pymysql.connect(
#         host = "localhost",
#         user = "root",
#         password = "M@ni1234",
#         database = "whatsapp"
#     )
#     cur = mydb.cursor()
#     if mydb.open:
#         print("Connected")
#         cur = mydb.cursor()
#         cur.execute("use whatsapp")
#     else:
#         print("Falied to connect")
#     return mydb, cur

mydb = pymysql.connect(
    host = "localhost",
    user = "root",
    password = "M@ni1234",
    database = "whatsapp"
)

cur = mydb.cursor()
if mydb.open:
    print("Connected")
    cur = mydb.cursor()
else:
    print("Falied to connect")

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def update_online(username):
    query = f'UPDATE lastSeen SET lastSeenTime = "online" WHERE contact_name = "{username}"'
    print(query)
    cur.execute(query)
    mydb.commit()

def getTableName(u1, u2):
    u1c, u2c = u1, u2
    if u1 > u2:
        u1c, u2c = u2, u1
    tableName = "`" + u1c + "@" + u2c + "`"
    return tableName

def isValid(u1):
    danger = [34, 39, 64, 92, 96]
    for letter in u1:
        if ord(letter) < 32 or ord(letter) in danger:
            return letter
    return None

def torture(s):
    verdict = ""
    if len(s) < 8:
        verdict = "Password is too short"
        return verdict
    if not re.search(r"\d", s):
        verdict = "Password must contain at least one number"
        return verdict
    if not re.search(r"[a-z]", s):
        verdict = "Password must contain at least one lowercase letter"
        return verdict
    if not re.search(r"[A-Z]", s):
        verdict = "Password must contain at least one uppercase letter"
        return verdict
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", s):
        verdict = "Password must contain at least one special character"
        return verdict
    return verdict

@app.route('/', methods=['POST','GET'])
def index():
    token = session.get('jwt_token')
    if token:
        try:
            payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
            username = payload['username']
            update_online(username)
            return redirect(url_for('chat'))
        except jwt.exceptions.ExpiredSignatureError:
            # Token has expired
            pass
        except jwt.exceptions.InvalidTokenError:
            # Token is invalid
            pass
    return render_template("index.html")

@app.route('/<typer>', methods=['POST', 'GET'])
def add(typer):
    query = 'CREATE TABLE IF NOT EXISTS users (S_no INT NOT NULL AUTO_INCREMENT, username VARCHAR(255), email VARCHAR(255), password VARCHAR(1000), PRIMARY KEY (S_no));'
    print(query)
    cur.execute(query)
    query = 'CREATE TABLE IF NOT EXISTS lastSeen (contact_name VARCHAR(255) UNIQUE, lastSeenTime VARCHAR(255));'
    print(query)
    cur.execute(query)
    token = session.get('jwt_token')
    if token:
        try:
            payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
            username = payload['username']
            update_online(username)
            return redirect(url_for('chat'))
        except jwt.exceptions.ExpiredSignatureError:
            # Token has expired
            session.clear()
        except jwt.exceptions.InvalidTokenError:
            # Token is invalid
            session.clear()
    query = 'SELECT username, email, password FROM users'
    print(query)
    cur.execute(query)
    list_of_users = cur.fetchall()
    # print(list_of_users)
    if request.method == 'POST' and typer == 'signin':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        name = name.strip()
        name = name.lower()
        restricted = isValid(name)
        if restricted:
            return render_template("login.html", err=f"Username must not contain {restricted}", new=typer)
        if name == 'admin':
            return render_template("login.html", err="Please choose a different username", new=typer)
        if email == 'admin@iiit.ac.in':
            return render_template("login.html", err="Please choose a different email", new=typer)
        # torturing users
        verdict = torture(password)
        if verdict != "":
            return render_template("login.html", err=verdict, new=typer)
        password = hash_password(password)
        for items in list_of_users:
            if items[0] == name or items[1] == email:
                return render_template("login.html", err="User already exists", new=typer)
        query = f'insert into users (username, email, password) values ("{name}", "{email}", "{password}")'
        payload = {
            # 'user_id': 1,
            'username': name,
            'password': password,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)  # Token expiration time
        }
        token = jwt.encode(payload, app.secret_key, algorithm='HS256')
        session['jwt_token'] = token
        session['user_details'] = {'username': name}
        cmd = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
        print(cmd)
        cur.execute(cmd, (name, email, password))
        tableName = "`" + name + "`"
        query = f'CREATE TABLE {tableName} (S_no INT PRIMARY KEY AUTO_INCREMENT, contact_name VARCHAR(255), pending_status VARCHAR(17), currContact TEXT);'
        print(query)
        cur.execute(query)
        query = f'INSERT INTO lastSeen (contact_name, lastSeenTime) VALUES ("{name}", "online");'
        print(query)
        cur.execute(query)
        mydb.commit()
        return redirect(url_for('chat'))
    elif request.method == 'POST' and typer == 'login':
        email = request.form.get('email')
        password = request.form.get('password')
        query = 'SELECT username FROM users WHERE email = %s'
        print(query)
        cur.execute(query, (email,))
        name = cur.fetchone()
        if name == None:
            return render_template("login.html", err="User not found", new=typer)
        # print("name :", name[0])
        for items in list_of_users:
            if items[1] == email:
                if bcrypt.checkpw(password.encode('utf-8'), items[2].encode('utf-8')):
                    payload = {
                        'username': name[0],
                        # 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)  # Token expiration time
                    }
                    token = jwt.encode(payload, app.secret_key, algorithm='HS256')
                    session['jwt_token'] = token
                    session['user_details'] = {'username': name[0]}
                    # print(session)
                    query = f'UPDATE lastSeen SET lastSeenTime = "online" WHERE contact_name = "{name[0]}"'
                    print(query)
                    cur.execute(query)
                    mydb.commit()
                    return redirect(url_for('chat'))
        return render_template("login.html", err="Incorrect username / password", new=typer)
    mydb.commit()
    return render_template("login.html", new=typer)

@app.route('/request', methods=['POST', 'GET'])
def friendRequest():
    token = session.get('jwt_token')
    if not token:
        return redirect(url_for('index'))
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        username = payload['username']
        update_online(username)
    except jwt.exceptions.ExpiredSignatureError:
        # Token has expired
        session.clear()
        return redirect(url_for('index'))
    except jwt.exceptions.InvalidTokenError:
        # Token is invalid
        session.clear()
        return redirect(url_for('index'))
    # username = session['user_details']['username']
    # update_online(username)
    return render_template('frReq.html')

@app.route('/dbs', methods=['POST'])
def dbs():
    token = session.get('jwt_token')
    if not token:
        return redirect(url_for('index'))
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        username = payload['username']
        update_online(username)
    except jwt.exceptions.ExpiredSignatureError:
        # Token has expired
        session.clear()
        return redirect(url_for('index'))
    except jwt.exceptions.InvalidTokenError:
        # Token is invalid
        session.clear()
        return redirect(url_for('index'))
    data = request.json
    print(data)
    target = data['target']
    client = session['user_details']['username']
    if client == data['target']:
        responseObject = {
            'Value': "You cannot send a request to yourself",
            'Status': 1
        }
        return responseObject
    query = f'SELECT * FROM users WHERE username = "{target}"'
    print(query)
    cur.execute(query)
    found = cur.fetchone()
    if found:
        responseObject = {
            'Value': f"{target}",
            'Status': 0
        }
        return responseObject
    responseObject = {
        'Value': "User not found",
        'Status': 1
    }
    return responseObject

@app.route('/chat', methods=['POST', 'GET'])
def chat():
    token = session.get('jwt_token')
    if not token:
        return redirect(url_for('index'))
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        username = payload['username']
        update_online(username)
    except jwt.exceptions.ExpiredSignatureError:
        # Token has expired
        session.clear()
        return redirect(url_for('index'))
    except jwt.exceptions.InvalidTokenError:
        # Token is invalid
        session.clear()
        return redirect(url_for('index'))
    # username = session['user_details']['username']
    # update_online(username)
    tableName = "`" + username + "`"
    query = f'SELECT * FROM {tableName} WHERE pending_status = "Friend"'
    print(query)
    cur.execute(query)
    contacts = cur.fetchall()
    print(contacts)
    contacts = [x[1] for x in contacts]
    return render_template('chat.html', contacts=contacts, username=username)

@app.route('/pending', methods=['POST', 'GET'])
def pending():
    token = session.get('jwt_token')
    if not token:
        return redirect(url_for('index'))
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        username = payload['username']
        update_online(username)
    except jwt.exceptions.ExpiredSignatureError:
        # Token has expired
        session.clear()
        return redirect(url_for('index'))
    except jwt.exceptions.InvalidTokenError:
        # Token is invalid
        session.clear()
        return redirect(url_for('index'))
    # username = session['user_details']['username']
    # update_online(username)
    # for incoming requests
    tableName = "`" + username + "`"
    query = f'SELECT contact_name FROM {tableName} WHERE pending_status = "Incoming"'
    print(query)
    cur.execute(query)
    incoming_list = cur.fetchall()
    incoming_list = [x[0] for x in incoming_list]
    print(incoming_list)
    # for outgoing requests
    query = f'SELECT contact_name FROM {tableName} WHERE pending_status = "Outgoing"'
    cur.execute(query)
    print(query)
    outgoing_list = cur.fetchall()
    outgoing_list = [x[0] for x in outgoing_list]
    print(outgoing_list)
    return render_template('pending.html', inc=incoming_list, out=outgoing_list)

@app.route('/sendReq', methods = ['POST'])
def sendReq():
    token = session.get('jwt_token')
    if not token:
        return redirect(url_for('index'))
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        username = payload['username']
        update_online(username)
    except jwt.exceptions.ExpiredSignatureError:
        # Token has expired
        session.clear()
        return redirect(url_for('index'))
    except jwt.exceptions.InvalidTokenError:
        # Token is invalid
        session.clear()
        return redirect(url_for('index'))
    data = request.json
    print(data)
    username1 = session['user_details']['username']
    username2 = data['target']
    print(username1, username2)
    if username1 == username2:
        responseObject = {
            'status': "You cannot send a request to yourself"
        }
        return responseObject
    tableName1 = "`" + username1 + "`"
    tableName2 = "`" + username2 + "`"
    query = f'SELECT contact_name FROM {tableName1} WHERE contact_name = "{username2}"'
    print(query)
    cur.execute(query)
    result = cur.fetchone()
    if result:
        responseObject = {
            'status': f"{username2} is already in your friends list"
        }
        return responseObject
    # for inserting into username1 table
    query = f'INSERT INTO {tableName1} (contact_name, pending_status) VALUES ("{username2}", "Outgoing")'
    print(query)
    cur.execute(query)
    # for inserting into username2 table
    query = f'INSERT INTO {tableName2} (contact_name, pending_status) VALUES ("{username1}", "Incoming")'
    print(query)
    cur.execute(query)
    mydb.commit()
    responseObject = {
        'status': "Request Sent"
    }
    return responseObject

@app.route('/approve', methods = ['POST'])
def approve():
    token = session.get('jwt_token')
    if not token:
        return redirect(url_for('index'))
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        username = payload['username']
        update_online(username)
    except jwt.exceptions.ExpiredSignatureError:
        # Token has expired
        session.clear()
        return redirect(url_for('index'))
    except jwt.exceptions.InvalidTokenError:
        # Token is invalid
        session.clear()
        return redirect(url_for('index'))
    data = request.json
    print(data)
    username = session['user_details']['username']
    target = data['target']
    tableName = "`" + username + "`"
    tableNameT = "`" + target + "`"
    if data['status'] == "rejected":
        # sender query
        query = f'DELETE FROM {tableName} WHERE contact_name = "{target}"'
        print(query)
        cur.execute(query)
        # target query
        query = f'DELETE FROM {tableNameT} WHERE contact_name = "{username}"'
        print(query)
        cur.execute(query)
        responseObject = {
            'status': f"Successfully rejected {target}"
        }
        mydb.commit()
        return responseObject
    # sender query
    query = f'UPDATE {tableName} SET pending_status = "Friend" WHERE contact_name = "{target}"'
    print(query)
    cur.execute(query)
    # target query
    query = f'UPDATE {tableNameT} SET pending_status = "Friend" WHERE contact_name = "{username}"'
    print(query)
    cur.execute(query)
    # create conversation thread
    tableName = getTableName(username, target)
    query = f'CREATE Table {tableName} ( S_no INT PRIMARY KEY AUTO_INCREMENT, textBody TEXT, sender VARCHAR(255), receiver VARCHAR(255), msgTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP, image LONGBLOB, audio LONGBLOB, msgType VARCHAR(20), msgStatus VARCHAR(20), replyMsg INT, deleteStatus VARCHAR(20), forwardedFlag INT DEFAULT 0);'
    print(query)
    cur.execute(query)
    mydb.commit()
    responseObject = {
        'status': f"Added {target} to your contacts / friends list"
    }
    return responseObject

@app.route('/showChat', methods=['GET', 'POST'])
def showChat():
    token = session.get('jwt_token')
    if not token:
        return redirect(url_for('index'))
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        username = payload['username']
        update_online(username)
    except jwt.exceptions.ExpiredSignatureError:
        # Token has expired
        session.clear()
        return redirect(url_for('index'))
    except jwt.exceptions.InvalidTokenError:
        # Token is invalid
        session.clear()
        return redirect(url_for('index'))
    data = request.json
    print(data)
    target = data['target']
    username = session['user_details']['username']
    tableName = "`" + username + "`"
    query = f'UPDATE {tableName} SET currContact = "{target}"'
    print(query)
    cur.execute(query)
    mydb.commit()
    tableName = getTableName(username, target)
    query = f'UPDATE {tableName} SET msgStatus = "seen" WHERE sender = "{target}"'
    print(query)
    cur.execute(query)
    query = f'SELECT * FROM {tableName}'
    print(query)
    cur.execute(query)
    msgs = cur.fetchall()
    mydb.commit()
    query = f'SELECT lastSeenTime FROM lastSeen WHERE contact_name = "{target}"'
    cur.execute(query)
    lastSeen = cur.fetchone()
    print(msgs)
    responseObject = {
        'data': msgs,
        'lastSeen': lastSeen
    }
    return responseObject

@app.route('/sendMsg', methods=['POST'])
def sendMsg():
    token = session.get('jwt_token')
    if not token:
        return redirect(url_for('index'))
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        username = payload['username']
        update_online(username)
    except jwt.exceptions.ExpiredSignatureError:
        # Token has expired
        session.clear()
        return redirect(url_for('index'))
    except jwt.exceptions.InvalidTokenError:
        # Token is invalid
        session.clear()
        return redirect(url_for('index'))
    data = request.json
    print(data)
    sender = session['user_details']['username']
    textBody = data['textBody']
    receiver = data['receiver']
    image = data['image']
    audio = data['audio']
    msgType = data['msgType']
    replyMessage = data['replyMessage']
    forwardedFlag = data['forwardedFlag']
    msgStatus = "sent"
    query = f'SELECT lastSeenTime FROM lastSeen WHERE contact_name = "{receiver}"'
    print(query)
    cur.execute(query)
    status = cur.fetchone()
    if status == "online":
        tableName = "`" + receiver + "`"
        query = f'SELECT currContact FROM {tableName} LIMIT 1'
        print(query)
        cur.execute(query)
        currContact = cur.fetchone()
        if currContact == sender:
            msgStatus = "seen"
    # print(msgStatus)
    tableName = getTableName(sender, receiver)
    query = f'INSERT INTO {tableName} (textBody, sender, receiver, msgType, msgStatus, replyMsg, deleteStatus, forwardedFlag) VALUES ("{textBody}", "{sender}", "{receiver}", "{msgType}", "{msgStatus}", {replyMessage}, "both", {forwardedFlag})'
    print(query)
    cur.execute(query)
    mydb.commit()
    query = f'SELECT * FROM {tableName} ORDER BY S_no DESC LIMIT 1'
    cur.execute(query)
    msg = cur.fetchall()
    print(msg)
    msg = msg[0]
    responseObject = {
        'status': "message sent",
        'data': msg
    }
    return responseObject

@app.route('/editMsg', methods=['POST'])
def editMsg():
    token = session.get('jwt_token')
    if not token:
        return redirect(url_for('index'))
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        username = payload['username']
        update_online(username)
    except jwt.exceptions.ExpiredSignatureError:
        # Token has expired
        session.clear()
        return redirect(url_for('index'))
    except jwt.exceptions.InvalidTokenError:
        # Token is invalid
        session.clear()
        return redirect(url_for('index'))
    username = session['user_details']['username']
    data = request.json
    print(data)
    target = data['target']
    id = data['id']
    modifiedBody = data['textBody']
    tableName = getTableName(username, target)
    query = f'UPDATE {tableName} SET textBody = "{modifiedBody}", msgStatus = "sent" WHERE S_no = {id}'
    print(query)
    cur.execute(query)
    mydb.commit()
    responseObject = {
        'status': "Edited message successfully"
    }
    return responseObject

@app.route('/deleteMsg', methods=['POST'])
def deleteMsg():
    token = session.get('jwt_token')
    if not token:
        return redirect(url_for('index'))
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        username = payload['username']
        update_online(username)
    except jwt.exceptions.ExpiredSignatureError:
        # Token has expired
        session.clear()
        return redirect(url_for('index'))
    except jwt.exceptions.InvalidTokenError:
        # Token is invalid
        session.clear()
        return redirect(url_for('index'))
    username = session['user_details']['username']
    data = request.json
    print(data)
    id = data['id']
    target = data['target']
    tableName = getTableName(username, target)
    query = f'DELETE FROM {tableName} WHERE S_no = {id}'
    print(query)
    cur.execute(query)
    mydb.commit()
    responseObject = {
        'status': "Message deleted"
    }
    return responseObject

@app.route('/clearChat', methods=['POST'])
def clearChat():
    token = session.get('jwt_token')
    if not token:
        return redirect(url_for('index'))
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        username = payload['username']
        update_online(username)
    except jwt.exceptions.ExpiredSignatureError:
        # Token has expired
        session.clear()
        return redirect(url_for('index'))
    except jwt.exceptions.InvalidTokenError:
        # Token is invalid
        session.clear()
        return redirect(url_for('index'))
    data = request.json
    print(data)
    username = session['user_details']['username']
    contact = data['target']
    tableName = getTableName(username, contact)
    query = f'DELETE FROM {tableName}'
    print(query)
    cur.execute(query)
    mydb.commit()
    responseObject = {
        'status': "Successfully deleted all the mssages"
    }
    return responseObject

@app.route('/deleteContact', methods=['POST'])
def deleteContact():
    token = session.get('jwt_token')
    if not token:
        return redirect(url_for('index'))
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        username = payload['username']
        update_online(username)
    except jwt.exceptions.ExpiredSignatureError:
        # Token has expired
        session.clear()
        return redirect(url_for('index'))
    except jwt.exceptions.InvalidTokenError:
        # Token is invalid
        session.clear()
        return redirect(url_for('index'))
    responseObject = {}
    return responseObject

@app.route('/close', methods=['POST'])
def close():
    username = session['user_details']['username']
    current_datetime = datetime.datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    print("Formatted date and time:", formatted_datetime)
    query = f'UPDATE lastSeen SET lastSeenTime = "{formatted_datetime}" WHERE contact_name = "{username}"'
    print(query)
    cur.execute(query)
    mydb.commit()
    responseObject = {
        'status': 'OK'
    }
    return responseObject

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    username = session['user_details']['username']
    current_datetime = datetime.datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    print("Formatted date and time:", formatted_datetime)
    query = f'UPDATE lastSeen SET lastSeenTime = "{formatted_datetime}" WHERE contact_name = "{username}"'
    print(query)
    cur.execute(query)
    mydb.commit()
    session.pop('jwt_token', None)
    session.pop('user_details', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
