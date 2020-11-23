from flask import render_template
import connexion

from os import getenv
import logging

logger = logging.getLogger('__name__')

o3api_listen_ip = getenv('O3API_LISTEN_IP', '127.0.0.1')
o3api_port = getenv('O3API_PORT', 5005)

# Create the application instance
app = connexion.FlaskApp(__name__, specification_dir='./')

# Read the swagger.yml file to configure the endpoints
app.add_api('swagger.yml') #, validate_responses=True)

### handle an exception
## vkoz: does not work??
#from flask import jsonify
#from connexion import ProblemException
#def handle_problem_exception(error):
#    resp = {
#        'error': {
#            'status': error.title,
#            'code': error.status,
#            'message': error.detail,
#        }
#    }
#
#    return jsonify(resp), error.status
#app.add_error_handler(ProblemException, handle_problem_exception)
###

# Create a URL route in our application for "/"
@app.route('/')
def home():
    """This function just responds to the browser URL localhost:5000/
    :return:        the rendered template 'home.html'
    """
    logger.debug("O3API_LISTEN_IP:O3API_PORT = {}:{}".format(o3api_listen_ip, 
                                                     o3api_port))

    return render_template('index.html')

# from app import routes

if __name__ == "__main__":
    app.run(host=o3api_listen_ip,
            port=o3api_port)
