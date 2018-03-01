## pkinoc

```
npm install
http-server -p 8081 .

pip install -r requirements.txt
export PORT=8081
python server.py
```

### Deploy
```
heroku buildpacks:add heroku/python

git push heroku master
```
