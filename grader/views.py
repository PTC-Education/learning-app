import os 
import requests
from datetime import timedelta, datetime
from typing import Union 
import json
import re

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

def url_input_page(request: HttpRequest, os_user_id: str , user_type:str):
    """ 
   This function will open the urlinput.html customized for single url and multiurl+upload csv function for student and educators use. 

    **Arguments:**
        
    - ``os_user_id``: identify the :model:`grader.AuthUser` model with the user's login information.
    - ``user_type:str``: type of user , options are student and educator

    **Template:**

    :template:`grader/url_input.html`
    """
    context = { "user": None, 
                "usertype": None} 
    
    if os_user_id: 
        curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
        context = {
        "user": curr_user, 
        "user_type": user_type,
        }
    return render(request, "grader/url_input.html", context=context)


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
    
    if not mass_props: # API error 
        return HttpResponse("An unexpected error has occurred. Please check internet connection and try relaunching the app.")

    # Set list of user_props - different for each etype
    try:
        if curr_user.etype == "partstudios":
            # Get parts list for part studio and create dictionary of IDs to names
            part_list = get_part_list(curr_user.os_domain, curr_user.did, "w", curr_user.wid, curr_user.eid, curr_user.access_token)
            partId_to_name = {} 
            for item in part_list: 
                partId_to_name[item['partId']] = item['name']
            
            mass_props = ignore_surfaces(mass_props)
            # partstudios user_props = [[mass, vol, periphery, principalInertia, partName],[...]] sorted by vol decending
            user_props = make_props(mass_props, partId_to_name)

        elif curr_user.etype == "assemblies":
            # assemblies user_props = [mass, vol, periphery, principalInertia]
            user_props = make_props(mass_props, None)
        
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
        user_props = None


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
            ref_props=[] # initialize empty array of ref props

            mass_props = get_mass_props(
                curr_user.os_domain, ref_url['did'], "w", ref_url['wid'], ref_url['eid'], curr_user.etype, 
                massAsGroup=False, auth_token=curr_user.access_token
            )

            if curr_user.etype == "partstudios":
                # Get parts list for part studio and create dictionary of IDs to names
                part_list = get_part_list(curr_user.os_domain, ref_url['did'], "w", ref_url['wid'], ref_url['eid'], curr_user.access_token)
                partId_to_name = {} 
                for item in part_list: 
                    partId_to_name[item['partId']] = item['name']

                mass_props = ignore_surfaces(mass_props)
                # partstudios ref_props = [[mass, vol, periphery, principalInertia, partName],[...]] sorted by vol decending
                ref_props = make_props(mass_props, partId_to_name)

            elif curr_user.etype == "assemblies":
                # assemblies ref_props = [mass, vol, periphery, principalInertia]
                ref_props = make_props(mass_props, None)
            
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

def check_model(request: HttpRequest, os_user_id: str): 
    """ 
    When a user submits, model best practices are checkd for 
    
    **Context:**
    
    View to get time to completion and mass props compared to reference model
    
    **Arguments:**
    
    - ``os_user_id``: the unique ID linked to the user's :model:`grader.AuthUser` profile
    
    **Template:**
    
    :template:`grader/checker.html`
    """
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)

    # Refresh token if needed 
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 

    check_type = request.GET.getlist('check_type')
    check_message = ""
    
    if "Features" in check_type:
        # Get feature list of model the user currently has opened
        feature_list = get_feature_list(
                curr_user.os_domain, curr_user.etype, curr_user.did, "w", curr_user.wid, curr_user.eid, auth_token=curr_user.access_token
            )
        if not feature_list: # API error 
            return HttpResponse("An unexpected error has occurred. Please check internet connection and try relaunching the app.")

        if curr_user.etype == "partstudios":
            check_message += ps_feature_list_helper(feature_list)
        if curr_user.etype == "assemblies":
            check_message += as_feature_list_helper(feature_list)
    
    if "Parts" in check_type:
        # Get parts list of model the user currently has opened
        if curr_user.etype == "partstudios":
            part_list = get_part_list(
                    curr_user.os_domain, curr_user.did, "w", curr_user.wid, curr_user.eid, auth_token=curr_user.access_token
                )
            if not part_list: # API error 
                return HttpResponse("An unexpected error has occurred. Please check internet connection and try relaunching the app.")

            check_message += part_list_helper(part_list)

        if curr_user.etype == "assemblies":
            assembly_def = get_assembly_definition(
                    curr_user.os_domain, curr_user.did, "w", curr_user.wid, curr_user.eid, auth_token=curr_user.access_token
                )
            if not assembly_def: # API error 
                return HttpResponse("An unexpected error has occurred. Please check internet connection and try relaunching the app.")

            check_message += instance_list_helper(assembly_def)

    context={
        "user": curr_user,
        "check_type": check_type,
        "check_message": check_message
    }
    return render(
        request, "grader/checker.html", 
        context=context
    )

#################### Helper API calls ####################

def get_mass_props(
    domain: str, did: str, wvm: str, wvmid: str, eid: str, etype: str, auth_token: str, massAsGroup=True
) -> Any: 
    """ Get the mass and geometry properties of the given element 
    """
    response = requests.get(
        os.path.join(domain, "api/{}/d/{}/{}/{}/e/{}/massproperties".format(etype, did, wvm, wvmid, eid)), 
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
        os.path.join(domain, "api/parts/d/{}/{}/{}/e/{}".format(did, wvm, wvmid, eid)), 
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


def get_assembly_definition(
    domain: str, did: str, wvm: str, wvmid: str, eid: str, auth_token: str
) -> Any: 
    """ Get all parts in an element
    """
    response = requests.get(
        os.path.join(domain, "api/assemblies/d/{}/{}/{}/e/{}".format(did, wvm, wvmid, eid)), 
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
        os.path.join(domain, "api/documents/d/{}/w/{}/elements".format(did,wid)), 
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
        os.path.join(domain, "api/blobelements/d/{}/w/{}/e/{}".format(did,wid,eid)), 
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
        os.path.join(domain, "api/{}/d/{}/w/{}/e/{}/shadedviews".format(etype, did, wid, eid)), 
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

def get_feature_list(
    domain: str, etype: str, did: str, wmv: str, wid: str, eid: str, auth_token: str
) -> Any: 
    """ Get the feature list from both part studios and assemblies
    """
    response = requests.get(
        os.path.join(domain, "api/{}/d/{}/{}/{}/e/{}/features".format(etype, did, wmv, wid, eid)),   
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
        os.path.join(domain, "api/documents"), 
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
        os.path.join(domain, "api/globaltreenodes/magic/15"), 
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
        os.path.join(domain, "api/documents/d/{}/w/{}/elements?elementId={}&withThumbnails=false".format(did, wvm, eid)), 
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

# Eliminate massless bodies from mass_props
def ignore_surfaces(mass_props):
    heavy_bodies = {}
    try:
        for key, value in mass_props['bodies'].items():
            if 'mass' in mass_props['bodies'][key]:
                heavy_bodies[key] = value  

        mass_props['bodies'] = heavy_bodies

        return mass_props
    except:
        return None

def make_props(mass_props, partId_to_name):
    if partId_to_name:
        # partstudios user_props = [[mass, vol, periphery, principalInertia, partName],[...]] sorted by vol decending
        try:
            user_props = [
                [prt['mass'][0] for prt in mass_props['bodies'].values()], 
                [prt['volume'][0] for prt in mass_props['bodies'].values()], 
                [prt['periphery'][0] for prt in mass_props['bodies'].values()], 
                [prt['principalInertia'][0] for prt in mass_props['bodies'].values()], 
                [partId_to_name[prt] for prt in mass_props['bodies'].keys()]
            ]
            user_props = sorted([
                [
                    user_props[0][i], user_props[1][i], 
                    user_props[2][i], user_props[3][i], 
                    user_props[4][i]
                ] 
                for i in range(len(user_props[0]))
            ], key=lambda x : x[1])
            return user_props
        except:
            return None
    else:
        # assemblies ref_props = [mass, vol, periphery, principalInertia]
        try: 
            ref_props = [[
                mass_props['mass'][0], 
                mass_props['volume'][0], 
                mass_props['periphery'][0],
                mass_props['principalInertia'][0]
            ]]
            return ref_props
        except:
            return None

# Extract useful information from featurelist for partstudios
def ps_feature_list_helper(feature_list):
    feature_count = {} # initialize dictionary for number of features used
    renamed_count = 0
    number_of_features = len(feature_list['features'])
    for feature in feature_list['features']:
        if feature['featureType'] == "newSketch":
            feature['featureType'] = "sketch"
        try:
            feature_count[feature['featureType']] += 1
        except:
            feature_count[feature['featureType']] = 1

        feature_name = re.sub('[0-9]','',feature['name']).replace(" ","")
        
        if feature_name.lower() != feature['featureType'].lower():
            renamed_count += 1
    
    feature_count = dict(sorted(feature_count.items(), key=lambda x:x[1], reverse=True)) # re-order feature count by descending number

    feature_message = f'''
    <h3>Feature Checking</h3>
    <p>{renamed_count} out of {number_of_features} features are currently renamed from their defaults.</p>
    <p>List of how many times each feature is used:
    <ul>
    '''
    for k, v in feature_count.items():
        feature_message += f'<li>{k} - {v}</li>'

    return feature_message + '</ul>'

# Extract useful information from featurelist for assemblies
def as_feature_list_helper(feature_list):
    mate_count = 0
    mate_relation_count = 0

    for feature in feature_list['features']:
        if feature['featureType'] == "mate":
            mate_count += 1
        elif feature['featureType'] == "mateRelation":
            mate_relation_count += 1

    feature_message = f'''
    <h3>Feature Checking</h3>
    <p>This assembly has {mate_count} mates and {mate_relation_count} mate relations.</p>
    '''

    return feature_message

# Extract useful information from part lists for partstudios
def part_list_helper(part_list):
    part_count = 0
    part_rename_count = 0
    part_material_count = 0
    surface_count = 0
    
    for part in part_list:
        if part['bodyType'] == "solid":
            part_count += 1
            if re.sub('[0-9]','',part['name']).replace(" ","") != "Part":
                part_rename_count += 1
            if 'material' in part:
                part_material_count += 1

        elif part['bodyType'] == "sheet":
            surface_count += 1

    part_message = f'''
    <h3>Part Checking</h3>
    <p>There is/are {part_count} part(s) in this part studio. <br>
    {part_rename_count}/{part_count} parts are renamed. <br>
    {part_material_count}/{part_count} parts have a material assigned.</p>
    '''

    if surface_count > 0:
        part_message += f'''
        <p>There are {surface_count} surfaces in this part studio.</p>
        '''

    return part_message

# Extract useful information about instances for assemblies
def instance_list_helper(assembly_def):
    instance_count = len(assembly_def['rootAssembly']['instances'])
    part_instance_count = 0
    assemby_instance_count = 0
    
    for instance in assembly_def['rootAssembly']['instances']:
        if instance['type'] == "Part":
            part_instance_count += 1

        elif instance['type'] == "Assembly":
            assemby_instance_count += 1

    part_message = f'''
    <h3>Instance Checking</h3>
    <p>There are {instance_count} instances in this assembly, with {part_instance_count} parts and {assemby_instance_count} sub-assemblies inserted.</p>
    '''

    return part_message