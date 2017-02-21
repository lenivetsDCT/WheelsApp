from flask import Flask, session, redirect, url_for, request, jsonify, send_from_directory
import os.path
import sqlite3
from PIL import Image
from werkzeug import secure_filename
from tempfile import NamedTemporaryFile
import json
from math import ceil

app = Flask(__name__)
s_size = (196, 196)
b_size = (1900, 1600)
app.config['UPLOAD_FOLDER'] = 'C:\\Users\\poar\\Documents\\WheelsApp\\uploads\\'
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg', 'gif'])

if __name__ == '__main__':
    app.secret_key = os.urandom(24)

class ServerError(Exception):pass

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']
           
def get(list, index, default = ''):
    try:
        return list[index]
    except IndexError:
        return default

def query_db(query,args=[],one=True):
    try:
        con = sqlite3.connect("C:\\Users\\poar\\Documents\\WheelsApp\\db.db")
        cur = con.cursor()
        if one:
           res = cur.execute(query, args).fetchone()
        else:
           res = cur.execute(query, args).fetchall()
    except:
        con.rollback()
        return False
    finally:
        con.commit()
        if res is None and one:
           data = cur.lastrowid
        elif res is not None and one:
             data = []
             data.append(dict((cur.description[i][0], value) for i, value in enumerate(res)))
        else:
            data = []
            for row in res:
                data.append(dict((cur.description[i][0], value) for i, value in enumerate(row)))
        cur.close()
        con.close()
        return (data)
           
def save_photo(prfx, file):
    filename = secure_filename(file.filename)
    fname = NamedTemporaryFile(prefix=prfx, suffix=os.path.splitext(filename)[1], dir=os.path.join(app.config['UPLOAD_FOLDER']), delete=False)
    try:
        orig = Image.open(file)
        orig.resize(b_size)
        orig.save(fname.name, 'JPEG', quality=100)
        o_img = fname.name
        img_s = Image.open(fname.name)
        img_s.thumbnail(s_size)
        img_s.save(os.path.splitext(fname.name)[0]+'_s'+os.path.splitext(fname.name)[1], 'JPEG', quality=70)
    except IOError:
        return False
    return os.path.splitext(os.path.basename(o_img))[0]

def img_url(js):
    js = json.loads(js)
    for image in js['data']:
        # try:
            # if image['img_m']: image['img_m'] = '/view?imagekey=%s_s' %(image['img_m'])
        # except KeyError:
            # return None
        if 'img_m' in image.keys(): image['img_m'] = '/view?imagekey=%s_s' %(image['img_m']) if (image['img_m'] is not None) else None
        if 'img1' in image.keys(): image['img1'] = '/view?imagekey=%s' %(image['img1']) if (image['img1'] is not None) else None
        if 'img2' in image.keys(): image['img2'] = '/view?imagekey=%s' %(image['img2']) if (image['img2'] is not None) else None
        if 'img3' in image.keys(): image['img3'] = '/view?imagekey=%s' %(image['img3']) if (image['img3'] is not None) else None
        if 'img4' in image.keys(): image['img4'] = '/view?imagekey=%s' %(image['img4']) if (image['img4'] is not None) else None
        if 'u_img' in image.keys(): image['u_img'] = '/view?imagekey=%s' %(image['u_img']) if (image['u_img'] is not None) else None
        if 'm_img' in image.keys(): image['m_img'] = '/view?imagekey=%s' %(image['m_img']) if (image['m_img'] is not None) else None
        if 'mo_img' in image.keys(): image['mo_img'] = '/view?imagekey=%s' %(image['mo_img']) if (image['mo_img'] is not None) else None
        if 't_img' in image.keys(): image['t_img'] = '/view?imagekey=%s' %(image['t_img']) if (image['t_img'] is not None) else None
        if 'w_img' in image.keys(): image['w_img'] = '/view?imagekey=%s' %(image['w_img']) if (image['w_img'] is not None) else None
    return js

@app.route('/',methods=['GET'])
def get_all_post():
   global pd_all
   arr=[]
   pstr=''
   sz = int(request.args.get('size')) if request.args.get('size') else 10
   pg = int(request.args.get('page')) if request.args.get('page') else 1
   
   if (pg == 1):
      if not request.args:
         pd_all = query_db('SELECT ID, WheelID, TireID, UserID, Description, img_m FROM Post ORDER BY ID desc',[], False)
      else:
         for param in request.args:
            if 'wheelid' in param:
                pstr += ' and WheelID= ?' if len(pstr)>1 else 'SELECT ID, WheelID, TireID, UserID, Description, img_m FROM Post WHERE WheelID= ?'
                arr.append(int(request.args.get('wheelid')))
            if 'tireid' in param:
                pstr += ' and TireID= ?' if len(pstr)>1 else 'SELECT ID, WheelID, TireID, UserID, Description, img_m FROM Post WHERE TireID= ?'
                arr.append(int(request.args.get('tireid')))
         pd_all = query_db(pstr+'ORDER BY ID desc',arr,False) if len(pstr)>1 else None
      if pd_all is None:
        return ("Couldn't receive post's data",500)
      else:
        lns= len(pd_all)
        return jsonify({'page':[{'elements':lns, 't_pages':ceil(lns/sz),'page':1 if pg is None else pg}]}, img_url(json.dumps({'data':pd_all[0:sz]})))
   elif (pg > 1):
      try:
        pd_all
      except NameError:
        return redirect(url_for('get_all_post'))
      else:
        tln =(pg*sz)
        return jsonify({'page':[{'page':pg, 'size':sz}]},img_url(json.dumps({'data':pd_all[tln-sz:tln]})))
   else:
        return ("Use 'size' parameter to change elements per page"+'\n'+"To get page, use 'page' parameter",404)

@app.route('/post/<int:post_id>',methods=['GET'])
def get_post(post_id):
   if not request.args: 
      post = query_db('SELECT * FROM Post WHERE ID= ?',[post_id])
      if post==0:
         return ('Not existing',404)
      else:
         return jsonify(img_url(json.dumps({'data':post})))
   else: 
      for img in request.args:
         if 'img' in img: return ('Please look to received data, just remove "_s" from picture and request it.',403)

@app.route('/wheel',methods=['GET'])
def get_wheels():
   arr = []
   wstr= ''
   
   if not request.args: 
      post = query_db('SELECT * FROM Wheels',[], False)
   else: 
      for param in request.args:
         if 'radius' in param:
            wstr += ' and RADIUS <= ?' if len(wstr)>1 else 'SELECT * FROM Wheels WHERE RADIUS <= ?'
            arr.append(int(request.args.get('radius'))) 
         if 'manufacture' in param:
            wstr += ' and MANUFACTURE LIKE ?' if len(wstr)>1 else 'SELECT * FROM Wheels WHERE MANUFACTURE LIKE ?'
            arr.append('%'+request.args.get('manufacture')+'%')
         if 'model' in param:
            wstr += ' and MODEL LIKE ?' if len(wstr)>1 else 'SELECT * FROM Wheels WHERE MODEL LIKE ?'
            arr.append('%'+request.args.get('model')+'%')  
         if 'width' in param:
            wstr += ' and WIDTH <= ?' if len(wstr)>1 else 'SELECT * FROM Wheels WHERE WIDTH <= ?'
            arr.append(request.args.get('width'))  
         if 'et' in param:
            wstr += ' and ET >= ?' if len(wstr)>1 else 'SELECT * FROM Wheels WHERE ET >= ?'
            arr.append(int(request.args.get('et')))         
      post = query_db(wstr, arr, False) if len(wstr)>0 else None
   if post is None:
      return ('Not existing', 404)
   else:
      return jsonify(img_url(json.dumps({'data':post})))

@app.route('/cars',methods=['GET'])
def get_cars():
   arr = []
   cstr= ''
   
   if not request.args: 
      post = query_db('SELECT * FROM Cars',[], False)
   else: 
      for param in request.args:
         if 'model' in param:
            cstr += ' and MODEL LIKE ?' if len(cstr)>1 else 'SELECT * FROM Cars WHERE MODEL LIKE ?'
            arr.append('%'+request.args.get('model')+'%')  
         if 'country' in param:
            cstr += ' and M_COUNTRY LIKE ?' if len(cstr)>1 else 'SELECT * FROM Cars WHERE M_COUNTRY LIKE ?'
            arr.append('%'+request.args.get('country')+'%')
         if 'make' in param:
            cstr += ' and ( MAKE LIKE ? or m_short LIKE ? )' if len(cstr)>1 else 'SELECT * FROM Cars WHERE ( MAKE LIKE ? or m_short LIKE ? )'
            arr.append('%'+request.args.get('make')+'%')
            arr.append('%'+request.args.get('make')+'%')
         if 'year' in param:
            cstr += ' and YEAR >= ?' if len(cstr)>1 else 'SELECT * FROM Cars WHERE YEAR >= ?'
            arr.append(int(request.args.get('year'))) 
      post = query_db(cstr, arr, False) if len(cstr)>1 else None
   if post is None:
      return ('Not existing', 404)
   else:
      return jsonify(img_url(json.dumps({'data':post})))      

@app.route('/post', methods=['POST'])
def post():
    img_list = []
    desc = request.form.get('desc')
    whid = request.form.get('whid')
    trid = request.form.get('trid')
    usid = request.form.get('user') if request.form.get('user') else 1
    
    for f in request.files:
        file = request.files[f]
        if file and allowed_file(file.filename):
           fname = save_photo('img_',file)
           if fname:
              img_list.append(fname)
           else:
              return ('Could not resize image',500)
        else:
            return ('File not supported',400)
    if whid and trid:
       res = query_db('INSERT INTO Post (WheelID, TireID, UserID, Description, img_m, img1, img2, img3, img4) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                       [whid, trid, usid, desc, get(img_list,0),get(img_list,0),get(img_list,1),get(img_list,2),get(img_list,3)])
       if res > 0:
          return redirect(url_for('get_post',post_id=res), 201)
       else:
          return ('Could not create post',400)
    else:
          return ('Could not create post \nNot enough params',400)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)