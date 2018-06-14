import boto3
import os
import json
from flask import Flask
from flask import render_template, request, flash
from media.s3_storage import S3MediaStorage
from media.name_generator import generate_name 
app = Flask(__name__)

s3 = boto3.resource('s3')
media_storage = S3MediaStorage(s3, os.getenv('APP_BUCKET_NAME'))

photos_list = []
sqs = boto3.resource('sqs', region_name="eu-central-1")
requestQueue = sqs.get_queue_by_name(
  QueueName=os.getenv("APP_QUEUE_NAME")
)

@app.route("/")
def hello():
    return render_template(
      'upload_files.html'
    )

@app.route("/upload", methods=['POST'])
def handle_upload():
  if 'uploaded_file' not in request.files:
    flash('No file part')
    return redirect(request.url)
  
  uploaded_file = request.files['uploaded_file']
  destination_name = generate_name(uploaded_file.filename)
  media_storage.store(
     dest=destination_name,
     source=uploaded_file
  )
  
  photos_list.append(destination_name)

  return "OK" 
@app.route("/proceed", methods=["POST"])
def proceed_animation():
  ani_request = {
    "email": request.form['email'],
    "photos": photos_list
  }

  requestQueue.send_message(
    MessageBody=json.dumps(ani_request)
  )
  return "OK"
  
  
@app.route("/prepare")
def prepare():
  return render_template(
    'prepare.html',
    invitation="the only limit is yourself",
    photos=photos_list 
  )

if __name__ == '__main__':
  app.run(host="0.0.0.0", port=8080, debug=True)
