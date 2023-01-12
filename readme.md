InsiliCHO model explorer, with streamlit

### Model
https://github.com/culturerobotics/insilicho


### Cloud
https://culturebio-insilicho.streamlit.app/


### Local Setup

Use py 3.10

```
$ pip install virtualenv
$ python -m venv env
$ source env/bin/activate
$ pip install -r requirements.txt
```


### Local Testing

streamlit model explorer:

```
$ source env/bin/activate
$ streamlit run explore.py
```


### Experimental Data for Plotting

Use a CSV file, with appropriate headers. See `example.csv`
