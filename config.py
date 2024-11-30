import os

# For a production app, you should use a secret key set in the environment
# The recommended way to generate a 64char secret key is to run:
# python -c 'import secrets; print(secrets.token_hex())'
SECRET_KEY = os.getenv('SECRET_KEY', 'not-set')
# Define allowed files
ALLOWED_EXTENSIONS = {'csv'}
# When deploying, set in the environment to the PostgreSQL URL
#SQLALCHEMY_DATABASE_URI = os.getenv('LOCAL_DATABASE_URL', 'postgresql://localhost/analysis?user=postgres&password=database1530!')
SQLALCHEMY_DATABASE_URI = os.getenv('LOCAL_DATABASE_URL', 'postgresql://neurosity_db_user:ShGcMbFsX8GUCjEULX9Io0oWNrY32oPy@dpg-ct4t8hpu0jms73aahdvg-a/neurosity_db')
#UPLOAD_FOLDER = os.path.join('staticFiles', 'uploads')
UPLOAD_FOLDER = '/' + s.path.join('var', 'uploads')
