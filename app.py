from bottle import route, run
import dropbox

APP_KEY = '0ki30ehnezn1qmz'
APP_SECRET = 'nis7wm8b0kk8djc'
ACCESS_TYPE = 'app_folder' # should be 'dropbox' or 'app_folder' as configured for your app
TOKEN_STORE = {}

def get_session():
    return dropbox.session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)

def get_client(access_token):
    sess = get_session()
    sess.set_token(access_token.key, access_token.secret)
    return dropbox.client.DropboxClient(sess)

@route('/login')
def login(self):
    sess = get_session()
    request_token = sess.obtain_request_token()
    TOKEN_STORE[request_token.key] = request_token

    callback = "http://%s/callback" % (bottle.request.headers['host'])
    url = sess.build_authorize_url(request_token, oauth_callback=callback)
    prompt = """Click <a href="%s">here</a> to link with Dropbox."""
    return prompt % url

@route('/callback')
def callback(self, oauth_token = None):
    request_token_key = oauth_token
    if not request_token_key:
        return "fail"

    sess = get_session()
    request_token = TOKEN_STORE[request_token_key]
    access_token = sess.obtain_acess_token(request_token)

    bottle.response.set_cookie('access_token_key', acess_token.key)
    return "hi!"
