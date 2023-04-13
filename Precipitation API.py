#Import all neccessary features to code.
from time import sleep
import RPi.GPIO as GPIO
import requests
import json
import datetime as dt
import math
def Setup():
    #checks if errors happens
    try:
        #store client values
        postcode = input("Enter postcode:")
        #used to test postcode works any issues will throw KeyError
        resp=request(postcode)
        #store client values
        #any issues with users entering non numericals values will throw a ValueError
        roofL = float(input("Enter roof length:"))
        roofW = float(input("Enter roof width:"))

        print("_________________")
        print(f"Postcode: {postcode}")
        print(f"Roof length: {roofL}")
        print(f"Roof width: {roofW}")
        print("_________________")
        #creates a dictionary of user values 
        userValues = {
            "working": True,
            "postcode": postcode,
            "roofL": roofL,
            "roofW": roofW,
        }
        return userValues
    #exceptions
    except KeyError:
        print("Postcode Invalid")
         
    except ValueError:
        print("Measurements were not numerical")
        
    #spare exception incase it isnt contained
    except:
        print("Error: Please try again")
        
    return False  #returns an error because an error occured


    #If code is stopped while the solenoid is active it stays active
    #This may produce a warning if the code is restarted and it finds the GPIO Pin, which it defines as non-active in next line, is still active
    #from previous time the code was run. This line prevents that warning syntax popping up which if it did would stop the code running.
    GPIO.setwarnings(False)
    #This means we will refer to the GPIO pins
    #by the number directly after the word GPIO. A good Pin Out Resource can be found here https://pinout.xyz/
    GPIO.setmode(GPIO.BCM)
    #This sets up the GPIO 18 pin as an output pin
    GPIO.setup(18, GPIO.OUT)

def request(postcode):
    #url
    url1 = "http://api.worldweatheronline.com/premium/v1/weather.ashx?key=#########"
    url2 ="&format=JSON"
    #get request
    resp = requests.get(url1+postcode+url2)
    #handling get request response
    resp = json.loads(resp.text)
    data = resp["data"]
    current_conditions=data["current_condition"]
    current_conditions=current_conditions[0]
    precipMM=current_conditions["precipMM"]
    #print precipitation
    
    return float(precipMM)
    
def calc(filled,precipMM,userValues):
    #constants
    CROSS_SECTIONAL_AREA=0.27
    CO_EFFICIENT_DISCHARGE=0.61
    AREA_OF_VALVE=0.003318
    GRAVITY=9.81
    MAXIMUM_HEIGHT=1
    MINIMUM_HEIGHT=0.1
    #calculates water intake
    waterIntake =precipMM/1000*userValues["roofL"]*userValues["roofW"]
    print(f"Current Water intake per hour: {waterIntake}")
    
    #updates how filled the container is
    filled+=(waterIntake/(500/1000))
    currentHeight=MAXIMUM_HEIGHT*filled
    
    #minutes till 10% =(2* cross-sectional area)/co-efficient discharge*area of valve*sqrt(2g)*sqrt(start-end height)
    if ((filled-MINIMUM_HEIGHT)>0):#this check prevents math error with negative sqrts
        drainDuration = (2*CROSS_SECTIONAL_AREA)/(CO_EFFICIENT_DISCHARGE*AREA_OF_VALVE*math.sqrt(2*GRAVITY))*(math.sqrt(filled)-math.sqrt(MINIMUM_HEIGHT))
        print(drainDuration)
        drainDuration=drainDuration*60
        return (filled,drainDuration)
    else:#this is should be only used when checking how filled it is
        return(filled,0.0)
    

    
###initialising###

filled=0.0
precipMM=0
response="n"
#If code is stopped while the solenoid is active it stays active
#This may produce a warning if the code is restarted and it finds the GPIO Pin, which it defines as non-active in next line, is still active
#from previous time the code was run. This line prevents that warning syntax popping up which if it did would stop the code running.
GPIO.setwarnings(False)
#This means we will refer to the GPIO pins
#by the number directly after the word GPIO. A good Pin Out Resource can be found here https://pinout.xyz/
GPIO.setmode(GPIO.BCM)
#This sets up the GPIO 18 pin as an output pin
GPIO.setup(18, GPIO.OUT)
#array and counter for last 3 hours
recentPrecip = [0, 0, 0]
counter=0
totalPrecip=0
#setup loop if values not correct
while (response=="n") or (response=="no"):
    #setup outputs a boolean of false if there is a error
    try:
        userValues=Setup()
        if userValues["working"]:
            response =input("Are these values correct? (y/n)")   
    except:
        print("-----TRY AGAIN-----")


###main section###


#forever loop
while True:
    #counter loops for each element of array
    if counter>2:
        counter=0
    #takes start time
    hr=dt.datetime.now().hour
    totalPrecip-=recentPrecip[counter]
    #request precipitation pushed to array
    precipMM=request(userValues["postcode"])
    print(f"Current precipitation:{precipMM}")
    
    recentPrecip[counter]=precipMM
    totalPrecip=totalPrecip+precipMM
    filled=calc(filled,precipMM,userValues)[0]
    
    #if rainfall small and more than 10% filled or filled >90%
    if ((totalPrecip>1.5 and filled>10) or filled>90):
        drainDuration =filled(filled,precipMM,userValues)[1]
        #open
        print("Solenoid valve opened")
        GPIO.output(18, 1)
        sleep(drainDuration)
        #close
        GPIO.output(18, 0)
        filled=0.1
        print("Solenoid valve closed")
    else:
        GPIO.output(18, 0)
        print("Solenoid valve closed")
    
    #counter incremented
    counter+=1
    print("Weather updated")
    print("waiting..")
    #while the hour is not new, do nothing
    sleep(15*60)
    while hr == dt.datetime.now().hour:
        response=True
        
