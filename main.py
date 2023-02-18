import os
import uuid
import urllib.request
from forms import SearchForm, PostForm
from flask_bootstrap import Bootstrap4
import openai
from flask import Flask, make_response, escape, session, render_template, request, redirect, url_for
from dotenv import load_dotenv
from flask_ckeditor import CKEditor
from functools import wraps, update_wrapper
from datetime import datetime

load_dotenv()

openai.organization = os.getenv('OPENAI_ORGANIZATION')
openai.api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['CKEDITOR_SERVE_LOCAL'] = True
app.config['CKEDITOR_HEIGHT'] = 400
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = -1
app.config['TEMPLATES_AUTO_RELOAD'] = True
bootstrap = Bootstrap4(app)
ckeditor = CKEditor(app)
img_path= "static/img/"
app_path= "templates/apps/"

def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
        
    return update_wrapper(no_cache, view)

@app.route('/edit/<uuid>', methods=['GET', 'POST'])
@nocache
def index(uuid):
    form = PostForm()
    path =app_path+uuid+'.html'
    if os.path.isfile(path) is True:
      if form.validate_on_submit():
        print('submit:'+form.title.data)
        title = form.title.data
        path =app_path+title+'.html'
        body = form.body.data
        f = open(path, "w+")
        f.write(body)
        f.close()
        return redirect(url_for('generate_app', uuid=title))
      else:
        f = open(path, "r")
        body = f.read()
        f.close()
        form.title.data = uuid
        form.body.data = body
        print(form.body.data)
        return render_template('flask_ckeditor.html', form=form)
    
    return render_template('error.html')

@app.route("/func/create_img", methods = ['GET', 'POST'])
def generate_img():
  form = SearchForm()
  img_name=form.search.data
  response = openai.Image.create(
    prompt="A cartoon "+img_name,
    n=1,
    size="256x256"
  )
  image_url = response['data'][0]['url']
  urllib.request.urlretrieve(image_url, img_path+img_name+".jpg")
  return redirect("/"+img_path+img_name+".jpg")

@app.route("/app/<uuid>", methods = ['GET', 'POST'])
@nocache
def generate_app(uuid):
  print(uuid)
  if 'prompt' in session:
    prompt = 'Tell me the whole code to create a good design website of ' + session['prompt']
    print(prompt)
  path =app_path+uuid+'.html'
  if os.path.isfile(path) is False:
    response = generate_gpt3_response(prompt)
    print(response)
    f = open(path, "w+")
    f.write(response)
    f.close()
  #return response
  return render_template("apps/"+uuid+'.html')

@app.route("/", methods=['GET', 'POST'])
def home():
    form = SearchForm()
    if request.method == 'POST' and form.validate_on_submit():
        session['prompt'] = form.search.data
        return redirect(url_for('generate_app', uuid=str(uuid.uuid4())))
    return render_template('search.html', form=form)

def generate_gpt3_response(user_text, print_output=False):
    """
    Query OpenAI GPT-3 for the specific key and get back a response
    :type user_text: str the user's text to query for
    :type print_output: boolean whether or not to print the raw output JSON
    """
    completions = openai.Completion.create(
        engine='text-davinci-003',  # Determines the quality, speed, and cost.
        temperature=0.5,            # Level of creativity in the response
        prompt=user_text,           # What the user typed in
        max_tokens=4080,             # Maximum tokens in the prompt AND response
        n=2,                        # The number of completions to generate
        stop=None,                  # An optional setting to control response generation
    )

    # Displaying the output can be helpful if things go wrong
    if print_output:
        print(completions)

    # Return the first choice's text
    return completions.choices[0].text

@app.route("/images/list")
@app.route('/images/list/<path:path>')
def list_images(path='.'):
  return render_template('img_autoindex.html', tree=make_tree(request.host_url+img_path, img_path+path))

@app.route("/apps/list")
@app.route('/apps/list/<path:path>')
def list_apps(path='.'):
  return render_template('img_autoindex.html', tree=make_tree(request.host_url+"app/", app_path+path, remove_ext=True, editable=True))

def make_tree(base_url, path, remove_ext=False, editable=False):
    tree = dict(name=os.path.basename(path), children=[])
    try: lst = os.listdir(path)
    except OSError:
        pass #ignore errors
    else:
        for name in lst:
            fn = os.path.join(path, name)
            if os.path.isdir(fn):
                tree['children'].append(make_tree(base_url, fn, remove_ext, editable))
            else:
                href = base_url+name
                editHref = None
                if remove_ext:
                  href = base_url + os.path.splitext(name)[0]
                if editable:
                  editHref = base_url.replace("app/","edit/") + os.path.splitext(name)[0]
                tree['children'].append(dict(name=name, href=href, editHref=editHref))
    return tree

if __name__ == "__main__":
    app.run(debug=True)


