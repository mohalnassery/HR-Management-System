fuser -n tcp -k 8000 
source venv/bin/activate
cd hrms_project
python3 manage.py runserver 0.0.0.0:7000