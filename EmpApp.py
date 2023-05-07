from flask import Flask, render_template, request, redirect, flash
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

# Index
@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('index.html')

# About Us
@app.route("/AboutUs", methods=['GET'])
def about():
    return render_template('AboutUs.html')

# View all employee
@app.route("/ViewEmp", methods=['GET'])
def viewEmployee():
    cursor = db_conn.cursor() 
    cursor.execute("SELECT * FROM employee")
    employee = cursor.fetchall()
    cursor.close()
    print(employee)
    return render_template('ViewEmp.html', employee = employee)

# Add Employee
@app.route("/AddEmp", methods=['POST', 'GET'])
def AddEmp():
    if request.method == 'GET':
        return render_template('AddEmp.html')
    
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        pri_skill = request.form['pri_skill']
        location = request.form['location']
        emp_image_file = request.files['emp_image_file']

        insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
        cursor = db_conn.cursor()

        try:            
            # To check if emp_id already exists
            check_sql = "SELECT * FROM employee WHERE emp_id = %s"
            cursor.execute(check_sql, (emp_id,))
            result = cursor.fetchone()

            if result:
                error_msg = "Employee with this ID already exists"
                return render_template('AddEmp.html', error_msg=error_msg, emp_id=emp_id, first_name=first_name, last_name=last_name, pri_skill=pri_skill, location=location)
           
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

# Edit Employee
@app.route("/EditEmployee/<int:emp_id>", methods=['POST', 'GET'])
def EditEmp(emp_id):
    if request.method == 'GET':
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM employee WHERE emp_id=%s", (emp_id))
        employee = cursor.fetchone()
        cursor.close()

        # Pass employee record to EditEmployee template
        return render_template('EditEmployee.html', employee=employee)
    
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        pri_skill = request.form['pri_skill']
        location = request.form['location']

        update_sql = "UPDATE employee SET first_name=%s, last_name=%s, pri_skill=%s, location=%s WHERE emp_id=%s"
        cursor = db_conn.cursor()

        cursor.execute(update_sql, (first_name, last_name, pri_skill, location, emp_id))
        db_conn.commit()
        cursor.close()

        print("Update Employee done...")
        return redirect('/ViewEmp')


#View all payroll
@app.route("/ViewPayroll", methods=['GET'])
def viewPayroll():
    cursor = db_conn.cursor() 
    cursor.execute("SELECT * FROM Payroll")
    payroll = cursor.fetchall()
    cursor.close()
    print(payroll)
    return render_template('ViewPayroll.html', payroll = payroll)

#Generate Payroll ID
def generate_pr_id():
    cursor = db_conn.cursor() 
    cursor.execute("SELECT MAX(payroll_id) FROM Payroll")
    max_id = cursor.fetchone()[0]
    if max_id is not None:
        count = int(max_id[2:]) + 1
    else:
        count = 1
    pr_id = "PR{:03d}".format(count)
    return pr_id

#Add payroll    
@app.route("/AddPayroll", methods=['POST', 'GET'])
def AddPayroll():

    if request.method == 'GET':
        cursor = db_conn.cursor()
        cursor.execute("SELECT emp_id FROM employee")
        employee_ids = cursor.fetchall()
        cursor.close()

        # Pass employee ids to AddPayroll
        return render_template('AddPayroll.html', employee_ids=employee_ids)

    if request.method == 'POST':
        emp_id = request.form['emp_id']
        emp_hourly_rate = int(request.form['hourly_rate'])
        emp_hours_worked = int(request.form['working_hours'])
        emp_bonus = int(request.form['bonus'])

        if int(emp_hourly_rate) < 0:
            return "please enter valid hourly rate!"
        
        if int(emp_hours_worked) < 0:
            return "please enter valid worked hours!"
        
        if int(emp_bonus) < 0:
            return "please enter at least 1 bonus amount"

        pr_id = generate_pr_id()

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
@app.route("/EditPayroll/<string:payroll_id>", methods=['POST', 'GET'])
def EditPayroll(payroll_id):
    if request.method == 'GET':
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM Payroll WHERE payroll_id=%s", (payroll_id,))
        payroll = cursor.fetchone()
        cursor.close()

        # Pass payroll record to EditPayroll template
        return render_template('EditPayroll.html', payroll=payroll)

    if request.method == 'POST':
        emp_hourly_rate = int(request.form['hourly_rate'])
        emp_hours_worked = int(request.form['working_hours'])
        emp_bonus = int(request.form['bonus'])

        if int(emp_hourly_rate) < 0:
            return "please enter valid hourly rate!"
        
        if int(emp_hours_worked) < 0:
            return "please enter valid worked hours!"
        
        if int(emp_bonus) < 0:
            return "please enter at least 1 bonus amount"

        gross_pay = (emp_hourly_rate * emp_hours_worked) + emp_bonus
        tax = 0.15
        gross_pay_tax = gross_pay * tax
        net_pay = gross_pay - gross_pay_tax

        update_sql = "UPDATE Payroll SET hourly_rate=%s, hours_worked=%s, bonus=%s, gross_pay=%s,net_pay=%s WHERE payroll_id=%s"
        cursor = db_conn.cursor()

        cursor.execute(update_sql, (emp_hourly_rate, emp_hours_worked, emp_bonus, gross_pay, net_pay, payroll_id))
        db_conn.commit()
        cursor.close()

        print("Update Payroll Successfully...")
        return redirect('/ViewPayroll')    

@app.route("/DeletePayroll/<string:payroll_id>", methods=['GET'])
def DeletePayroll(payroll_id):

    delete_sql = "DELETE FROM Payroll WHERE payroll_id=%s"
    cursor = db_conn.cursor()

    cursor.execute(delete_sql, (payroll_id))
    db_conn.commit()
    cursor.close()

    print("Delete Payroll Successfully...")
    return redirect('/ViewPayroll')    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

