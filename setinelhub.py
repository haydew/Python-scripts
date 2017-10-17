import sentinelhub
from datetime import datetime, timedelta
import urllib
import gdal
import numpy as np
from numpy import *
import os
import json
import urllib2
import rasterio as rio
from rasterio.warp import calculate_default_transform, reproject

sent2TileList = ['54/H/XF','54/H/XG','55/H/BA','55/H/CV','55/H/BB','55/H/DA','54/H/YE','54/H/YF','54/H/YG','55/H/BV','55/H/CA','55/H/DV'] #list of GMID intersecting Tiles



def reproject(file2, proj):
    input_raster = gdal.Open(file2)
    gdal.Warp(proj,input_raster,dstSRS='EPSG:3111')

def downloadSent(a, b):
    for e in sent2TileList:
        patha='../NDVI/Unprocessed/Sent_B4_'+e.replace("/","_")+'_'+b+'.jp2'
        print patha
        pathb='../NDVI/Unprocessed/Sent_B8_'+e.replace("/","_")+'_'+b+'.jp2'
        urlopnPath ='http://sentinel-s2-l1c.s3.amazonaws.com/tiles/'+e+'/'+a+'/0/tileInfo.json'
        print urlopnPath
        tilejson=urllib2.urlopen(urlopnPath)
        print tilejson
        jdata= json.load(tilejson)
        if os.path.isfile('../NDVI/Unprocessed/Sent_B4_'+e+'_'+b+'.jp2')==True:
            print "Sentinal 2 file exists"
            processNDVI(patha, pathb,b,e)
        elif jdata["cloudyPixelPercentage"] > 60:
            print "Cloud cover is greater than 15%"
            print jdata["cloudyPixelPercentage"]

        else:
            print "downloading "+e+" band 4 and 8 from AWS"
            print '..//NDVI//Unprocessed//Sent_B4_'+e+'_'+b+'.jp2'
            sentinelhub.download_data(('http://sentinel-s2-l1c.s3.amazonaws.com/tiles/'+e+'/'+a+'/0/B04.jp2', '..//NDVI//Unprocessed//Sent_B4_'+e.replace("/","_")+'_'+b.replace("/","_")+'.jp2'))
            sentinelhub.download_data(('http://sentinel-s2-l1c.s3.amazonaws.com/tiles/'+e+'/'+a+'/0/B08.jp2', '..//NDVI//Unprocessed//Sent_B8_'+e.replace("/","_")+'_'+b.replace("/","_")+'.jp2'))

            processNDVI(patha, pathb, b, e)


def processNDVI(b4, b8, b, e):
    if os.path.isfile('../NDVI/Unprocessed/Sent_NDVI_'+e.replace("/","_")+'_'+b.replace("/","_")+'.tif')==True:
        print "NDVI file exists"
    else:
        outfile = r'../NDVI/Unprocessed/Sent_NDVI_'+e.replace("/","_")+'_'+b.replace("/","_")+'.tif'
        print "Processing NDVI"
        with rio.Env(GDAL_SKIP='JP2ECW'):
            with rio.open(b4) as red:
                RED = red.read()
        with rio.open(b8) as nir:
            NIR = nir.read()
        #compute the ndvi
        RED=RED.astype('float')
        NIR-NIR.astype('float')
        ndvi = (NIR-RED)/(NIR+RED)
        ##ndvi = ndvi.astype(rio.float32)
        print "ndvi=",ndvi
        print(ndvi.min(), ndvi.max()) ##The problem is alredy here
        profile = red.meta
        print profile
        profile.update(driver='GTiff')
        profile.update(dtype=rio.float32)
        #print "ndvi after floatupdate=",ndvi.astype(rio.float32)
        with rio.open(outfile, 'w', **profile) as dst:
            dst.write(ndvi)
        print "NDVI Sentinel 2 complete"
        print profile

        projTiff ='../NDVI/Sent_NDVI_'+e.replace("/","_")+'_'+b.replace("/","_")+'.tif'
        reproject(outfile, projTiff)
        dst.closed

pathStatus = False
count = 0

while (pathStatus == False):
    pathYear1 = datetime.now()
    pathYear= pathYear1-timedelta(days=count)
    y1=pathYear.year
    m1=pathYear.month
    d1=pathYear.day
    dateStructure=str(y1)+"/"+str(m1)+"/"+str(d1)
    filedateStructure =str(y1)+""+str(m1)+""+str(d1)
    URLPath="http://sentinel-s2-l1c.s3.amazonaws.com/tiles/55/H/CV/"+dateStructure+"/0/tileInfo.json"

    if urllib.urlopen(URLPath).getcode() == 404:
        count += 1
        pathStatus=False

    elif urllib.urlopen(URLPath).getcode() == 200:
         count += 1
         pathStatus=True
         downloadSent(dateStructure, filedateStructure)
    else:
        downloadSent(dateStructure, filedateStructure)
        pathStatus= True
        break



