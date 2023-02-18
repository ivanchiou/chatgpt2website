from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditorField

class SearchForm(FlaskForm):
  search = StringField('What you want to create:', [DataRequired()], render_kw={'size': '100', 'placeholder': 'greedy snake game'})
  submit = SubmitField('Generate Website',
                       render_kw={'style': 'margin-top:10px', 'class': 'btn btn-success btn-block'})
  create_img = SubmitField('Create Image',
                       render_kw={'style': 'margin-top:10px', 'class': 'btn btn-success btn-block'})

class PostForm(FlaskForm):
    title = StringField('Title')
    body = CKEditorField('Body', validators=[DataRequired()])
    submit = SubmitField('Submit')