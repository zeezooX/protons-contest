import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.secret_key = "whatever lol"


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.errorhandler(413)
def too_large(e):
    flash("❌ File Too Large")
    return redirect(url_for('upload'))


@app.route('/', methods=['GET', 'POST'])
def upload():
    teams = open("data/teams.txt", "r").read().splitlines()
    problems = open("data/problems.txt", "r").read().splitlines()

    if request.method == 'POST':
        uploaded_file = request.files['file']
        team = request.form.get("team")
        problem = request.form.get("problem")
        filename = secure_filename(uploaded_file.filename)

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
            'submissions', f"{len(os.listdir('submissions'))}_{teams[int(team)]}_{problems[int(problem)]}.py"))
        flash("✅ Solution Submitted Successfully")
        return redirect(url_for('upload'))

    return render_template("upload.html", n=len(teams), teams=teams, m=len(problems), problems=problems)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
