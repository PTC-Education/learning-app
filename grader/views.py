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
import markdown

# Create your views here.

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
def generic_grader(request: HttpRequest, os_user_id: str, mass_props=None):
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
        context={
        "user": curr_user, 
        "urlgradetab" : True #to enable url text input
        }
    if mass_props:
        context['mass_props'] = mass_props
    return render(request, "grader/generic_grader.html", context=context)
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
    user.etype = get_element_type(user.os_domain ,user.did, user.wid, user.eid, auth_token=user.access_token)[0]["elementType"]
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
def classlist(request: HttpRequest, os_user_id: str): 
    """ 
    This function loads the list of classes the user has created.
    
    **Context:**
    
    
    **Arguments:**
    
    - ``os_user_id``: the unique ID linked to the user's :model:`grader.AuthUser` profile
    
    **Template:**
    
    :template:`grader/grader.html`
    """

    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 

    classes=[] # to store the names of classes
    assignments=[] #array to store assisgnments within the classes
    #get all elements in the document
    classinfo=get_class_list(curr_user.os_domain,auth_token=curr_user.access_token) 
    items=classinfo["items"]

    try:
        for item in items:
            if(item["resourceType"]=="classroom"):
                classes.append([item["name"],item["id"]])
   
    except:
        print("Error in classes") #need better error message here
    context={
            "user": curr_user, 
            "classes":classes,
        }
    return render(
        request, "grader/showlist.html",  # need to render this page with a list of available markdown files , users should be able to select and open the file of their choice
        context=context
   
    )
def filelist(request: HttpRequest, os_user_id: str): 
    """ 
    If the user wants to load instruction content on the app as HTML using a markdown file the view is called. This function will return an array of all markdown files and their contents
    **Context:**
    
    
    **Arguments:**
    
    - ``os_user_id``: the unique ID linked to the user's :model:`grader.AuthUser` profile
    
    **Template:**
    
    :template:`grader/grader.html`
    """
    mdHTMLtext='Empty'

    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 

    blobs=[] # to store the blob from the markdowns imported on the document
    markdown_file_names=[] #array to store all markdown files in the document
    #get all elements in the document
    elements_info=get_elements_info(curr_user.os_domain, curr_user.did,curr_user.wid ,auth_token=curr_user.access_token) 
    try:
        for element_info in elements_info:
            #if(element_info['name'] == "instruction.md"): 
            if(element_info["dataType"] == "text/x-markdown"): #check if the element is a markdown file
                filename=element_info["name"]
                filecontent_in_md=get_blob_data(curr_user.os_domain, curr_user.did,curr_user.wid,element_info['id'] ,auth_token=curr_user.access_token)
                filecontent_in_HTML=md_HTML_create(filecontent_in_md)
                blobs.append([filename,filecontent_in_HTML])
   
    except:
        print("Error") #need better error message here
    context={
            "user": curr_user, 
            "filenames":markdown_file_names, # all markdown file names with the context
            "blobs":blobs                     #all markdown contents   
        }
    return render(
        request, "grader/showlist.html",  # need to render this page with a list of available markdown files , users should be able to select and open the file of their choice
        context=context
   
    )

    #saving the snippet below for instruction.html to render markdown files to HTML
    '''
    
        context={
            "user": curr_user, 
            "error_message":"Error"
        }
    if mdHTMLtext=='Empty':
        context={
            "user": curr_user, 
            "error_message":"No supporting markdownfile found. Upload instruction.md "
        }
    else:
        context={
            "user": curr_user, 
            "mdHTMLtext":mdHTMLtext
        }
    return render(
        request, "grader/instruction.html", 
        context=context
    )
    '''
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
    cs_ref_urls = request.GET.getlist('ref_url')
    ref_urls = convert_cs_to_array(cs_ref_urls) 
    if(ref_urls ==['']): #check blank url field
        context={ 
        "user": curr_user, 
        "urlgradetab" :True,
        "error_message" : "URL not detected. Please copy and paste a valid Onshape URL and try again",
        }
        return render(request, "grader/generic_grader.html",context=context )

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
    user_user_name=user_doc_info['name']
    user_doc_name=user_doc_info["createdBy"]["name"]
    user_doc_time = elapsed_time(user_doc_info['defaultWorkspace']['createdAt'],user_doc_info['defaultWorkspace']['modifiedAt'])

    # Set list of user_props [mass, vol, periphery, principleInertia]
    try:
        if curr_user.etype == "PARTSTUDIO":
            user_props = [
                    user_mass_prop['bodies']['-all-']['mass'][0], 
                    user_mass_prop['bodies']['-all-']['volume'][0], 
                    user_mass_prop['bodies']['-all-']['periphery'][0],
                    user_mass_prop['bodies']['-all-']['principalInertia'][0]
                ]
        elif curr_user.etype == "ASSEMBLY":
            user_props = [
                    user_mass_prop['mass'][0], 
                    user_mass_prop['volume'][0], 
                    user_mass_prop['periphery'][0],
                    user_mass_prop['principalInertia'][0]
                ]
        '''
        for i, prop in enumerate(user_props):
            if prop < 0.1 or prop > 99: 
                user_props[i] = '{:.2e}'.format(user_props[i])
            else: 
                user_props[i] = round(user_props[i], 3)
            pass
        '''
    except:
        user_props = None
    
    user_props.append(user_user_name)
    user_props.append(user_doc_name)
    user_props.append(user_doc_time)

    # Get info and mass props for all url's in ref doc list
    all_ref_props = []
    failed_urls = []
    

    for i, url in enumerate(ref_urls): 
        ref_url = get_ref_url_ids(url)

        #grab the element Type of reference URL 
        try:
            eType=get_element_type(curr_user.os_domain ,ref_url['did'],ref_url['wid'], ref_url['eid'], auth_token=curr_user.access_token)
            ref_url['eType']=eType[0]["elementType"]
            ref_element_name=eType[0]["name"]
        except:
            print("Error with eType, perhaps blank refURL")
            ref_url['eType']="Error"

        try:
            #check the element type of reference and current document
            ref_props=[]  
            if(ref_url['eType']==curr_user.etype):     
                try:
                    ref_mass_prop = get_mass_props(
                        curr_user.os_domain, ref_url['did'], "w", ref_url['wid'], ref_url['eid'], ref_url['eType'], 
                        massAsGroup=True, auth_token=curr_user.access_token
                    )
                    if ref_url['eType'] == "PARTSTUDIO" :
                        ref_props = [
                                ref_mass_prop['bodies']['-all-']['mass'][0], 
                                ref_mass_prop['bodies']['-all-']['volume'][0], 
                                ref_mass_prop['bodies']['-all-']['periphery'][0],
                                ref_mass_prop['bodies']['-all-']['principalInertia'][0]
                            ]
                    elif ref_url['eType']== "ASSEMBLY":
                        ref_props = [
                                ref_mass_prop['mass'][0], 
                                ref_mass_prop['volume'][0], 
                                ref_mass_prop['periphery'][0],
                                ref_mass_prop['principalInertia'][0]
                            ]
                    '''
                    for i, prop in enumerate(ref_props):
                        if prop < 0.1 or prop > 99: 
                            ref_props[i] = '{:.2e}'.format(ref_props[i])
                        else: 
                            ref_props[i] = round(ref_props[i], 3)
                        pass
                        '''
                except:
                    ref_props = None       

                type_match_check=True

            else:
                type_match_check=False 

            #Get the document info of the reference document for user, name of document,time
            ref_doc_info = get_doc_info(curr_user.os_domain, ref_url['did'], auth_token=curr_user.access_token)
            ref_user_name=ref_doc_info["createdBy"]["name"]
            ref_doc_name = ref_doc_info['name']
            ref_doc_time = elapsed_time(ref_doc_info['defaultWorkspace']['createdAt'],ref_doc_info['defaultWorkspace']['modifiedAt'])
            ref_props.append(ref_element_name)
            ref_props.append(ref_user_name)
            ref_props.append(ref_doc_time)
            ref_props.append(ref_doc_name)
            all_ref_props.append((ref_props,type_match_check))
        except:
            print("failed")
            failed_urls.append(url)

    if len(failed_urls) == 0:
        failed_urls = None
    zipped_url_props=zip(all_ref_props,ref_urls)
    context={
    "user": curr_user, 
    "failed_urls" : failed_urls,
    "user_props":user_props,
    "zipped_url_props":zipped_url_props,
    "urlgradetab": True,
    }
    return render(
        request, "grader/generic_grader.html", 
        context=context
    )
    err_tol = 0.005

    if len(all_ref_props)>0 and user_props:
        check_symbols=[]
        for i, ref_prop in enumerate(all_ref_props): 
            if(ref_prop[1]): #only when type_match_check=True 
                check_symbol=[] # 0 - mass ,1 - Surface Area, 2 - Volume
                # Check for accuracy 
                if (
                    float(ref_prop[0][0]) * (1 - err_tol) > float(user_props[0]) or 
                    float(user_props[0]) > float(ref_prop[0][0]) * (1 + err_tol)
                ): 
                    check_symbol.append("&#x2717;")
                else: 
                    check_symbol.append("&#x2713;")

                if (
                    float(ref_prop[0][1]) * (1 - err_tol) > float(user_props[1]) or 
                    float(user_props[1]) > float(ref_prop[0][1]) * (1 + err_tol)
                ): 
                    check_symbol.append("&#x2717;")
                else: 
                    check_symbol.append("&#x2713;")
                
                if (
                    float(ref_prop[0][2]) * (1 - err_tol) > float(user_props[2]) or 
                    float(user_props[2]) > float(ref_prop[0][2]) * (1 + err_tol)
                ): 
                    check_symbol.append("&#x2717;")
                else: 
                    check_symbol.append("&#x2713;")

                check_symbols.append(check_symbol)
            else:
                check_symbols.append("Type Mismatch")
    else:
        check_symbols=None

    ref_table = ref_table_create(user_props, all_ref_props,check_symbols,ref_urls)
    context={
        "user": curr_user, 
        "ref_table" : ref_table,
        "failed_urls" : failed_urls,
        "ref_urls" : ref_urls,
        "urlgradetab": True

    }
    return render(
        request, "grader/generic_grader.html", 
        context=context
    )

def listdocs(request: HttpRequest, os_user_id: str, did:str, wid:str): 
    """ 
    This function loads the list of document created, opened or shared by/with the users
    
    **Context:**
    
    
    **Arguments:**
    
    - ``os_user_id``: the unique ID linked to the user's :model:`grader.AuthUser` profile
    
    **Template:**
    
    :template:`grader/grader.html`
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
            eName=eInfo["name"]
            eid=eInfo["id"]

            if(eType == curr_user.etype):
                eType_present=True  # indicate the etype is present
                image_bytes=get_shadedviews_image_data(curr_user.os_domain, did,wid,eid, eType, auth_token=curr_user.access_token)
                if(image_bytes):
                    image_str=image_bytes.decode('utf8')
                    image_json=json.loads(image_str)
                    image=image_json["images"][0]
                else:
                    #if there are no shaded views add a default image of an empty
                    image= "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"
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
            "doclisttab" :True

        }
    return render(
        request, "grader/generic_grader.html",  # need to render this page with a list of available markdown files , users should be able to select and open the file of their choice
        context=context    )  



def enable_csv(request: HttpRequest, os_user_id: str): 
    """ 
    Upload a list of documents using a csv file. The urls must be separated by commas
 
    
    **Arguments:**
    - ``os_user_id``: the unique ID linked to the user's :model:`grader.AuthUser` profile
    **Template:**
    :template:`grader/grader.html`
    """
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 
    context={
        "user": curr_user, 
        "uploadtab":True
        }
    
    print(context)
    print("Enable uploaded")
    return render(
        request, "grader/generic_grader.html",  # need to render this page with a list of available markdown files , users should be able to select and open the file of their choice
        context=context
   
    )

def upload_csv(request: HttpRequest, os_user_id: str): 
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
    print("great")
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 
    print("called")
    csvfile = request.FILES["csvfile"]
    cs_ref_urls=csvfile.read().decode("utf-8")
    context={
        "user": curr_user, 
        "ref_urls" :cs_ref_urls,
        "urlgradetab" : True
        }

    return render(
        request, "grader/generic_grader.html",  # need to render this page with a list of available markdown files , users should be able to select and open the file of their choice
        context=context    )  
#################### Helper API calls ####################

def get_mass_props(
    domain: str, did: str, wvm: str, wvmid: str, eid: str, eType: str, auth_token: str, massAsGroup=True
) -> Any: 
    """ Get the mass and geometry properties of the given element 
    """
    elementType=""
    if(eType=="PARTSTUDIO"):
        elementType="partstudios"
    elif(eType=="ASSEMBLY"):
        elementType="assemblies"
    response = requests.get(
        os.path.join(
            domain, 
            "api/{}/d/{}/{}/{}/e/{}/massproperties".format(
            elementType, did, wvm, wvmid, eid
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
def get_shadedviews_image_data(
    domain: str, did: str, wid:str, eid:str, eType:str,  auth_token: str
) -> Any: 
    """ Get the image data from the given url
    """
    elementType=""
    if(eType=="PARTSTUDIO"):
        elementType="partstudios"
    elif(eType=="ASSEMBLY"):
        elementType="assemblies"
    response = requests.get(
        os.path.join(
            domain, 
            "api/{}/d/{}/w/{}/e/{}/shadedviews?viewMatrix=0.612,0.612,0,0,-0.354,0.354,0.707,0,0.707,-0.707,0.707,0&outputHeight=50&outputWidth=50&pixelSize=0&edges=show&showAllParts=false&includeSurfaces=false&useAntiAliasing=false&includeWires=false".format(elementType,did,wid,eid)
        ), 
        headers={
            "Content-Type": "application/json", 
            "Accept": "application/vnd.onshape.v2+json;charset=UTF-8;qs=0.09", 
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
def get_user_doc_list(
    domain:str, auth_token: str
) -> Any: 
    """ Get list of documents - created by the user/ recently opened by the user and shared with the user
    """

    response = requests.get(
        os.path.join(
            domain, 
            "api/documents"
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
            domain, 
            "api/globaltreenodes/magic/15"        
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
def get_element_type(
    domain: str, did: str, wvm: str, eid: str, auth_token: str
) -> Any: 
    """ Get the mass and geometry properties of the given element 
    """
    response = requests.get(
        os.path.join(
            domain, 
            "api/documents/d/{}/w/{}/elements?elementId={}&withThumbnails=false".format(did, wvm, eid)
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

def md_HTML_create(blob: Iterable[Any]=None) -> Union[bool, str]: 
    
    mdHTMLtext=''
    mdHTMLtext =  markdown.markdown(blob.decode('utf-8'), extensions=['md_in_html'])
    return mdHTMLtext

def ref_table_create(user_props:Iterable[Any]=None, ref_props: Iterable[Any]=None, checks: Iterable[Any]=None, ref_urls: Iterable[Any]=None,) -> Union[bool, str]: 
    
    if checks:
        ref_table = '''
        <table id="resulttable">
            <tr>
                <th>Tab name</th>
                <th>Mass</th>
                <th>Volume</th>
                <th>Periphery</th>
                <th>Check</th>
                <th>User name</th>
                <th>Elapsed Time</th>
                <th>URL<th>
            </tr>
            <tr class= "userrow">
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>-</td>
                <td>{}</td>
                <td>{}</td>
                <td>-</td>
            </tr>

            '''.format(user_props[4],user_props[0],user_props[1],user_props[2],user_props[5],user_props[6])
        for i, item in enumerate(ref_props): 
            if item[1]: #if the element type is matched - the match = True is saved in item[1] item[0] has all other values 0-mass, 1, volume, 2 surface area, 3, interia, 4, tab name, 5 username, 6 time between creation and edit
                ref_table += f'''
                <tr>
                    <td>{item[0][4]}</td>
                    <td>{item[0][0]}</td>
                    <td>{item[0][1]}</td>
                    <td>{item[0][2]}</td>
                    <td>{checks[i]}</td>
                    <td>{item[0][5]}</td>
                    <td>{item[0][6]}</td>
                    <td><a href={ref_urls[i]} target='_blank'> Document link </a></td>
                </tr>
                '''
            else:#if the element type is not matched -  0, tab name, 1 username, 2 time between creation and edit
           
                ref_table += f'''
                <tr>

                    <td>{item[0][0]}</td>
                    <td>-</td>
                    <td>-</td>
                    <td>-</td>
                    <td>{checks[i]}</td>
                    <td>{item[0][1]}</td>
                    <td>{item[0][2]}</td>
                    <td><a href={ref_urls[i]} target='_blank'> Document link </a></td>
   
                </tr>
                '''
        return ref_table + '</table>'


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
    
def convert_cs_to_array(cs_ref_urls: str): #converts all the comma separated urls to array of urls
    ref_urls=[]
    try:
        for cs_ref_url in cs_ref_urls:
            for url in cs_ref_url.split(","):
                ref_urls.append(url)
    except:
        return None
    return ref_urls
    