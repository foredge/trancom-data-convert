from flask import Flask

import csv_uploads
import send_log_mail

app = Flask(__name__)

@app.route('/')
def main():
    try:
        csv_uploads.main()
        return f'csv uploads ok'
    except:
        return f'csv uploads failed'

@app.route('/mail')
def mail():
    try:
        send_log_mail.main()
        return f'mail ok'
    except:
        return f'mail failed'

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(8000))