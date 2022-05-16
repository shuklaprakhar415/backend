from email.policy import default
from turtle import title
from flask import Flask , jsonify , request
from flask_sqlalchemy import SQLAlchemy
import datetime
from flask_marshmallow import Marshmallow
from sqlalchemy import null
import base64

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///attendanceflask.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db=SQLAlchemy(app)
ma=Marshmallow(app)

class Students(db.Model):
    id = db.Column(db.Integer , primary_key=True)
    admission_No = db.Column(db.String(10))
    name = db.Column(db.String(50))
    image_known = db.Column(db.Text())
    image_unknown = db.Column(db.Text() , default = "")
    present_status = db.Column(db.Boolean , default = False)
    date = db.Column(db.DateTime , default = datetime.datetime.now)


    def __init__(self , admission_No , name , image_known):
        self.admission_No = admission_No
        self.name = name
        self.image_known = image_known

class StudentSchema(ma.Schema):
    class Meta:
        fields = ('id' , 'admission_No' , 'name' , 'image_known', 'image_unknown' ,'present_status' , 'date')

student_schema = StudentSchema()
students_schema = StudentSchema(many=True)
        


@app.route('/get' , methods = ['GET'])
def get_student_list():
    all_students = Students.query.all()
    results = students_schema.dump(all_students)
    return jsonify(results)

@app.route('/add_student' , methods = ['POST'])
def add_student():
    admission_No = request.json['admission_No']
    name = request.json['name']
    image_known = request.json['image_known']

    students = Students(admission_No , name , image_known)
    db.session.add(students)
    db.session.commit()
    return student_schema.jsonify(students)

# ---Marking Attendance Route---
@app.route('/mark_attendance/<admission_No>/' , methods = ['PUT'])
def mark_attendance(admission_No):
    student = Students.query.filter_by(admission_No = admission_No).first()
    image_unknown = request.json['image_unknown']
    present_status = request.json['present_status']
    # Now decoding unknown img and saving it it unknown_img.png
    image_64_decode = base64.b64decode(image_unknown)
    unknown_img = open('unknown_img.jpeg' , 'wb')
    unknown_img.write(image_64_decode)
    # Now unknown_img contains image for testing
    

    db.session.commit()
    return student_schema.jsonify(student)




if __name__ == "__main__":
    app.run(debug=True)