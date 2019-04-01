from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from .forms import PhotoForm, ImageForm, ImageForm2
from .models import Photo
import requests
import base64
import json
 
def upload(request):
    ENDPOINT_URL = 'https://vision.googleapis.com/v1/images:annotate'
    api_key = 'your_api_key'
    
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('app1:upload')
    else:
        form =PhotoForm()
        objects = Photo.objects.all()
        last = objects.last()
    
    #image_files = []     
    #image_requests = []
    
    #image_files.append(last.image.url[1:])
    
    #for file in image_files:
    #    with open(file, 'rb') as f:
    #        content = base64.b64encode(f.read()).decode('UTF-8')
    #        image_requests.append({
    #                'image': {'content': content},
    #                'features': [{
    #                   'type': 'LABEL_DETECTION',
    #                   'maxResults': 5
    #                }]
    #        })
    
    if len(objects) > 0:
        with open(last.image.url[1:], 'rb') as f:
            content = base64.b64encode(f.read()).decode('UTF-8')
            image_requests = {
                    'image': {'content': content},
                    'features': [{
                            'type': 'LABEL_DETECTION',
                            'maxResults': 3
                            }]
                    }
                
        response = requests.post(ENDPOINT_URL,
                                 data=json.dumps({"requests": image_requests}),
                                 params={'key': api_key},
                                 headers={'Content-Type': 'application/json'})
        
        description1 = response.json()['responses'][0]['labelAnnotations'][0]['description']
        score1 = response.json()['responses'][0]['labelAnnotations'][0]['score']
        description2 = response.json()['responses'][0]['labelAnnotations'][1]['description']
        score2 = response.json()['responses'][0]['labelAnnotations'][1]['score']
        description3 = response.json()['responses'][0]['labelAnnotations'][2]['description']
        score3 = response.json()['responses'][0]['labelAnnotations'][2]['score']
        
    else:
        description1 = ''
        score1 = 0
        description2 = ''
        score2 = 0
        description3 = ''
        score3 = 0
                    
    d = {
        'form': form,
        'objects': objects,
        'last': last,
        'description1': description1,
        'score1': '{:.3f}'.format(score1),
        'description2': description2,
        'score2': '{:.3f}'.format(score2),
        'description3': description3,
        'score3': '{:.3f}'.format(score3),
    }
        
    return render(request, 'app1/upload.html', d)

def upload2(request):
    from PIL import Image
    from io import BytesIO
    
    ENDPOINT_URL = 'https://vision.googleapis.com/v1/images:annotate'
    api_key = 'your_api_key'
    
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = request.FILES['image']
            #image = form.cleaned_data['image']
            
            img = Image.open(image)
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
                        
            content = base64.b64encode(buffered.getvalue()).decode('UTF-8')
            image_requests = {
                    'image': {'content': content},
                    'features': [{
                            'type': 'LABEL_DETECTION',
                            'maxResults': 3
                            }]
                    }
                    
            response = requests.post(ENDPOINT_URL,
                                 data=json.dumps({"requests": image_requests}),
                                 params={'key': api_key},
                                 headers={'Content-Type': 'application/json'})
            
            description1 = response.json()['responses'][0]['labelAnnotations'][0]['description']
            score1 = response.json()['responses'][0]['labelAnnotations'][0]['score']
            description2 = response.json()['responses'][0]['labelAnnotations'][1]['description']
            score2 = response.json()['responses'][0]['labelAnnotations'][1]['score']
            description3 = response.json()['responses'][0]['labelAnnotations'][2]['description']
            score3 = response.json()['responses'][0]['labelAnnotations'][2]['score']
            
            d = {
                'description1': description1,
                'score1': '{:.3f}'.format(score1),
                'description2': description2,
                'score2': '{:.3f}'.format(score2),
                'description3': description3,
                'score3': '{:.3f}'.format(score3),
            }
                        
            return render(request, 'app1/label.html', d)
        
    else:
        form = ImageForm()   
                
    d = {
        'form': form,
    }
        
    return render(request, 'app1/upload2.html', d)

def upload3(request):
    import os
    from google.cloud import storage
    from google.cloud import vision
    from google.cloud import translate
    from google.cloud import firestore
    
    # for local
    #key_path = './app1/key/xxx.json'
    #os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
    #CLOUD_STORAGE_BUCKET = 'bucket_name'
    
    # for deploy
    CLOUD_STORAGE_BUCKET = os.environ['CLOUD_STORAGE_BUCKET']
        
    path = 'gs://' + CLOUD_STORAGE_BUCKET + '/'
                    
    if request.method == 'POST':
        form = ImageForm2(request.POST, request.FILES)
        if form.is_valid():
            blob_name = form.cleaned_data['name']
            image = request.FILES['image']
            #image = form.cleaned_data['image']
                                    
            # Cloud Storage            
            client_storage = storage.Client()
            bucket = client_storage.get_bucket(CLOUD_STORAGE_BUCKET)            
            blob = bucket.blob(blob_name)            
            blob.upload_from_string(
                    image.read(),
                    #content_type='image/jpeg',
                    )
            
            # Vision API
            vision_client = vision.ImageAnnotatorClient()
            image = vision.types.Image()
            image.source.image_uri = path + blob_name
            response = vision_client.label_detection(image=image)
            labels = response.label_annotations
                                    
            # Cloud Firestore
            firestore_client = firestore.Client()
            doc_ref = firestore_client.collection('images').document(blob_name)
            
            d1 = labels[0].description
            s1 = labels[0].score
            d2 = labels[1].description
            s2 = labels[1].score
            d3 = labels[2].description
            s3 = labels[2].score
                                   
            doc_ref.set({
                'description1': d1,
                'scale1': s1,
                'description2': d2,
                'scale2': s2,
                'description3': d3,
                'scale3': s3,               
            })
                    
            # Translate API
            translate_client = translate.Client()
            target = 'ja'
            text1 = labels[0].description
            text2 = labels[1].description
            text3 = labels[2].description

            translation = translate_client.translate(
                    text1,
                    target_language=target)
            t1 = translation['translatedText']

            translation = translate_client.translate(
                    text2,
                    target_language=target)
            t2 = translation['translatedText']

            translation = translate_client.translate(
                    text3,
                    target_language=target)
            t3 = translation['translatedText']            
            
            d = {
                    'description1': t1,
                    'score1': '{:.3f}'.format(s1),
                    'description2': t2,
                    'score2': '{:.3f}'.format(s2),
                    'description3': t3,
                    'score3': '{:.3f}'.format(s3),
                }
             
            return render(request, 'app1/label.html', d)
        
    else:
        form = ImageForm2()   
                
    d = {
        'form': form,
    }
        
    return render(request, 'app1/upload3.html', d)
    

def download(request):
    return render(request, 'app1/download.html')
