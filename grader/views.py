import os 
import requests
from datetime import timedelta, datetime
from typing import Union 
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse 
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.utils import timezone 
from django.utils.datastructures import MultiValueDictKeyError
from django.core.exceptions import ObjectDoesNotExist

from .models import * 


# Create your views here.

def login(request: HttpRequest): 
    """ 
    When the app extension is first opened, this view should be called. 

    **Context:**
    
    If new user, redirects the user to initiate Onshape's OAuth authorization. Once authenticated, the user will be redirected back to :view:`grader.views.authorize`.  
    
    - A new :model:`grader.AuthUser` model will be created for the new user with the user's ``os_user_id``. 
    
    - If the user already exists, new Onshape working environment IDs will be recorded. 
    
    """
    if request.GET.get("wvm") != 'w': 
        return HttpResponse("Please relaunch this app in the main workspace or create a branch from the left panel to start modelling ...")

    user_id = request.GET.get('userId')
    try: 
        user = AuthUser.objects.get(os_user_id=user_id)
        # Refresh token if needed 
        if user.expires_at < timezone.now() + timedelta(hours=1): 
            user.refresh_oauth_token() 
    except ObjectDoesNotExist: 
        # Create a new user 
        user = AuthUser(os_user_id=user_id)
    
    user.os_domain = request.GET.get('server')
    user.did = request.GET.get('did')
    user.wid = request.GET.get('wvmid')
    user.eid = request.GET.get('eid')
    user.etype = request.GET.get('etype')
    user.save() 
    

    return redirect(
        os.path.join(
            os.environ['OAUTH_URL'], 
            "oauth/authorize"
        ) + "?response_type=code&client_id={}".format(
            os.environ['OAUTH_CLIENT_ID'].replace('=', '%3D')
        )
    )

def authorize(request: HttpRequest): 
    """ 
    When the user authorizes the OAuth integration, Onshape's OAuth authorization page will redirect the user to this page, as registered as the redirect URL. 
    
    Once all necessary registration of the returned tokens is done by the app, the user will be redirected to :view:`grader.views.index`. 
    """
    try: 
        auth_code = request.GET.get('code')
    except MultiValueDictKeyError: 
        return HttpResponse(
            "User authentication failed!\nError: " + str(
                request.GET.get('error')
            )
        )
    
    # Use the authorization code to get access token and refresh token 
    token_response = requests.post(
        os.path.join(
            os.environ['OAUTH_URL'], 
            "oauth/token"
        ) + "?grant_type=authorization_code&code={}&client_id={}&client_secret={}".format(
            auth_code.replace('=', '%3D'), 
            os.environ['OAUTH_CLIENT_ID'].replace('=', '%3D'), 
            os.environ['OAUTH_CLIENT_SECRET'].replace('=', '%3D')
        ), 
        headers={'Content-Type': "application/x-www-form-urlencoded"}
    ).json() 
    
    # Use the sessioninfo API request to get the user's info 
    # for backend data storage 
    sess_response = requests.get(
        "https://cad.onshape.com/api/users/sessioninfo", 
        headers={"Authorization": "Bearer " + token_response['access_token']}
    ).json() 

    user = AuthUser.objects.get(os_user_id=sess_response['id'])
    user.access_token = token_response['access_token']
    user.refresh_token = token_response['refresh_token']
    user.expires_at = timezone.now() + timedelta(seconds=token_response['expires_in'])
    user.save() 

    return HttpResponseRedirect(reverse("grader:index", args=[user.os_user_id]))


def index(request: HttpRequest, os_user_id: str): 
    """ 
    The index view of the app. 
    
    **Context:**
    
    **Arguments:**
    
    - ``os_user_id``: identify the :model:`grader.AuthUser` model with the user's login information and reviewer status. 
    
    **Template:**
    
    :template:`grader/index.html`
    """
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    context = {"user": curr_user}
    return render(request, "grader/index.html", context=context)


def grader(request: HttpRequest, os_user_id: str, mass_props=None):
    """ 
    The auto grader page for checking a model's mass properties and time completion, will potentially be renamed SciOly. 

    **Arguments:**
        
    - ``os_user_id``: identify the :model:`grader.AuthUser` model with the user's login information.

    **Template:**

    :template:`grader/grader.html`
    """
    context = {"user": None,
               "time": None} 
    if os_user_id: 
        curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
        context['user'] = curr_user
    if mass_props:
        context['mass_props'] = mass_props
    return render(request, "grader/grader.html", context=context)


def generic_grader(request: HttpRequest, os_user_id: str, mass_props=None):
    """ 
    The auto grader page for checking a model's mass properties and time completion. This will be used by all users.

    **Arguments:**
        
    - ``os_user_id``: identify the :model:`grader.AuthUser` model with the user's login information.

    **Template:**

    :template:`grader/generic_grader.html`
    """
    context = {"user": None,
               "time": None} 
    
    if os_user_id: 
        curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
        context={
        "user": curr_user, 
        "urlgradetab" : True #to enable url text input
        }
    if mass_props:
        context['mass_props'] = mass_props
    return render(request, "grader/generic_grader.html", context=context)


def grade_model(request: HttpRequest, os_user_id: str): 
    """ 
    When a user submits, model properties are compared from the currently opened element or answer key (called user_props) 
    to the selected elements or input urls (called all_ref_props)
    
    **Context:**
    
    View to get time to completion and mass props compared to reference model
    
    **Arguments:**
    
    - ``os_user_id``: the unique ID linked to the user's :model:`grader.AuthUser` profile
    - ``ref_urls``: the reference element for the model to be compared to
    
    **Template:**
    
    :template:`grader/results.html`
    """
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)

    #grab reference urls , possibly in a csv format, from the generic_grader.html
    cs_ref_urls = request.GET.getlist('ref_url')

    #parse the csv file into array of urls
    ref_urls = convert_cs_to_array(cs_ref_urls) 

    if(ref_urls ==['']): #check blank url field
        context={ 
        "user": curr_user, 
        "urlgradetab": True,
        "error_message": "URL not detected. Please copy and paste a valid Onshape URL and try again",
        }
        return render(request, "grader/generic_grader.html",context=context )

    # Refresh token if needed 
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 
    
    # Get mass props of model the user currently has opened
    mass_props = get_mass_props(
            curr_user.os_domain, curr_user.did, "w", curr_user.wid, curr_user.eid, curr_user.etype, 
            massAsGroup=False, auth_token=curr_user.access_token
        )
    
    # Eliminate massless bodies from mass_props
    heavy_bodies = {}

    for key, value in mass_props['bodies'].items():
        if mass_props['bodies'][key]['hasMass']:
            heavy_bodies[key] = value  

    mass_props['bodies'] = heavy_bodies

    if not mass_props: # API error 
        return HttpResponse("An unexpected error has occurred. Please check internet connection and try relaunching the app.")

    # Set list of user_props - different for each etype
    try:
        user_url = {'did' : curr_user.did, 'wid' : curr_user.wid, 'eid' : curr_user.eid}
        user_props = make_props(curr_user, user_url, mass_props) 

        # Can we do precision in JS?
        # TO FIX : check the user's configuration for precision and units
        # Make rounding off based on the user's settings
        # for i, prop in enumerate(user_props):
        #     if prop < 0.1 or prop > 99: 
        #         user_props[i] = '{:.6f}'.format(user_props[i])
        #     else: 
        #         user_props[i] = round(user_props[i], 3)
        #     pass

    except:
        raise #user_props = None

    # Get info about the document the user currently has opened
    # DO WE NEED THIS?
    user_doc_info = get_doc_info(curr_user.os_domain, curr_user.did, auth_token=curr_user.access_token)
    user_doc_name = user_doc_info['name']
    user_user_name = user_doc_info["createdBy"]["name"]
    user_doc_time = elapsed_time(user_doc_info['defaultWorkspace']['createdAt'],user_doc_info['defaultWorkspace']['modifiedAt'])

    # Append user related information along with mass properties
    # DO WE NEED THIS?
    user_props.insert(0, [user_doc_name, user_user_name, user_doc_time])

    ## Initialize arrays for ref docs
    all_ref_props = [] # 3D array - each 2D array corresponds to one URL
    # First element of each 2D array is an array of doc info [user_name, doc_name, element_name, doc_time, image, url]
    # Rest is model props [[mass, vol, periphery, principalInertia, partName],[...]] (without partName for assemblies)
    failed_urls = [] # Array of all URLs that we failed to get info from
    # Get info and mass props for all url's in ref doc list
    for i, url in enumerate(ref_urls): 
        ref_url = get_ref_url_ids(url)

        try:         
            # ref_props=[] # initialize empty array of ref props

            mass_props = get_mass_props(
                curr_user.os_domain, ref_url['did'], "w", ref_url['wid'], ref_url['eid'], curr_user.etype, 
                massAsGroup=False, auth_token=curr_user.access_token
            )
            ref_props = make_props(curr_user, ref_url, mass_props)
            
            # Can we do precision in JS?
            # for i, prop in enumerate(ref_props):
            #     if prop < 0.1 or prop > 99: 
            #         ref_props[i] = '{:.6f}'.format(ref_props[i])
            #     else: 
            #         ref_props[i] = round(ref_props[i], 3)
            #     pass

            # Get all additional info from the reference document
            image = get_shaded_views(curr_user.os_domain, ref_url['did'],ref_url['wid'], ref_url['eid'], curr_user.etype, auth_token=curr_user.access_token)

            element_info = get_element_info(curr_user.os_domain ,ref_url['did'],ref_url['wid'], ref_url['eid'], auth_token=curr_user.access_token)
            element_name = element_info[0]["name"]
            
            ref_doc_info = get_doc_info(curr_user.os_domain, ref_url['did'], auth_token=curr_user.access_token)
            user_name=ref_doc_info["createdBy"]["name"]
            doc_name = ref_doc_info['name']
            doc_time = elapsed_time(ref_doc_info['defaultWorkspace']['createdAt'],ref_doc_info['defaultWorkspace']['modifiedAt'])

            # Insert first element of array 
            ref_props.insert(0,[user_name, doc_name, element_name, doc_time, image, url])

            all_ref_props.append((ref_props))
        except:
            # If anything above failed, add url to the fairled URL list
            failed_urls.append(url)
    
    if len(failed_urls) == 0:
        failed_urls = None

    context={
        "user": curr_user, 
        "etype": curr_user.etype,
        "failed_urls": failed_urls,
        "user_props": user_props,
        "all_ref_props": all_ref_props
    }
    return render(
        request, "grader/basic_results.html", 
        context=context
    )

def listdocs(request: HttpRequest, os_user_id: str, did:str, wid:str): 
    """ 
    This function loads the list of document created, opened or shared by/with the users
    
    **Context:**
    
    
    **Arguments:**
    
    - ``os_user_id``: the unique ID linked to the user's :model:`grader.AuthUser` profile
    
    **Template:**
    
    :template:`grader/generic_grader.html`
    """
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 

    created_doc_info=[] # arry to store list of documents created by users
    shared_doc_info=[] #arry to store list of documents shared with users
    opened_doc_info=[] #arry to store list of documents opened by users
    #get all documents in the user's recently opened list (perpahps 20? )
    docsinfo=get_user_doc_list(curr_user.os_domain,auth_token=curr_user.access_token) 
    items=docsinfo["items"]

    try:
        for item in items:
            userID=item["createdBy"]["id"]
            documentName=item["name"]
            documentID=item["id"]
            workspaceID=item["defaultWorkspace"]["id"]
            

            if(userID==os_user_id):
                created_doc_info.append((documentName,documentID,workspaceID))
            else:
                shared_doc_info.append((documentName,documentID,workspaceID))


    except:
        print("ERROR on main TRY") #need better error message here

    if (did=="None" and wid=="None"):
        did=curr_user.did
        wid=curr_user.wid

    elements_info=get_elements_info(curr_user.os_domain,did,wid ,auth_token=curr_user.access_token) 

    try:
        element=[]
        eType_present=False #check if the element type is present
        #grab elements and their information from all the tabs in the document
        for eInfo in elements_info:
            image=""
            eType=eInfo["elementType"]
            if eType == "PARTSTUDIO":
                eType = "partstudios"
            elif eType == "ASSEMBLY":
                eType = "assemblies"
            eName=eInfo["name"]
            eid=eInfo["id"]

            if(eType == curr_user.etype):
                eType_present=True  # indicate the etype is present
                image=get_shaded_views(curr_user.os_domain, did,wid,eid, eType, auth_token=curr_user.access_token)
                element.append((eType,eName,image,did,wid,eid))
    except:
        print("ERROR")
    
    if not eType_present:
        element.append((curr_user.etype,eName,eid,image))

    context={
            "user": curr_user, 
            "created_docs":created_doc_info,
            "shared_docs":shared_doc_info,
            "elements":element,
            "doclisttab" :True # to enable the doc list tab 

        }
    return render(
        request, "grader/generic_grader.html",  
        context=context    )  



def enable_csv(request: HttpRequest, os_user_id: str): 

    """ 
    Detects the click of upload csv button show the upload csv tab
 
    
    **Arguments:**
    - ``os_user_id``: the unique ID linked to the user's :model:`grader.AuthUser` profile
    **Template:**
    :template:`grader/generic_grader.html`
    """
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 
    context={
        "user": curr_user, 
        "uploadtab":True #upload csv tab enabled
        }

    return render(
        request, "grader/generic_grader.html",  
        context=context
    )

def upload_csv(request: HttpRequest, os_user_id: str): 

    # TO FIX: embedd csv upload on URL field tab. 
    """ 
    Funtion to upload csv file containing urls for grading. reads and returns the comma separated list of urls to the url grade tab
    
    **Arguments:**
    
    - ``os_user_id``: the unique ID linked to the user's :model:`grader.AuthUser` profile
    
    **Template:**
    
    :template:`grader/generic_grader.html`
    """

    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 

    csvfile = request.FILES["csvfile"]
    cs_ref_urls=csvfile.read().decode("utf-8")
    context={ 
        "user": curr_user, 
        "ref_urls" : cs_ref_urls,
        "urlgradetab" : True  # enable the url grade tab
        }

    return render(
        request, "grader/generic_grader.html", 
        context=context    )  


#################### Helper API calls ####################

def get_mass_props(
    domain: str, did: str, wvm: str, wvmid: str, eid: str, etype: str, auth_token: str, massAsGroup=True
) -> Any: 
    """ Get the mass and geometry properties of the given element 
    """
    response = requests.get(
        os.path.join(
            domain, "api/{}/d/{}/{}/{}/e/{}/massproperties".format(etype, did, wvm, wvmid, eid)
        ), 
        headers={
            "Content-Type": "application/json", 
            "Accept": "application/vnd.onshape.v2+json;charset=UTF-8;qs=0.09", 
            "Authorization" : "Bearer " + auth_token
        }, 
        params={
            "massAsGroup": massAsGroup
        }
    )
    if response.ok: 
        return response.json() 
    else: 
        return None

def get_part_list(
    domain: str, did: str, wvm: str, wvmid: str, eid: str, auth_token: str
) -> Any: 
    """ Get all parts in an element
    """
    response = requests.get(
        os.path.join(
            domain, "api/parts/d/{}/{}/{}/e/{}".format(did, wvm, wvmid, eid)
        ), 
        headers={
            "Content-Type": "application/json", 
            "Accept": "application/vnd.onshape.v2+json;charset=UTF-8;qs=0.09", 
            "Authorization" : "Bearer " + auth_token
        }
    )
    if response.ok: 
        return response.json() 
    else: 
        return None

def get_elements_info(
    domain: str, did: str, wid: str, auth_token: str
) -> Any: 
    """ Get the information about available elements in the current document
    """
    response = requests.get(
        os.path.join(
            domain, "api/documents/d/{}/w/{}/elements".format(did,wid)
        ), 
        headers={
            "Content-Type": "application/json", 
            "Accept": "application/vnd.onshape.v2+json;charset=UTF-8;qs=0.09", 
            "Authorization" : "Bearer " + auth_token
        }
    )
    if response.ok: 
        return response.json() 
    else: 
        return None

def get_blob_data(
    domain: str, did: str, wid: str, eid: str, auth_token: str
) -> Any: 
    """ Get the blob content of the given element
    """
    response = requests.get(
        os.path.join(
            domain, "api/blobelements/d/{}/w/{}/e/{}".format(did,wid,eid)
        ), 
        headers={
            "Accept": "application/octet-stream", 
            "Authorization" : "Bearer " + auth_token
        }
    )
    if response.ok: 
        return response.content
    else: 
        return None

def get_shaded_views(
    domain: str, did: str, wid:str, eid:str, etype:str,  auth_token: str
) -> Any: 
    """Get a thumbnail image of the question for display 
    """
    response = requests.get(
        os.path.join(
            domain, "api/{}/d/{}/w/{}/e/{}/shadedviews".format(etype, did, wid, eid)
        ), 
        params={
            "outputHeight": 60, 
            "outputWidth": 60, 
            "pixelSize": 0, 
            "viewMatrix": "0.612,0.612,0,0,-0.354,0.354,0.707,0,0.707,-0.707,0.707,0"
        }, 
        headers={
            "Content-Type": "application/json", 
            "Accept": "application/vnd.onshape.v2+json;charset=UTF-8;qs=0.09", 
            "Authorization": "Bearer " + auth_token
        }
    )
    
    if response.ok: 
        return f"data:image/png;base64,{response.json()['images'][0]}"
    else: 
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABmJLR0QA/wD/AP+gvaeTAAAAy0lEQVRIie2VXQ6CMBCEP7yDXkEjeA/x/icQgrQcAh9czKZ0qQgPRp1kk4ZZZvYnFPhjJi5ABfRvRgWUUwZLxIe4asEsMOhndmzhqbtZSdDExxh0EhacRBIt46V5oJDwEd4BuYQjscc90ATiJ8UfgFvEXPNNqotCKtEvF8HZS87wLAeOijeRTwhahsNoWmVi4pWRhLweqe4qCp1kLVUv3UX4VgtaX7IXbmsU0knuzuCz0SEwWIovvirqFTSrKbLkcZ8v+RecVyjyl3AHdAl3ObMLisAAAAAASUVORK5CYII="


def get_doc_info(
    domain: str, did: str, auth_token: str
) -> Any: 
    """ Get the document info from the current document
    """
    response = requests.get(
        os.path.join(
            domain, "api/documents/{}".format(did)
        ), 
        headers={
            "Content-Type": "application/json", 
            "Accept": "application/vnd.onshape.v2+json;charset=UTF-8;qs=0.09", 
            "Authorization" : "Bearer " + auth_token
        }
    )
    if response.ok: 
        return response.json() 
    else: 
        return None

def get_user_doc_list(
    domain:str, auth_token: str
) -> Any: 
    """ Get list of documents - created by the user/ recently opened by the user and shared with the user
    """
    response = requests.get(
        os.path.join(
            domain, "api/documents"
        ), 
        headers={
            "Content-Type": "application/json", 
            "Accept": "application/vnd.onshape.v2+json;charset=UTF-8;qs=0.09", 
            "Authorization" : "Bearer " + auth_token
        }
    )
    if response.ok: 
        return response.json() 
    else: 
        return None

def get_class_list(
    domain: str,  auth_token: str, massAsGroup=True
) -> Any: 
    """ Get the list of classes for the user
    """
    response = requests.get(
        os.path.join(
            domain, "api/globaltreenodes/magic/15"        
            ), 
        headers={
            "Content-Type": "application/json", 
            "Accept": "application/vnd.onshape.v2+json;charset=UTF-8;qs=0.09", 
            "Authorization" : "Bearer " + auth_token
        }
    )
    if response.ok: 
        return response.json() 
    else:   
        return None


def get_element_info(
    domain: str, did: str, wvm: str, eid: str, auth_token: str
) -> Any: 
    """ Get information about element 
    """
    response = requests.get(
        os.path.join(
            domain, "api/documents/d/{}/w/{}/elements?elementId={}&withThumbnails=false".format(did, wvm, eid)
        ), 
        headers={
            "Content-Type": "application/json", 
            "Accept": "application/vnd.onshape.v2+json;charset=UTF-8;qs=0.09", 
            "Authorization" : "Bearer " + auth_token
        }
    )
    if response.ok: 
        return response.json() 
    else:   
        return None

#################### Other helper functions ####################

def elapsed_time(start_time: str, stop_time: str):
    createdAt = datetime.strptime(start_time.replace("T"," ").split("+")[0],'%Y-%m-%d %H:%M:%S.%f')
    modifiedAt = datetime.strptime(stop_time.replace("T"," ").split("+")[0],'%Y-%m-%d %H:%M:%S.%f')
    delta = modifiedAt - createdAt
    time_formatted = str(delta).split(".")[0].split(":")
    if "days" in time_formatted[0]:
        return time_formatted[0].split(" days,")[0] + "D" + time_formatted[0].split(" days,")[1] + "H" + time_formatted[1] + "M" + time_formatted[2] + "S"
    else:
        return time_formatted[0] + "H" + time_formatted[1] + "M" + time_formatted[2] + "S"

def get_ref_url_ids(ref_url: str):
    try:
        ref = dict()
        ref['did'] = ref_url.split("documents/")[1].split("/w/")[0]
        ref['wid'] = ref_url.split("/w/")[1].split("/e/")[0]
        ref['eid'] = ref_url.split("/e/")[1].split("?")[0]
        ref['eType']=''
        return ref
    except:
        return None
    
def convert_cs_to_array(cs_ref_urls: str): 
    
    #converts all the comma separated urls to array of urls

    #TO FIX: check for empty or ill formatted urls before returning the ref_urls
    ref_urls=[]
    try:
        for cs_ref_url in cs_ref_urls:
            for url in cs_ref_url.split(","):
                ref_urls.append(url)
    except:
        return None
    return ref_urls

# Get parts list for part studio and create dictionary of IDs to names
def make_props(curr_user, urlIds, mass_props):
    if curr_user.etype == "partstudios":
        part_list = get_part_list(curr_user.os_domain, urlIds['did'], "w", urlIds['wid'], urlIds['eid'], curr_user.access_token)
        partId_to_name = {} 
        for item in part_list: 
            partId_to_name[item['partId']] = item['name']
        # partstudios ref_props = [[mass, vol, periphery, principalInertia, partName],[...]] sorted by vol decending
        props = [
            [prt['mass'][0] for prt in mass_props['bodies'].values()], 
            [prt['volume'][0] for prt in mass_props['bodies'].values()], 
            [prt['periphery'][0] for prt in mass_props['bodies'].values()], 
            [prt['principalInertia'][0] for prt in mass_props['bodies'].values()], 
            [partId_to_name[prt] for prt in mass_props['bodies'].keys()]
        ]
        props = sorted([
                [
                    props[0][i], props[1][i], 
                    props[2][i], props[3][i], 
                    props[4][i]
                ] 
                for i in range(len(props[0]))
            ], key=lambda x : x[1])
        
    elif curr_user.etype == "assemblies":
        # assemblies ref_props = [mass, vol, periphery, principalInertia]
        props = [[
                mass_props['mass'][0], 
                mass_props['volume'][0], 
                mass_props['periphery'][0],
                mass_props['principalInertia'][0]
            ]]
    return props