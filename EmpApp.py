from flask import Flask, render_template, request, redirect
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('index.html')


@app.route("/about", methods=['POST'])
def about():
    return render_template('www.intellipaat.com')


@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)

#View all payroll
@app.route("/ViewPayroll", methods=['GET'])
def viewPayroll():
    cursor = db_conn.cursor() 
    cursor.execute("SELECT * FROM Payroll")
    payroll = cursor.fetchall()
    cursor.close()
    print(payroll)
    return render_template('ViewPayroll.html', payroll = payroll)

#Add payroll    
@app.route("/AddPayroll", methods=['POST', 'GET'])
def AddPayroll():
    if request.method == 'GET':
        return render_template('AddPayroll.html')

    if request.method == 'POST':
        emp_id = request.form['emp_id']
        emp_hourly_rate = float(request.form['emp_hourly_rate'])
        emp_hours_worked = float(request.form['emp_hours_worked'])
        emp_bonus = float(request.form['emp.bonus'])

        if float(emp_hourly_rate) < 0:
            return "please enter valid hourly rate!"

        if float(emp_hours_worked) < 0:
            return "please enter valid worked hours!"

        if (emp_bonus) < 0:
            return "please enter at least 1 bonus amount"

        pr_id = "PR" + str(emp_id)

        gross_pay = (emp_hourly_rate * emp_hours_worked) + emp_bonus
        tax = 0.15
        gross_pay_tax = gross_pay * tax
        net_pay = gross_pay - gross_pay_tax

        insert_sql = "INSERT INTO Payroll VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor = db_conn.cursor()
        cursor.execute(insert_sql, (pr_id, emp_id, emp_hourly_rate, emp_hours_worked, emp_bonus, gross_pay, net_pay))
        db_conn.commit()

        cursor.close()

        print("Add New Payroll Successfully...")
        return redirect('/ViewPayroll')

#Edit Payroll
@app.route("/EditPayroll/<string:pr_id>", methods=['POST'])
def EditPayroll(pr_id):
    emp_hourly_rate = float(request.form['emp_hourly_rate'])
    emp_hours_worked = float(request.form['emp_hours_worked'])
    emp_bonus = float(request.form['emp.bonus'])
  
    if float(emp_hourly_rate) < 0:
        return "please enter a valid hourly rate!"
    
    if float(emp_hours_worked) < 0:
        return "please enter a valid worked hours!"
    
    if (emp_bonus) < 0:
        return "please enter at least 1 bonus amount"

    gross_pay = (emp_hourly_rate * emp_hours_worked) + emp_bonus
    tax = 0.15
    gross_pay_tax = gross_pay * tax
    net_pay = gross_pay - gross_pay_tax

    update_sql = "UPDATE Payroll SET hourly_rate=%s, hours_worked=%s, bonus=%s, gross_pay=%s,net_pay=%s WHERE payroll_id=%s"
    cursor = db_conn.cursor()

    cursor.execute(update_sql, (emp_hourly_rate, emp_hours_worked, emp_bonus, gross_pay, net_pay, pr_id))
    db_conn.commit()
    cursor.close()

    print("Update Payroll Successfully...")
    return redirect('/ViewPayroll')    

@app.route("/DeletePayroll/<string:pr_id>", methods=['POST'])
def DeletePayroll(pr_id):

    delete_sql = "DELETE FROM Payroll WHERE payroll_id=%s"
    cursor = db_conn.cursor()

    cursor.execute(delattr, (pr_id))
    db_conn.commit()
    cursor.close()

    print("Delete Payroll Successfully...")
    return redirect('/ViewPayroll')    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

