from cStringIO import StringIO
import bottle
import dropbox
import pystache2
import os.path

app = bottle.Bottle()
APP_KEY = 'lysqbrowfmkpdca'
APP_SECRET = '2jze13nzt7nedll' 
ACCESS_TYPE = 'dropbox' # should be 'dropbox' or 'app_folder' as configured for your app
TOKEN_STORE = {}

def get_session():
    return dropbox.session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)

def get_client(access_token):
    sess = get_session()
    sess.set_token(access_token.key, access_token.secret)
    return dropbox.client.DropboxClient(sess)

@app.route('/')
def redir():
    return bottle.redirect('/login')

@app.route('/login')
def login():
    sess = get_session()
    request_token = sess.obtain_request_token()
    TOKEN_STORE[request_token.key] = request_token

    callback = "http://%s/callback" % (bottle.request.headers['host'])
    url = sess.build_authorize_url(request_token, oauth_callback=callback)
    prompt = """Click <a href="%s">here</a> to link with Dropbox."""
    return prompt % url

@app.route('/callback')
def callback(oauth_token = None):
    oauth_token = bottle.request.query.oauth_token
    request_token_key = oauth_token
    if not request_token_key:
        return "fail"

    sess = get_session()
    request_token = TOKEN_STORE[request_token_key]
    access_token = sess.obtain_access_token(request_token)
    TOKEN_STORE[access_token.key] = access_token
    bottle.response.set_cookie('access_token_key', access_token.key)
    bottle.redirect('/view_files')

@app.route('/view_files')
def view_files():
    access_token_key = bottle.request.get_cookie('access_token_key') 
    access_token = TOKEN_STORE[access_token_key] 
    client = get_client(access_token) 
    context = client.metadata('.') 
    print str(context)
    return pystache2.render_file('viewfiles.mustache', context)

@app.route('/view_files/<path:path>')
def view_files(path = '.'):
    submitted = bottle.request.query.submit
    access_token_key = bottle.request.get_cookie('access_token_key') 
    access_token = TOKEN_STORE[access_token_key] 
    client = get_client(access_token) 
    context = client.metadata(path) 
    context['fpath'] = context['path'].split('/')[-1:]
    print str(context)
    if context['is_dir']:
        return pystache2.render_file('viewfiles.mustache', context)
    f, metadata = client.get_file_and_metadata(path)
    text = f.read()
    context['text'] = text
    if submitted:
        context['submit_message'] = 'Submission successful!'
    else:
        context['submit_message'] = ''
    return pystache2.render_file('read.mustache', context)

@app.post('/submission')
def submission():
    forms = bottle.request.params
    print forms
    access_token_key = bottle.request.get_cookie('access_token_key') 
    access_token = TOKEN_STORE[access_token_key] 
    client = get_client(access_token) 
    str_file = StringIO(forms['submission'])
    print forms['rev']
    client.put_file(forms['filepath'], str_file, overwrite = True)#,parent_rev = forms['rev'])
    bottle.redirect('/view_files/%s?submit=True'%forms['filepath'])

if __name__ == '__main__':
    app.run(host = 'localhost', port = 8080, debug = True)
