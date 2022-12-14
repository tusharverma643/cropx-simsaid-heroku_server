from django.shortcuts import render,redirect
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
import pyrebase
import plotly.express as px

# Create your views here.

firebaseConfig = {
  'apiKey' : "AIzaSyC5R0M7_moapH95d2W-eU1Zzg1LnZXPYRw",
  'databaseURL' : "https://cropx-a5a83-default-rtdb.firebaseio.com",
  'authDomain' : "cropx-a5a83.firebaseapp.com",
  'projectId' : "cropx-a5a83",
  'storageBucket' : "cropx-a5a83.appspot.com",
  'messagingSenderId' : "1063284115703",
  'appId' : "1:1063284115703:web:f5d86fd9a81db0a5e56bf2"
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db=firebase.database()


def loginPage(request):

    page = 'login'
    flag=1
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username=request.POST.get('username')
        password=request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request,'User does not exist')
            flag=0

        user = authenticate(request,username=username,password=password)

        if user is not None:
            login(request,user)
            return redirect('home')
        else:
            if flag:
                messages.error(request,'Incorrect Password.')
        
        
    context={'page': page}
    return render(request,'base/login_register.html',context)

def logoutUser(request):
    logout(request)
    return redirect('home')

def registerUser(request):
    form = UserCreationForm()
    context={'form': form}
    if request.method == 'POST':
        username=request.POST['username']
        password=request.POST['password']
        if User.objects.filter(username=username).exists():
            messages.error(request,'User already exists.')
        else:
            user=User.objects.create_user(username=username,password=password)
            user.save()
            login(request,user)
            return redirect('home')
    return render(request,'base/login_register.html',context) 

@login_required(login_url='login')
def userprofile(request):
    kc_value={
        "Broccoli":[0.7,1.05,0.95],
        "Cabbage" :[0.7,1.05,0.95],
        "Carrots" :[0.7,1.05,0.95],
        "Cauliflower" :[0.7,1.05,0.95],
        "Garlic" :[0.7,1.00,0.70],
        "Onion" :[0.7,1.05,0.75],
        "Spinach" :[0.7,1.00,0.95],
        "Radish" :[0.7,0.90,0.85],
        "Tomato" :[0.75,1.15,0.84]
    }
    if request.method == 'POST':
        crop=request.POST.get('crop',None)
        stage=int(request.POST.get('stage',None))
        kc_computed_val=kc_value[crop][stage]
        db.update({"Kc": kc_computed_val})
        db.update({"crop": crop})
        db.update({"stage": stage})

    crop=db.child('crop').get().val()
    if crop=="None":
        kc=-1
        stage="Not selected"
    else:
        kc=db.child('Kc').get().val()
        stage=int(db.child('stage').get().val())
    if stage==0:
        stage="Initial"
    elif stage==1:
        stage="Mid"
    elif stage==2:
        stage="End"
    
    sensorHumidity=db.child('SensorHumidity').get().val()
    # sensorHumidity=round(sensorHumidity.popitem(last=True)[1],3)
    sensorMoistureSoil=db.child('SensorMoistureSoil').get().val()
    # sensorMoistureSoil=round(sensorMoistureSoil.popitem(last=True)[1],3)
    sensorTemperature=db.child('SensorTemperature').get().val()
    # sensorTemperature=round(sensorTemperature.popitem(last=True)[1],3)
    
    sensorHumidityList=[]
    sensorMoistureSoilList=[]
    sensorTemperatureList=[]
    for i in range(10):
        sensorHumidityList.append(round(sensorHumidity.popitem(last=True)[1],3))
        sensorMoistureSoilList.append(round(sensorMoistureSoil.popitem(last=True)[1],3))
        sensorTemperatureList.append(round(sensorTemperature.popitem(last=True)[1],3))

    sensorHumidityList.reverse()
    sensorMoistureSoilList.reverse()
    sensorTemperatureList.reverse()

    sensorHumidityChart=px.line(
        x=[range(len(sensorHumidityList))],
        y=sensorHumidityList,
        template="plotly_dark",
        labels=dict(y="Air Humidity (%)",x="Time (15 min quaters -prior)"),
        
    )
    sensorHumidityChart.layout.update(showlegend=False,xaxis=dict(title='Time (Past 15 min interval)'),yaxis_range=[0,100])
 
    Humidity=sensorHumidityChart.to_html()

    sensorMoistureSoilChart=px.line(
        x=[range(len(sensorMoistureSoilList))],
        y=sensorMoistureSoilList,
        template="plotly_dark",
        labels=dict(y="Soil Moisture (%)",x="Time (15 min quaters -prior)"),
    )
    sensorMoistureSoilChart.layout.update(showlegend=False,xaxis=dict(title='Time ( Past 15 min interval )'))
    soilMoisture=sensorMoistureSoilChart.to_html()

    sensorTemperatureChart=px.line(
        x=[range(len(sensorTemperatureList))],
        y=sensorTemperatureList,
        template="plotly_dark",
        labels=dict(x="Time (15 min quaters)",y="Soil Temperature (??C)"),
    )
    sensorTemperatureChart.layout.update(showlegend=False,xaxis=dict(title='Time (Past 15 min interval )'))
    soilTemperature=sensorTemperatureChart.to_html()
    
    context={
            'crop': crop,   
            'stage': stage,
            'kc': kc,
            'sensorHumidity': Humidity,
            'sensorMoistureSoil': soilMoisture,
            'soilTemperature': soilTemperature,
        }   
    return render(request,'base/profile.html',context)

@login_required(login_url='login')
def home(request):
    mode_curr=db.child('mode').get().val()
    DisplayHumidity=db.child('DisplayHumidity').get().val()
    atmosp=db.child('DisplayPressure').get().val()
    MaxTemp=db.child('DisplayTempMax').get().val()
    # MinTemp=db.child('DisplayTempMin').get().val()
    WindSpeed=db.child('DisplayWindSpeed').get().val()
    Kc=(db.child('Kc').get().val())

    if Kc==-1:
        Kc="Crop Not Selected"

    context={'DisplayHumidity' : DisplayHumidity,
            'atmosp' : atmosp,
            "MaxTemp" : round(MaxTemp,3),
            "WindSpeed" : round(WindSpeed,3),
            "Kc" : Kc,
            "Mode" :mode_curr
    }
    if request.method == 'POST':
        val=request.POST.get('mode',None)
        db.update({"mode": int(val)})
        mode_curr=int(val)

        context={'DisplayHumidity' : DisplayHumidity,
            'atmosp' : atmosp,
            "MaxTemp" : round(MaxTemp,3),
            "WindSpeed" : round(WindSpeed,3),
            "Kc" : Kc,
            "Mode" :mode_curr
    }
       
    return render(request,'base/home.html',context)



