from flask import Flask, render_template, request, send_file, jsonify
from datetime import datetime, timedelta
import sqlite3

app = Flask(__name__)

# Utility function to convert EST to IST
def convert_est_to_ist(est_time):
    est_format = "%Y-%m-%dT%H:%M"
    est_time_obj = datetime.strptime(est_time, est_format)
    ist_time_obj = est_time_obj + timedelta(hours=10, minutes=30)
    return ist_time_obj.strftime(est_format)

# Route for the form
@app.route('/', methods=['GET', 'POST'])
def form():
    success_message = ""
    if request.method == 'POST':
        category = request.form['category']
        received_time_est = request.form['received_time_est']
        received_time_ist = convert_est_to_ist(received_time_est)
        pims_id = request.form['pims_id']
        completed_time_est = request.form['completed_time_est']
        completed_time_ist = convert_est_to_ist(completed_time_est)
        completed_by = request.form['completed_by']

        # Insert into database
        conn = sqlite3.connect('production.db')
        c = conn.cursor()
        c.execute('''INSERT INTO production_data 
                    (category, received_time_est, received_time_ist, pims_id, completed_time_est, completed_time_ist, completed_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                    (category, received_time_est, received_time_ist, pims_id, completed_time_est, completed_time_ist, completed_by))
        
        conn.commit()
        conn.close()

        success_message = "Data Submitted Successfully!"  # Set success message

    return render_template('form.html', success_message=success_message)

# Route for live data page
@app.route('/live_report', methods=['GET'])
def live_report():
    return render_template('live_report.html')

# Route to fetch live data
@app.route('/live_data', methods=['GET'])
def live_data():
    conn = sqlite3.connect('production.db')
    c = conn.cursor()
    
    c.execute('''SELECT * FROM production_data ORDER BY id DESC LIMIT 10''')  # Get the latest 10 records
    data = c.fetchall()
    conn.close()
    
    # Convert data to a format suitable for JSON
    live_data = []
    for row in data:
        live_data.append({
            'id': row[0],
            'category': row[1],
            'received_time_est': row[2],
            'received_time_ist': row[3],
            'pims_id': row[4],
            'completed_time_est': row[5],
            'completed_time_ist': row[6],
            'completed_by': row[7]
        })

    return jsonify(live_data)

# Route to generate the report
@app.route('/download_report', methods=['GET'])
def download_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Convert dates to the format used in the database
    start_date_str = f"{start_date} 00:00:00"
    end_date_str = f"{end_date} 23:59:59"

    conn = sqlite3.connect('production.db')
    c = conn.cursor()
    
    # Select data within the date range
    c.execute('''SELECT * FROM production_data 
                 WHERE received_time_est BETWEEN ? AND ?''', 
                 (start_date_str, end_date_str))
    
    data = c.fetchall()
    conn.close()

    # Generate a CSV file for the report
    report_filename = f"report_{datetime.now().strftime('%Y-%m-%d')}.csv"
    with open(report_filename, "w") as f:
        f.write("SL.NO,Category,Received Time (EST),Received Time (IST),PIMS ID,Completed Time (EST),Completed Time (IST),Completed By\n")
        for index, row in enumerate(data, start=1):
            # Format the datetime fields
            received_time_est = row[2].replace("T", " ")
            received_time_ist = row[3].replace("T", " ")
            completed_time_est = row[5].replace("T", " ")
            completed_time_ist = row[6].replace("T", " ")
            
            # Convert PIMS ID to string
            pims_id = str(row[4])
            
            f.write(",".join([str(index), row[1], received_time_est, received_time_ist, pims_id, completed_time_est, completed_time_ist, row[7]]) + "\n")

    return send_file(report_filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
