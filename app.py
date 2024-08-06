import threading
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, send_file
import time
import os
import mimetypes
from turbo_flask import Turbo
import socket


mimetypes.add_type('application/javascript', '.js')

app = Flask(__name__)
turbo = Turbo(app)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.secret_key = "whatever lol"

TEAMS_FILE = "data/teams.txt"
PROBLEMS_FILE = "data/problems.txt"
TIMELINE_FILE = "data/timeline.txt"

teams = []
passwords = []
problems = []
timeline = []
headers = []
table = [[]]


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.errorhandler(413)
def too_large(e):
    flash("❌ File Too Large")
    return redirect(url_for('upload'))


@app.route('/pset.pdf', methods=['GET', 'POST'])
def pset():
    if timeline[0] != "yet":
        return send_file('pset/pset.pdf', download_name='pset.pdf')
    return '<h1 style="font-family: sans-serif"><b>❌ Contest Hasn\'t Started</b></h1>'


@app.route('/scoreboard', methods=['GET', 'POST'])
def scoreboard():
    return render_template("scoreboard.html", n=len(headers), headers=headers, m=len(teams), table=table,
                           time=timeline[1], start=timeline[0], ip=socket.gethostbyname(socket.gethostname()))


@app.route('/', methods=['GET', 'POST'])
def upload():
    team = request.cookies.get('team')

    if request.method == 'POST':
        uploaded_file = request.files['file']
        problem = request.form.get("problem")
        filename = secure_filename(uploaded_file.filename)

        if team is None or int(team) >= len(teams) or passwords[int(team)] != request.cookies.get('password'):
            flash("❌ Invalid Credentials")
            return redirect(url_for('login'))

        if timeline[0] == "yet":
            flash("❌ Contest Hasn\'t Started")
            return redirect(url_for('upload'))

        if filename == '':
            flash("❌ No File Selected")
            return redirect(url_for('upload'))

        if team == '':
            flash("❌ No Team Selected")
            return redirect(url_for('upload'))

        if problem == '':
            flash("❌ No Problem Selected")
            return redirect(url_for('upload'))

        file_ext = os.path.splitext(filename)[1]
        if file_ext != ".py":
            flash("❌ File Type Not Python")
            return redirect(url_for('upload'))

        uploaded_file.save(os.path.join(
            'submissions', f"{int(os.listdir('submissions')[-1][0]) + 1}_{teams[int(team)]}_{problems[int(problem)]}.py"))
        flash("✅ Solution Submitted Successfully")
        return redirect(url_for('upload'))

    if team is None:
        return redirect(url_for('login'))

    return render_template("upload.html", n=len(teams), teams=teams, m=len(problems), problems=problems, team=int(team))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get("password") != passwords[int(request.form.get("team"))]:
            flash("❌ Incorrect Password")
            return redirect(url_for('login'))
        resp = redirect(url_for('upload'))
        resp.set_cookie('team', request.form.get("team"))
        resp.set_cookie('password', request.form.get("password"))
        return resp
    return render_template("login.html", n=len(teams), teams=teams)


def updateData():
    stamps = [0.0, 0.0, 0.0]
    submissions = []
    with app.app_context():
        while True:
            global teams, passwords, problems, timeline, table, headers

            new_submissions = os.listdir("submissions")
            new_stamps = [os.stat(TEAMS_FILE).st_mtime, os.stat(
                PROBLEMS_FILE).st_mtime, os.stat(TIMELINE_FILE).st_mtime]
            if new_stamps == stamps and submissions == new_submissions:
                time.sleep(1)
                continue
            stamps = new_stamps
            submissions = new_submissions

            teams = [line.split('_')[0] for line in open(
                TEAMS_FILE, "r").read().splitlines()]
            passwords = [line.split('_')[1] for line in open(
                TEAMS_FILE, "r").read().splitlines()]
            problems = open(PROBLEMS_FILE, "r").read().splitlines()
            timeline = open(TIMELINE_FILE, "r").read().splitlines()
            table = [([0 for i in range(3)] + ["N" for i in range(len(problems))])
                     for j in range(len(teams))]

            queue = []
            blind = False
            for event in timeline:
                if event == "blind":
                    blind = True
                    continue

                if event == "=":
                    if not queue:
                        continue
                    f_event = queue.pop(0).split("_")
                else:
                    f_event = event.split("_")

                if len(f_event) != 3:
                    if len(f_event) == 2 and f_event[0] in teams:
                        table[teams.index(f_event[0])][1] += int(f_event[1])
                    continue

                if blind and event != "=":
                    queue.append(event)
                    continue

                table[teams.index(f_event[1])][3 +
                                               problems.index(f_event[2])] = "Y"
                if f_event[2].find("(Hard)") != -1:
                    table[teams.index(f_event[1])][1] += 20
                elif f_event[2].find("(Medium)") != -1:
                    table[teams.index(f_event[1])][1] += 10
                else:
                    table[teams.index(f_event[1])][1] += 5

            for filename in submissions:
                f_filename = filename[:-3].split("_")
                if len(f_filename) != 3:
                    continue
                if table[teams.index(f_filename[1])][3 + problems.index(f_filename[2])] != "Y":
                    table[teams.index(f_filename[1])][3 +
                                                      problems.index(f_filename[2])] = "P"

            for i in range(len(teams)):
                table[i][0] = teams[i]
                if table[i][1] >= 75:
                    table[i][2] = "Fourth"
                elif table[i][1] >= 50:
                    table[i][2] = "Third"
                elif table[i][1] >= 30:
                    table[i][2] = "Second"
                elif table[i][1] >= 15:
                    table[i][2] = "First"
                else:
                    table[i][2] = "Zero"

            table = sorted(table, key=lambda l: l[1], reverse=True)
            headers = ["Team", "Points", "Milestone"] + \
                list(range(1, len(problems) + 1))

            for i in range(len(teams)):
                j = i
                while j and table[i][1] == table[j - 1][1]:
                    j -= 1
                table[i].append(j + 1)

            turbo.push(turbo.replace(render_template('table.html', n=len(
                headers), headers=headers, m=len(teams), table=table, start=timeline[0]), 'table1'))

            time.sleep(1)


if __name__ == '__main__':
    threading.Thread(target=updateData).start()
    app.run(host='0.0.0.0', port=80)
