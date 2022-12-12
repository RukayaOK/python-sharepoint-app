from flask import Flask
import os
from routes.get import get
from routes.put import put
from routes.patch import patch
from routes.delete import delete


app = Flask(__name__)
app.register_blueprint(get)
app.register_blueprint(put)
app.register_blueprint(patch)
app.register_blueprint(delete)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5010))
    app.run(debug=True, host='0.0.0.0', port=port)
