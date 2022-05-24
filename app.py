from email.policy import default
from fileinput import filename
from msilib.schema import Directory
from turtle import title
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
# import datetime
from flask_marshmallow import Marshmallow
from sqlalchemy import null
import base64
import urllib.request
from werkzeug.utils import secure_filename
import io
import os
from pathlib import Path
import pathlib
import cv2
import numpy as np
import face_recognition
from PIL import Image
from imageio import imread
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)
app.secret_key = "prakharshukla"
UPLOAD_FOLDER = 'static/ImgUploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///attendanceflask.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


db = SQLAlchemy(app)
ma = Marshmallow(app)


class Students(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admission_No = db.Column(db.String(10))
    student_name = db.Column(db.String(50))
    image_uploded = db.Column(db.Boolean, default=False)
    present_status = db.Column(db.Boolean, default=False)
    
    date = db.Column(db.String(20), default="00:00")
    

    def __init__(self, admission_No, student_name):
        self.admission_No = admission_No
        self.student_name = student_name


class StudentSchema(ma.Schema):
    class Meta:
        fields = ('id', 'admission_No', 'student_name',
                  'image_uploded', 'present_status', 'date')


student_schema = StudentSchema()
students_schema = StudentSchema(many=True)


@app.route('/get', methods=['GET'])
def get_student_list():
    all_students = Students.query.all()
    results = students_schema.dump(all_students)
    return jsonify(results)

# ---Adding Student Name and Admission No list Route---
@app.route('/add_student', methods=['POST'])
def add_student():
    admission_No = request.json['admission_No']
    student_name = request.json['student_name']
    students = Students(admission_No, student_name)
    db.session.add(students)
    db.session.commit()
    return student_schema.jsonify(students)


# ---Adding Student Image while adding image to list Route---


@app.route('/add_student/image_upload/<admission_No>/', methods=['POST'])
def add_student_image(admission_No):
    student = Students.query.filter_by(admission_No=admission_No).first()
    if 'file' not in request.files:
        resp = jsonify({'message': 'No file part in the request'})
        resp.status_code = 400
        return resp
    file = request.files['file']
    if file.filename == '':
        resp = jsonify({'message': 'No file part in the request'})
        resp.status_code = 400
        return resp
    if file and allowed_file(file.filename):
        filename = file.filename
        file_extension = os.path.splitext(filename)[1]
        filename = f'{admission_No}{file_extension}'
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        student.image_uploded = True
        db.session.commit()
        resp = jsonify({'message': 'File successfully uploaded'})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify({'message': 'Allowed file types are png, jpg, jpeg'})
        resp.status_code = 400
        return resp

# ---Marking Attendance Route---


@app.route('/mark_attendance/<admission_No>/', methods=['POST'])
def mark_attendance(admission_No):
    student = Students.query.filter_by(admission_No=admission_No).first()
    
    base64_string = request.json['base64_string']
    
    path = 'static/ImgUploads'
    images = []
    classNames = []
    myList = os.listdir(path)
    for cl in myList:
        curImg = cv2.imread(f'{path}/{cl}')
        images.append(curImg)
        classNames.append(os.path.splitext(cl)[0])

    def findEncodings(images):
        encodeList = []
        for img in images:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encode = face_recognition.face_encodings(img)[0]
            encodeList.append(encode)
        return encodeList

    encodeListKnown = findEncodings(images)

    def data_uri_to_cv2_img(uri):
        encoded_data = uri.split(',')[1]
        nparr = np.fromstring(base64.b64decode(encoded_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img

    img =data_uri_to_cv2_img(base64_string)
    imgS = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    facesCurFrame = face_recognition.face_locations(imgS)
    encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace , tolerance=0.6)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
        matchIndex = np.argmin(faceDis)

        if matches[matchIndex]:
            name = classNames[matchIndex].upper()
            if name == admission_No:
                student.present_status = True
                now = datetime.now()
                dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
                student.date = dt_string
                db.session.commit()

                return jsonify({'mesaage': 'Face Found'})

            else:
                return jsonify({'mesaage': 'Face NOT Found'})

        else:
            return jsonify({'mesaage': 'Face NOT Found'})
    cv2.waitKey(1)


if __name__ == "__main__":
    app.run(debug=True)
