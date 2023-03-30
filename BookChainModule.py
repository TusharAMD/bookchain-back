import shortuuid
import rsa
import pymongo
import base64
import requests
import pickle

import pyqrcode
import png
from pyqrcode import QRCode

client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/?retryWrites=true&w=majority")
db = client.sih
coll = db["BookChain"]

def ImageUpload():
    with open("image.png", "rb") as file:
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": "fb13020baf1e55ab0f8abe7be3834531",
            "image": base64.b64encode(file.read()),
        }
        res = requests.post(url, payload)
    return res

class BookChain:
    def __init__(self,book_name,edition,serial_no,isbn,classn,language,image=""):
        self.unique_id = shortuuid.uuid()
        self.serial_no = serial_no
        self.book_name = book_name
        self.edition = edition
        self.isbn = edition
        self.classn = edition
        self.language = edition
        self.current_owner = "tusharvamanamdoskar@gmail.com"
        self.image = image
        self.chain = ["tusharvamanamdoskar@gmail.com"]
    
    def change_owner(self,current_owner):
        self.current_owner = current_owner
        self.chain.append(current_owner)
    
    
'''
b = BookChain("Chemistry","12th")
#print(b)
#print(b.__dict__)
#b.change_owner("Tushar")
#print(b.__dict__)
thebytes = pickle.dumps(b)   ####
#print(type(thebytes))
#temp3 = pickle.loads(thebytes)   ####
#print(temp3)

#x = coll.insert_one({"name":thebytes})
x = coll.find_one()
print(x["name"])
temp3 = pickle.loads(x["name"])
print(temp3.__dict__)
temp3.change_owner("Tushar")
print(temp3.__dict__)
'''


class User:
    def __init__(self,username,email_id,location=""):
        self.email_id = email_id
        self.location = location
        self.publicKey,self.privateKey = rsa.newkeys(1024)
        
'''
def CreateBookEntry(book_name,edition,serial_no):
    bookObj = BookChain(book_name,edition,serial_no)
    toBytes = pickle.dumps(bookObj)
    
    s = bookObj.unique_id
    url = pyqrcode.create(s)
    url.png('image.png', scale = 6)
    qrurl = ImageUpload().json()['data']['url']
    
    coll.insert_one({book_name:toBytes,"unique_id":bookObj.unique_id,"qrurl":qrurl})
'''
def CreateBookEntry(book_name,edition,serial_no,isbn,classn,language,image):

    bookObj = BookChain(book_name=book_name,edition=edition,serial_no=serial_no,isbn=isbn,classn=classn,language=language,image=image)
    toBytes = pickle.dumps(bookObj)
    
    s = bookObj.unique_id
    url = pyqrcode.create(s)
    url.png('image.png', scale = 6)
    qrurl = ImageUpload().json()['data']['url']
    
    coll.insert_one({"book_name":book_name,"book_data":toBytes,"unique_id":bookObj.unique_id,"qrurl":qrurl})
    
    return bookObj.unique_id

def CreateUser(username,email_id,location):
    coll = db["Users"]
    
    userObj = User(username=username,email_id=email_id,location=location)
    toBytes = pickle.dumps(userObj)
    s = userObj.email_id
    url = pyqrcode.create(s)
    url.png('image.png', scale = 6)
    qrurl = ImageUpload().json()['data']['url']
    
    coll.insert_one({"email_id":email_id,"email_data":toBytes,"qrurl":qrurl})
    
    return {}

def getCurrentOwner():
    pass

#CreateBookEntry("Chemistry2","12th",20001)    
    
        

#u = User("tusharvamanamdoskar@gmail.com")
#print(u.publicKey)
#print(u.privateKey)
#temp = u.publicKey.save_pkcs1('PEM')
#print(rsa.PublicKey.load_pkcs1(temp))