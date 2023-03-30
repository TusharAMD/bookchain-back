from subprocess import STDOUT, check_call
import os
check_call(['apt-get', 'install', '-y', 'libzbar0'], stdout=open(os.devnull,'wb'), stderr=STDOUT) 

import BookChainModule
from flask import Flask,request
from flask_cors import CORS, cross_origin
import os
import base64
import requests
import json
import pymongo
#Firebase
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import cv2
import numpy as np
from PIL import Image
from pyzbar.pyzbar import ZBarSymbol
from pyzbar.pyzbar import decode
import pickle
import PyPDF2
import datetime



#Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
##

app = Flask(__name__)
cors = CORS(app)

def ImageUpload(Ifilename):
    with open(Ifilename, "rb") as file:
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": "fb13020baf1e55ab0f8abe7be3834531",
            "image": base64.b64encode(file.read()),
        }
        res = requests.post(url, payload)
    return res

@app.route('/api/blockchain/createbook',methods=["POST","GET"])
@cross_origin()
def bookentry():
    ## Database
    client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/?retryWrites=true&w=majority")
    db = client.sih
    coll = db["BookChain"]
    ###
    res = request
    bookImage = res.files['file']
    Ifilename = "image.png"
    bookImage.save(Ifilename)
    image = ImageUpload(Ifilename).json()['data']['url']
    print(image)
    resp = json.loads(res.files['content'].stream.read().decode('UTF-8'))
    uploadedId = BookChainModule.CreateBookEntry(book_name=resp["book_name"],edition=resp["edition"],serial_no=resp["serial_no"],isbn=resp["isbn"],classn=resp["classn"],language=resp["lang"],image=image)
    x = coll.find_one({"unique_id":uploadedId})
    print(x["qrurl"])
    print(uploadedId)
    return {"uploadedId":uploadedId,"qrcodeurl":x["qrurl"]}

@app.route('/api/blockchain/adduser',methods=["POST","GET"])
@cross_origin()
def adduser():
    ## Database
    client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/?retryWrites=true&w=majority")
    db = client.sih
    coll = db["Users"]
    ###
    
    res = request.json
    BookChainModule.CreateUser(res["username"],res["email"],res["location"])
    
    return {}

@app.route('/api/blockchain/getprofile',methods=["POST","GET"])
@cross_origin()
def getprofile():
    ## Database
    client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/?retryWrites=true&w=majority")
    db = client.sih
    coll = db["Users"]
    ###
    x = coll.find_one({"email_id":request.json["email"]})
    print(x["qrurl"])
    #print(request.json)
    return {"qrurl":x["qrurl"]}

@app.route('/api/blockchain/purchaserequest',methods=["POST","GET"])
@cross_origin()
def purchaserequest():
    ## Database
    client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/?retryWrites=true&w=majority")
    db = client.sih
    collUsers = db["Users"]
    collBooks = db["BookChain"]
    ###
    
    if request.method=="POST":
        print(request.files)
        bookQR = request.files["file1"]
        shopQR = request.files["file2"]
        
        
        ####Book QR Decode
        Ifilename = request.files["file1"].name+".jpg"
        request.files["file1"].save(Ifilename)
        bookdecodedQR = (decode(Image.open(Ifilename))[0].data).decode('utf-8')
        print(bookdecodedQR)
        ####
        
        ####Shop QR Decode
        Ifilename = request.files["file2"].name+".jpg"
        request.files["file2"].save(Ifilename)
        shopdecodedQR = (decode(Image.open(Ifilename))[0].data).decode('utf-8')
        print(shopdecodedQR)
        ####
        
        ### Check Book ###
        x = collBooks.find_one({"unique_id":bookdecodedQR})
        x1 = x["book_name"]
        unpickleddata = pickle.loads(x["book_data"])
        #print(unpickleddata.current_owner)
        ########
        
        ### Check Shop ###
        x = collUsers.find_one({"email_id":shopdecodedQR})
        unpickleddataShop = pickle.loads(x["email_data"])
        #print(unpickleddata.current_owner)
        ########
        
        #Firebase Working
        dbFire = firestore.client()
        userrequests = dbFire.collection(u'userrequests').get()
        #print(status[0].to_dict())

        
        
        if unpickleddata.current_owner!=shopdecodedQR:
            return {"data":"QR does not match"}
        else:
            print(unpickleddata)
            print(unpickleddata.book_name)

            '''
            res = collection.document(shopdecodedQR).set({
                "book_name":f"{}",
                "buyer_email":"",
                "createdAt":""
            })'''
            db = client.sih
            collTrans = db["Transfer"]
            buyer_email = json.loads(request.files['content'].stream.read().decode('UTF-8'))

            collTrans.insert_one({
                "book_name":f"{x1}",
                "buyer_email":f"{buyer_email['buyer_email']}",
                "shop_email":unpickleddata.current_owner,
                "createdAt":datetime.datetime.now()
            })
            
            return {"data":"Successful"}
            
        
        '''
        toBytes = pickle.dumps(unpickleddata)
        s = unpickleddata.unique_id
        collBooks.update_one({"unique_id":unpickleddata.unique_id},{"$set":{"book_data":toBytes}})
        '''
        #### ####

        
        return {}
    return {}

@app.route('/api/blockchain/transferrequest',methods=["POST","GET"])
@cross_origin()
def transferrequest():
    if request.method=="POST":
        req = request.json
        print(req)
        client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/?retryWrites=true&w=majority")
        db = client.sih
        collTrans = db["Transfer"]

        results = collTrans.find()
        li = []
        for ele in results:
            #print(ele["buyer_email"], req["email"])
            if ele["shop_email"] == req["email"]:
                print(ele)
                del ele["_id"]
                li.append(ele)

    return {"data":li}


@app.route('/api/blockchain/transferrequestapprove',methods=["POST","GET"])
@cross_origin()
def transferrequestapprove():
    if request.method=="POST":
        req = request.json
        print(req)
        client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/?retryWrites=true&w=majority")
        db = client.sih
        collBook = db["BookChain"]

        results = collBook.find_one({"book_name":req["buyer"]["book_name"]})
        unpickleddata = pickle.loads(results["book_data"])
        unpickleddata.chain.append(req["buyer"]["buyer_email"])
        toBytes = pickle.dumps(unpickleddata)
        collBook.update_one({"book_name":req["buyer"]["book_name"]},{ "$set": { "book_data": toBytes }})


        results = collBook.find_one({"book_name":req["buyer"]["book_name"]})
        unpickleddata = pickle.loads(results["book_data"])
        print(unpickleddata.__dict__)

        #Removing
        collTrans = db["Transfer"]
        collTrans.delete_one({"book_name":req["buyer"]["book_name"], "buyer_email":req["buyer"]["buyer_email"]})


        li = []



    return {"data":li}

@app.route('/api/blockchain/addbookdata',methods=["POST","GET"])
@cross_origin()
def addbookdata():
    if request.method=="POST":

        #print(request.files['file'])
        #print(json.loads(request.files['content'].stream.read().decode('UTF-8')))
        jsonRes = json.loads(request.files['content'].stream.read().decode('UTF-8'))
        
        request.files['file'].save(request.files['file'].filename)
        pdf_file = open(request.files['file'].filename, 'rb')
        pdf_reader = PyPDF2.PdfFileReader(pdf_file)
        page_count = pdf_reader.numPages
        
        ### Store in firestore ###
        
        db = firestore.client()  # this connects to our Firestore database
        collection = db.collection('AllBooks')  # opens collection
        doc = collection.document(request.files['file'].filename)  # specifies the document
        
        res = collection.document(jsonRes['bookname']).set({
            "classn":jsonRes['classn'],
            "bookname":jsonRes['bookname'],
            "edition":jsonRes['edition'],
            "isbn":jsonRes['isbn'],
            "coverpage":jsonRes['coverpage'],
            "text_data": {
            
            }
        })
        ####*******************###
        
        dictdata = {}
        for page in range(page_count):
            page_obj = pdf_reader.getPage(page)
            text = page_obj.extractText()
            dictdata[f"page{page+1}"] = text
        #print(dictdata)
        
        res = collection.document(jsonRes['bookname']).update({
            'text_data': dictdata
        })
            
    return {}

@app.route('/api/blockchain/checkchain',methods=["POST","GET"])
@cross_origin()
def checkchain():
    if request.method == "POST":
        print(request.files)

        ### Mongo Setup ###
        client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/?retryWrites=true&w=majority")
        db = client.sih
        collBooks = db["BookChain"]
        ###

        ### Book QR ###
        Ifilename = request.files["file1"].name+".jpg"
        request.files["file1"].save(Ifilename)
        bookdecodedQR = (decode(Image.open(Ifilename))[0].data).decode('utf-8')
        #print(bookdecodedQR)
        ###

        book_data = collBooks.find_one({"unique_id":bookdecodedQR})["book_data"]
        unpickleddata = pickle.loads(book_data)
        print(unpickleddata.chain)

    return {"chain":unpickleddata.chain}


if __name__=="__main__":
    app.run(debug=True)
    
    
##https://towardsdatascience.com/nosql-on-the-cloud-with-python-55a1383752fc