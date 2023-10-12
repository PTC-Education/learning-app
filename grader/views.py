import os 
import requests
from datetime import timedelta, datetime
from typing import Union 

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse 
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.utils import timezone 
from django.utils.datastructures import MultiValueDictKeyError
from django.core.exceptions import ObjectDoesNotExist


from .models import * 

import markdown

# Create your views here.
def home(request: HttpRequest, os_user_id=None):
    """ 
    The home page that can be accessed either logged in in-app or as a standard URL without login information. 
    
    The page documents more extensive user instructions, some technical tips, and a documentation on all data collections from the users. 

    **Arguments:**
        
    - ``os_user_id``: (Optional) identify the :model:`grader.AuthUser` model with the user's login information.

    **Template:**

    :template:`grader/home.html`
    """
    context = {"user": None} 
    if os_user_id: 
        curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
        context['user'] = curr_user
    return render(request, "grader/home.html", context=context)


def grader(request: HttpRequest, os_user_id: str, mass_props=None):
    """ 
    The auto grader page for checking a model's mass properties and time completion. 

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



def instruction(request: HttpRequest, os_user_id: str): 
    """ 
    If the user wants to load instruction content on the app as HTML using a markdown file the view is called
    
    **Context:**
    
    
    **Arguments:**
    
    - ``os_user_id``: the unique ID linked to the user's :model:`grader.AuthUser` profile
    
    **Template:**
    
    :template:`grader/grader.html`
    """
    mdHTMLtext=''

    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 

    blobs=[] #store the blob from the markdown imported on the document
    #get all elements in the document
    elements_info=get_elements_info(curr_user.os_domain, curr_user.did,curr_user.wid ,auth_token=curr_user.access_token) 
    #only for elements that is named instruction.md
    for element_info in elements_info:
        if(element_info['name'] == "instruction.md"): 
            blobs.append(get_blob_data(curr_user.os_domain, curr_user.did,curr_user.wid,element_info['id'] ,auth_token=curr_user.access_token)) #read the content of the markdown file
    mdHTMLtext=md_HTML_create(blobs)  #convert markdown .md file to HTML
    context={
        "user": curr_user, 
        "mdHTMLtext":mdHTMLtext
    }
    return render(
        request, "grader/instruction.html", 
        context=context
    )

def grade_model(request: HttpRequest, os_user_id: str): 
    """ 
    When a user submits a model, API calls are made to check if the 
    model is dimensionally correct and placed in proper orientation. 
    
    **Context:**
    
    View to get time to completion and mass props compared to reference model
    
    **Arguments:**
    
    - ``os_user_id``: the unique ID linked to the user's :model:`grader.AuthUser` profile
    - ``ref_urls``: the reference element for the model to be compared to
    
    **Template:**
    
    :template:`grader/grader.html`
    """
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    ref_urls = request.GET.getlist('ref_url')

    # Refresh token if needed 
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 
    
    # Get mass props of model the user currently has opened
    user_mass_prop = get_mass_props(
            curr_user.os_domain, curr_user.did, "w", curr_user.wid, curr_user.eid, curr_user.etype, 
            massAsGroup=True, auth_token=curr_user.access_token
        )

    if not user_mass_prop: # API error 
        return HttpResponse(curr_user.etype)
        # return HttpResponse("An unexpected error has occurred. Please check internet connection and try relaunching the app in the part studio that you originally started this modelling question with ...")
    # Get info about the document the user currently has opened
    user_doc_info = get_doc_info(curr_user.os_domain, curr_user.did, auth_token=curr_user.access_token)

    # Set list of user_props [mass, vol, periphery, principleInertia]
    try:
        if curr_user.etype == "partstudios":
            user_props = [
                    user_mass_prop['bodies']['-all-']['mass'][0], 
                    user_mass_prop['bodies']['-all-']['volume'][0], 
                    user_mass_prop['bodies']['-all-']['periphery'][0],
                    user_mass_prop['bodies']['-all-']['principalInertia'][0]
                ]
        elif curr_user.etype == "assemblies":
            user_props = [
                    user_mass_prop['mass'][0], 
                    user_mass_prop['volume'][0], 
                    user_mass_prop['periphery'][0],
                    user_mass_prop['principalInertia'][0]
                ]
        for i, prop in enumerate(user_props):

            #instead of rounding off the mass here we will round off during display
            if prop < 0.1 or prop > 99: 
                user_props[i] = '{:.2e}'.format(user_props[i])
            else: 
                user_props[i] = round(user_props[i], 3)
            pass
    except:
        user_props = None
    
    # Get info and mass props for all url's in ref doc list
    ref_props = []
    failed_urls = []
    blobs=[]
    for i, url in enumerate(ref_urls):
        ref_url = get_ref_url_ids(url)
        try:
            mass_prop = get_mass_props(
                        curr_user.os_domain, ref_url['did'], "w", ref_url['wid'], ref_url['eid'], curr_user.etype, 
                        massAsGroup=True, auth_token=curr_user.access_token
                    )
            if curr_user.etype == "partstudios":
                doc_mass = mass_prop['bodies']['-all-']['mass'][0]
            elif curr_user.etype == "assemblies":
                doc_mass = mass_prop['mass'][0]
            # Round for display
            #might be source of error
            if doc_mass < 0.1 or doc_mass > 99: 
                doc_mass = '{:.2e}'.format(doc_mass)
            else: 
                doc_mass = round(doc_mass, 3)
            
            doc_info = get_doc_info(curr_user.os_domain, ref_url['did'], auth_token=curr_user.access_token)
            doc_name = doc_info['name']
            doc_time = elapsed_time(doc_info['defaultWorkspace']['createdAt'],doc_info['defaultWorkspace']['modifiedAt'])
            ref_props.append([doc_name, doc_time, doc_mass])
        except:
            failed_urls.append(url)
    
    if len(failed_urls) == 0:
        failed_urls = None

    ref_table = ref_table_create(ref_props)
    err_tol = 0.005

    if len(ref_props)>0 and user_props:
        check_symbols=[]
        for i, ref_prop in enumerate(ref_props): 

            # Check for accuracy 
            if (
                float(ref_prop[2]) * (1 - err_tol) > float(user_props[0]) or 
                float(user_props[0]) > float(ref_prop[2]) * (1 + err_tol)
            ): 
                check_symbols.append("&#x2717;")
            else: 
                check_symbols.append("&#x2713;")

    else:
        check_symbols=None
        
    ref_table = ref_table_create(ref_props,check_symbols)

    user_doc_time = elapsed_time(user_doc_info['defaultWorkspace']['createdAt'],user_doc_info['defaultWorkspace']['modifiedAt'])
    context={
        "user": curr_user, 
        "doc_time" : user_doc_time,
        "ref_table" : ref_table,
        "failed_urls" : failed_urls,
        "ref_urls" : ref_urls,

    }
    return render(
        request, "grader/grader.html", 
        context=context
    )

#################### Helper API calls ####################

def get_mass_props(
    domain: str, did: str, wvm: str, wvmid: str, eid: str, etype: str, auth_token: str, massAsGroup=True
) -> Any: 
    """ Get the mass and geometry properties of the given element 
    """
    response = requests.get(
        os.path.join(
            domain, 
            "api/{}/d/{}/{}/{}/e/{}/massproperties".format(
            etype, did, wvm, wvmid, eid
        )
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


def get_elements_info(
    domain: str, did: str, wid: str, auth_token: str
) -> Any: 
    """ Get the information about available elements in the current document
    """
    response = requests.get(
        os.path.join(
            domain, 
            "api/documents/d/{}/w/{}/elements".format(did,wid)
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
            domain, 
            "api/blobelements/d/{}/w/{}/e/{}".format(did,wid,eid)
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



def get_doc_info(
    domain: str, did: str, auth_token: str
) -> Any: 
    """ Get the document info from the current document
    """
    response = requests.get(
        os.path.join(
            domain, 
            "api/documents/{}".format(did)
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

def part_mass_check(user_prop: Iterable[Any], ref_prop: Iterable[Any]=None, check_symbols: Iterable[Any]=None
) -> Union[bool, str]: 
    
    if ref_prop:
        mass_msg = '''
        <table>
            <tr>
                <th>Properties</th>
                <th>User Values</th>
                <th>Ref Values</th>
                <th>Check</th>
            </tr>
        '''
        prop_name = ["Mass (kg)", "Volume (m^3)", "Surface Area (m^2)", "Principal Inertia Min (kg.m^2)"]
        for i, item in enumerate(prop_name): 
            mass_msg += f'''
            <tr>
                <td>{item}</td>
                <td>{user_prop[i]}</td>
                <td>{ref_prop[i]}</td>
                <td>{check_symbols[i]}</td>
            </tr>
            '''
        return mass_msg + "</table>"
    else:
        mass_msg = '''
        <table>
            <tr>
                <th>Properties</th>
                <th>User Values</th>
            </tr>
        '''
        prop_name = ["Mass (kg)", "Volume (m^3)", "Surface Area (m^2)", "Principal Inertia Min (kg.m^2)"]
        for i, item in enumerate(prop_name): 
            mass_msg += f'''
            <tr>
                <td>{item}</td>
                <td>{user_prop[i]}</td>
            </tr>
            '''
        return mass_msg + "</table><br><small>Reference URL can't be accessed or is a different element type</small>"



def md_HTML_create(blobs: Iterable[Any]=None) -> Union[bool, str]: 
    
    mdHTMLtext=''
    for blob in blobs:
        mdHTMLtext =  markdown.markdown(blob.decode('utf-8'), extensions=['md_in_html'])
    return mdHTMLtext



def ref_table_create(ref_props: Iterable[Any]=None, checks: Iterable[Any]=None) -> Union[bool, str]: 
    
    if checks:
        ref_table = '''
        <table>
            <tr>
                <th>Doc Name</th>
                <th>Time</th>
                <th>Mass</th>
                <th>Check</th>
            </tr>
        '''
        for i, item in enumerate(ref_props): 
            ref_table += f'''
            <tr>
                <td>{item[0]}</td>
                <td>{item[1]}</td>
                <td>{item[2]}</td>
                <td>{checks[i]}</td>
            </tr>
            '''
        return ref_table + "</table>"
    else:
        ref_table = '''
        <table>
            <tr>
                <th>Doc Name</th>
                <th>Time</th>
                <th>Mass</th>
            </tr>
        '''
        for i, item in enumerate(ref_props): 
            ref_table += f'''
            <tr>
                <td>{item[0]}</td>
                <td>{item[1]}</td>
                <td>{item[2]}</td>
            </tr>
            '''
        return ref_table + "</table>"


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
        ref['eid'] = ref_url.split("/e/")[1].split("/")[0]
        return ref
    except:
        return None