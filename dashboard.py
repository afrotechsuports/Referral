from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import csv
import io

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session management

# Hardcoded login credentials
EMAIL = "afrotechsuports@gmail.com"
PASSWORD = "All3434Log"

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == EMAIL and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid email or password")
    return render_template('login.html', error=None)

# Dashboard route
@app.route('/')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = sqlite3.connect("referrals.db")
    c = conn.cursor()
    # Get all users with points > 0
    c.execute("SELECT user_id, username, points, emoji, link_views, link_sends FROM users WHERE points > 0")
    inviters = c.fetchall()
    referral_data = []
    for inviter in inviters:
        inviter_id, username, points, emoji, link_views, link_sends = inviter
        c.execute("SELECT invited_username FROM referrals WHERE inviter_id = ?", (inviter_id,))
        invited_users = [row[0] for row in c.fetchall()]
        referral_data.append({
            "inviter_id": inviter_id,
            "username": username,
            "points": points,
            "emoji": emoji,
            "invited_users": invited_users,
            "total_referrals": len(invited_users),
            "link_views": link_views,
            "link_sends": link_sends
        })
    conn.close()
    return render_template("index.html", referral_data=referral_data)

# Export to CSV route
@app.route('/export', methods=['POST'])
def export():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    selected_users = request.form.getlist('selected_users')
    conn = sqlite3.connect("referrals.db")
    c = conn.cursor()
    output = io.StringIO()
    writer = csv.writer(output)
    # Write CSV headers
    writer.writerow(["Inviter ID", "Username", "Points", "Total Referrals", "Link Views", "Link Sends", "Invited Users"])
    for user_id in selected_users:
        c.execute("SELECT user_id, username, points, link_views, link_sends FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()
        if user:
            inviter_id, username, points, link_views, link_sends = user
            c.execute("SELECT invited_username FROM referrals WHERE inviter_id = ?", (inviter_id,))
            invited_users = [row[0] for row in c.fetchall()]
            writer.writerow([inviter_id, username, points, len(invited_users), link_views, link_sends, ", ".join(invited_users)])
    conn.close()
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='referral_data.csv'
    )

# Logout route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    # Use a production-ready WSGI server for development to avoid async issues
    from werkzeug.serving import run_simple
    run_simple('127.0.0.1', 5000, app, use_reloader=True, use_debugger=True)