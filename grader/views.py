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
from .api import *


# Create your views here.

def login(request: HttpRequest): 
    """ 
    When the app extension is first opened, this view should be called. 

    **Context:**
    
    If new user, redirects the user to initiate Onshape's OAuth authorization. Once authenticated, the user will be redirected back to :view:`grader.views.authorize`.  
    
    - A new :model:`grader.AuthUser` model will be created for the new user with the user's ``os_user_id``. 
    
    - If the user already exists, new Onshape working environment IDs will be recorded. 
    
    """

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
    user.wv = request.GET.get('wvm')
    user.wvid = request.GET.get('wvmid')
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

    if user.etype == "infopanel":
        return HttpResponseRedirect(reverse("grader:doc_info_checker", args=[user.os_user_id]))
    else:
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

   This function will open the url_input.html customized for single url and multiurl+upload csv function for student and educators use. 


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

def doc_info_checker(request: HttpRequest, os_user_id: str):
    """ 
    This function is for showing elements in a document for best practices checking. 

    **Arguments:**
        
    - ``os_user_id``: identify the :model:`grader.AuthUser` model with the user's login information.

    **Template:**

    :template:`grader/doc_info_checker.html`
    """
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    # Get info and workspace for current document selected

    doc_info = get_doc_info(curr_user.os_domain, curr_user.did, auth_token=curr_user.access_token)
    doc_wid = doc_info['defaultWorkspace']['id']

    # Create HTML for list of elements
    element_list = []
    elements_info = get_element_info(curr_user.os_domain, curr_user.did, "w", doc_wid, "", auth_token=curr_user.access_token)
    for element in elements_info:
        if element['elementType'] == "PARTSTUDIO":
            image = get_shaded_views(curr_user.os_domain, curr_user.did, "w", doc_wid, element['id'], "partstudios", auth_token=curr_user.access_token)
            element_dict = {'etype': 'partstudios', 'id': element['id'], 'name': element['name'], 'image': image}
            element_list.append(element_dict)
        elif element['elementType'] == "ASSEMBLY":
            image = get_shaded_views(curr_user.os_domain, curr_user.did, "w", doc_wid, element['id'], "assemblies", auth_token=curr_user.access_token)
            element_dict = {'etype': 'assemblies', 'id': element['id'], 'name': element['name'], 'image': image}
            element_list.append(element_dict)
    # Get element and check type that the user has selected
    element = request.GET.get('elements')
    check_type = request.GET.getlist('check_type')
    try:
        etype = element.split(" ")[0]
        eid = element.split(" ")[1]
    except:
        pass
    check_message = ""
    summary_msg = {}
    detail_msg = {}
    mates = {}
    mate_relations = {}
    mate_details = {}
    features = {}
    renamed = []
    
    if "Features" in check_type and element:
        # Get feature list of model the user currently has opened
        feature_list = get_feature_list(
                curr_user.os_domain, etype, curr_user.did, "w", doc_wid, eid, auth_token=curr_user.access_token
            )
        if not feature_list: # API error 
            return HttpResponse("An unexpected error has occurred. Please check internet connection and try relaunching the app.")

        if etype == "partstudios":
            features, renamed = ps_feature_list_helper(feature_list)
        if etype == "assemblies":
            # check_message += as_feature_list_helper(feature_list)
            mates, mate_relations, summary_msg = as_get_mate_summary(feature_list)
            mate_details, detail_msg = as_get_mate_details(feature_list)
    
    if "Parts" in check_type and element:
        # Get parts list of model the user currently has opened
        if etype == "partstudios":
            part_list = get_part_list(
                    curr_user.os_domain, curr_user.did, "w", doc_wid, eid, auth_token=curr_user.access_token
                )
            if not part_list: # API error 
                return HttpResponse("An unexpected error has occurred. Please check internet connection and try relaunching the app.")

            check_message += part_list_helper(part_list)

        if etype == "assemblies":
            assembly_def = get_assembly_definition(
                    curr_user.os_domain, curr_user.did, "w", doc_wid, eid, auth_token=curr_user.access_token
                )
            if not assembly_def: # API error 
                return HttpResponse("An unexpected error has occurred. Please check internet connection and try relaunching the app.")

            check_message += instance_list_helper(assembly_def)

    context={
        "user": curr_user, 
        "element_list": element_list,
        "check_type": check_type,
        "check_message": check_message,
        "features": features,
        "renamed": renamed,
        "mates": mates,
        "mate_relations": mate_relations, 
        "summary_msg": summary_msg,
        "mate_details": mate_details,
        "detail_msg": detail_msg
    }

    return render(request, "grader/doc_info_checker.html", context=context)


def list_classes(request: HttpRequest, os_user_id: str):
    """ 
   This function will get the list of classes created by the user.

    **Arguments:**
        
    - ``os_user_id``: identify the :model:`grader.AuthUser` model with the user's login information.

    **Template:**

    :template:`grader/c_and_a.html`
    """
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 

    classes=[]          # to store the names of classes
    assignments=[]      #array to store assisgnments within the classes

    #get information about classrooms created by the user
    try:
        classinfo = get_class_list(curr_user.os_domain,auth_token=curr_user.access_token) 
        items = classinfo["items"]
        for item in items:
            if(item["resourceType"]=="classroom"):
                class_id = item["id"]
                class_name = item["name"]
                number_of_assignment = item["numberOfAssignments"]
                number_of_members = item["numberOfMembers"]
                classes.append([class_id, class_name, number_of_assignment, number_of_members]) # Append all classroom id, name,  number of assignments and number of members
    except:
        print("Error in classes") #need better error message here
    
    #If no classes were detected
    if ( len(classes) == 0): 
        context={
                "user": curr_user, 
                "error_message" : "No classes were found."
            }
        return render(
        request, "grader/index.html", 
        context=context
    )
    
    context={
            "page": "classes",
            "user": curr_user, 
            "classes":classes,
        }
    return render(
        request, "grader/c_and_a.html", 
        context=context
    )

def list_assignments(request: HttpRequest, os_user_id: str, class_id:str , class_name:str):
    """ 
   This function will get the list of classes created by the user.

    **Arguments:**
        
    - ``os_user_id``: identify the :model:`grader.AuthUser` model with the user's login information.

    **Template:**

    :template:`grader/c_and_a.html`
    """
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 

    assignments = []

    try:
        assignment_list = get_assignment_list(curr_user.os_domain, class_id, auth_token = curr_user.access_token)
        items = assignment_list["items"]
        for item in items:
            assignment_id = item["id"]
            assignment_name = item["name"]
            status = item["stateName"]
            in_progress = item["numberOfSubmissionsInProgress"]
            submitted = item["numberOfSubmissionsSubmitted"]
            not_submitted = item["numberOfSubmissionsNotStarted"]
            description = item["description"]
            published_date = item["publishedDate"]
            assignments.append([assignment_id, assignment_name, status, submitted, not_submitted, in_progress, published_date, description,])

    except:
        print("Error in assignment") #need better error message here

    context={
            "user": curr_user, 
            "page": "assignments",
            "assignments": assignments,
            "class_name": class_name,
            "class_id":class_id
        }
    return render(
        request, "grader/c_and_a.html", 
        context=context
    )


def list_members(request: HttpRequest, os_user_id: str, class_id:str, class_name:str, assignment_id:str, assignment_name:str):
    """ 
   This function will get the list of classes created by the user.

    **Arguments:**
        
    - ``os_user_id``: identify the :model:`grader.AuthUser` model with the user's login information.

    **Template:**

    :template:`grader/c_and_a.html`
    """
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 

    submitted_student_works = []  #store submitted work
    action_required_student_works = [] # submitted work that requires user action
    inprogress_student_works = [] #store inprogress work

    #submitted_student_works
    #action_required_student_works
    #both have 6 elements
        # element 0 - student id 
        # element 1 - student name
        # element 2 - number of submission attempts
        # element 3 - submitted document name
        # element 4 - submitted document url
        # element 5 - array of tabs with 3 elements
            # subelement 0 - element url
            # subelement 1 - element name
            # subelement 2 - element thumbnail

    try:
        full_submission_list = get_submission_list(curr_user.os_domain, class_id, assignment_id, auth_token = curr_user.access_token)
        submissions = full_submission_list["submissions"]

        type_dict = {"partstudios":"PARTSTUDIO", "assemblies":"ASSEMBLY"}
        for submission in submissions:
            member_id = submission["memberId"]
            member_name = submission["memberName"]
            state_name = submission["stateName"]

            require_user_action = True 
            number_of_attempts = 0
            tab_names_and_ids =[]  
            
            #If the document is submitted
            if (state_name == "Submitted"):
                doc_name = submission["documents"][0]["metadata"]["dn"]
                url = submission["documents"][0]["viewRef"]
                number_of_attempts = submission["numberOfAttempts"]
                splitted_url = url.split("/documents/")[1].split("/")
                did = splitted_url[0]
                if(len(splitted_url)==1): # url has a document id only
                    doc_info = get_doc_info(curr_user.os_domain, did,  auth_token=curr_user.access_token)
                    wv = "w"
                    wvid = doc_info["defaultWorkspace"]["id"]
                else:
                    wv      = splitted_url[1]
                    wvid    = splitted_url[2]

                if not url.find("/e/") < 0: # if there is an element id in the url of the submitted document
                    tab_id = splitted_url[4].split("?")[0]
                    tab_info = get_element_info(curr_user.os_domain, did, wv, wvid, tab_id, auth_token=curr_user.access_token)
                    tab_type = tab_info[0]["elementType"]

                    #if the type of eid in the url is the same as the current user etype
                    if( tab_type == type_dict[curr_user.etype]):
                        require_user_action = False  #dont require action from user
                        tab_name = tab_info[0]["name"]
                        tab_image   = get_shaded_views(curr_user.os_domain, did, wv, wvid, tab_id, curr_user.etype, auth_token=curr_user.access_token) 
                        tab_names_and_ids.append([url, tab_name, tab_image])  # bundle the  url ,  name and image each tab
                        submitted_student_works.append([member_id, member_name, number_of_attempts, doc_name, url, tab_names_and_ids])
                    else:
                        require_user_action = True #require action from user
                                      
                else:  # if there is no element id in the url of the submitted document
                     require_user_action = True #require action from user
                
                if require_user_action:
                    tab_infos = get_element_info(curr_user.os_domain, did, wv, wvid, " ", auth_token=curr_user.access_token) #get all tab info
                    
                    for tab_info in tab_infos:
                        tab_type = tab_info["elementType"]
                        if( tab_type == type_dict[curr_user.etype]): # Only get information of the tabs that have same element type as the user document
                            tab_name    = tab_info["name"]
                            tab_id      = tab_info["id"]
                            tab_image   = get_shaded_views(curr_user.os_domain, did, wv, wvid, tab_id, curr_user.etype, auth_token=curr_user.access_token)
                            tab_url = curr_user.os_domain + "/documents/" + did + "/" + wv + "/" + wvid + "/e/" + tab_id
                            tab_names_and_ids.append([tab_url, tab_name, tab_image])  # bundle the  url ,  name and image each tab
                    

                    url = tab_names_and_ids[0][0] # update the url to point to the first tab of the document  
                    if(len(tab_names_and_ids) == 1): #If there is only one tab
                        submitted_student_works.append([member_id, member_name, number_of_attempts, doc_name, url, tab_names_and_ids])
                    else:
                        action_required_student_works.append([member_id, member_name, number_of_attempts, doc_name, url, tab_names_and_ids])

                           
            #If the document is in progress
            else:
                doc_name = "Not included"
                url = ""
                if submission["documents"]: # if the user has started a document
                    doc_name = submission["documents"][0]["metadata"]["dn"]
                    url = submission["documents"][0]["viewRef"]
                    
                inprogress_student_works.append([member_id, member_name, state_name, doc_name, url])

    except:
         print("Error in members") #need better error message here
    context={
            "user": curr_user, 
            "page": "submissions",
            "submitted_student_works":submitted_student_works,
            "action_required_student_works": action_required_student_works,
            "inprogress_student_works": inprogress_student_works,
            "class_name": class_name,
            "class_id": class_id,
            "assignment_name": assignment_name 

        }
    return render(
        request, "grader/c_and_a.html", 
        context = context
    )

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

    # Refresh token if needed 
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 
    
    # Get mass props of model the user currently has opened
    mass_props = get_mass_props(
            curr_user.os_domain, curr_user.did, curr_user.wv, curr_user.wvid, curr_user.eid, curr_user.etype, 
            massAsGroup=False, auth_token=curr_user.access_token
        )
    
    if not mass_props: # API error 
        return HttpResponse("An unexpected error has occurred. Please check internet connection and try relaunching the app.")

    # Set list of user_props - different for each etype
    try:
        if curr_user.etype == "partstudios":
            # Get parts list for part studio and create dictionary of IDs to names
            part_list = get_part_list(curr_user.os_domain, curr_user.did, curr_user.wv, curr_user.wvid, curr_user.eid, curr_user.access_token)
            partId_to_name = {} 
            for item in part_list: 
                partId_to_name[item['partId']] = item['name']
            
            mass_props = ignore_surfaces(mass_props)
            # partstudios user_props = [[mass, vol, periphery, principalInertia, partName],[...]] sorted by vol decending
            user_props = make_props(mass_props, partId_to_name)

        elif curr_user.etype == "assemblies":
            # assemblies user_props = [mass, vol, periphery, principalInertia]
            user_props = make_props(mass_props, None)

    except:
        user_props = None

    # Get info about the document the user currently has opened
    user_doc_info = get_doc_info(curr_user.os_domain, curr_user.did, auth_token=curr_user.access_token)
    user_doc_name = user_doc_info['name']
    user_user_name = user_doc_info["createdBy"]["name"]
    user_doc_time = elapsed_time(user_doc_info['defaultWorkspace']['createdAt'],user_doc_info['defaultWorkspace']['modifiedAt'])

    user_url = curr_user.os_domain + "/documents/" + curr_user.did + "/"+ curr_user.wv + "/" + curr_user.wvid + "/e/" + curr_user.eid

    
    # Append user related information along with mass properties
    user_props.insert(0, [user_doc_name, user_user_name, user_doc_time, user_url])

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
                curr_user.os_domain, ref_url['did'], ref_url['wv'], ref_url['wvid'], ref_url['eid'], curr_user.etype, 
                massAsGroup=False, auth_token=curr_user.access_token
            )

            if curr_user.etype == "partstudios":
                # Get parts list for part studio and create dictionary of IDs to names
                part_list = get_part_list(curr_user.os_domain, ref_url['did'], ref_url['wv'], ref_url['wvid'], ref_url['eid'], curr_user.access_token)
                partId_to_name = {} 
                for item in part_list: 
                    partId_to_name[item['partId']] = item['name']

                mass_props = ignore_surfaces(mass_props)
                # partstudios ref_props = [[mass, vol, periphery, principalInertia, partName],[...]] sorted by vol decending
                ref_props = make_props(mass_props, partId_to_name)

            elif curr_user.etype == "assemblies":
                # assemblies ref_props = [mass, vol, periphery, principalInertia]
                ref_props = make_props(mass_props, None)

            # Get all additional info from the reference document
            image = get_shaded_views(curr_user.os_domain, ref_url['did'], ref_url['wv'], ref_url['wvid'], ref_url['eid'], curr_user.etype, auth_token=curr_user.access_token)
            element_info = get_element_info(curr_user.os_domain, ref_url['did'], ref_url['wv'], ref_url['wvid'], ref_url['eid'], auth_token=curr_user.access_token)
            element_name = element_info[0]["name"]
            ref_doc_info = get_doc_info(curr_user.os_domain, ref_url['did'], auth_token=curr_user.access_token)
            user_name = ref_doc_info["createdBy"]["name"]
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
    summary_msg = {}
    detail_msg = {}
    mates = {}
    mate_relations = {}
    mate_details = {}
    features = {}
    renamed = []


    if "Features" in check_type:
        # Get feature list of model the user currently has opened
        feature_list = get_feature_list(
                curr_user.os_domain, curr_user.etype, curr_user.did, curr_user.wv, curr_user.wvid, curr_user.eid, auth_token=curr_user.access_token
            )
        if not feature_list: # API error 
            return HttpResponse("An unexpected error has occurred. Please check internet connection and try relaunching the app.")

        if curr_user.etype == "partstudios":
            features, renamed = ps_feature_list_helper(feature_list)
        if curr_user.etype == "assemblies":
            # check_message += as_feature_list_helper(feature_list)
            mates, mate_relations, summary_msg = as_get_mate_summary(feature_list)
            mate_details, detail_msg = as_get_mate_details(feature_list)
    
    if "Parts" in check_type:
        # Get parts list of model the user currently has opened
        if curr_user.etype == "partstudios":
            part_list = get_part_list(
                    curr_user.os_domain, curr_user.did, curr_user.wv, curr_user.wvid, curr_user.eid, auth_token=curr_user.access_token
                )
            if not part_list: # API error 
                return HttpResponse("An unexpected error has occurred. Please check internet connection and try relaunching the app.")

            check_message += part_list_helper(part_list)

        if curr_user.etype == "assemblies":
            assembly_def = get_assembly_definition(
                    curr_user.os_domain, curr_user.did, curr_user.wv, curr_user.wvid, curr_user.eid, auth_token=curr_user.access_token
                )
            if not assembly_def: # API error 
                return HttpResponse("An unexpected error has occurred. Please check internet connection and try relaunching the app.")

            check_message += instance_list_helper(assembly_def)

    context={
        "user": curr_user,
        "check_type": check_type,
        "check_message": check_message,
        "features": features,
        "renamed": renamed,
        "mates": mates,
        "mate_relations": mate_relations, 
        "summary_msg": summary_msg,
        "mate_details": mate_details,
        "detail_msg": detail_msg
    }
    return render(
        request, "grader/checker.html", 
        context=context
    )

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
        ref['did'] = ref_url.split("documents/")[1].split("/")[0]
        ref['wv'] = ref_url.split("documents/")[1].split("/")[1].split("/")[0]
        ref['wvid'] = ref_url.split("/e/")[0].split("/")[-1]
        ref['eid'] = ref_url.split("/e/")[1].split("?")[0]
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
    default_features = ['sketch', 'extrude', 'revolve', 'sweep', 'loft', 'thicken', 'fill', 'enclose', 'fillet', 'faceblend', 'chamfer', 'draft', 'shell', 'rib', 'externalthread', 'curvepattern', 'linearpattern', 'circularpattern', 'plane', 'mirror', 'boolean', 'split', 'wrap', 'transform', 'deletepart', 'moveface', 'replaceface', 'offsetsurface', 'boundarysurface', 'moveboundary', 'ruledsurface', 'transform', 'mutualtrim', 'helix', '3dfitspline', 'projectedcurve', 'bridgingcurve', 'compositecurve', 'intersectioncurve', 'trimcurve', 'isocline', 'mateconnector', 'derived', 'transform', 'compositepart', 'sheetmetalmodel', 'flange', 'hem', 'tab', 'flange', 'makejoint', 'corner', 'bendrelief', 'finishsheetmetalmodel', 'frame', 'frametrim', 'gusset', 'endcap', 'cutlist', 'dfitspline']
    types_to_check = ['booleanBodies', 'boundarySurface', 'bridgingCurve', 'chamfer', 'circularPattern', 'compositeCurve', 'compositePart', 'cPlane', 'curvePattern', 'cutlist', 'deleteBodies', 'draft', 'enclose', 'endcap', 'extendSurface', 'externalThread', 'extrude', 'faceBlend', 'fill', 'fillet', 'fitSpline', 'frame', 'frameTrim', 'gusset', 'helix', 'importDerived', 'intersectionCurve', 'isocline', 'linearPattern', 'loft', 'mateConnector', 'mirror', 'moveFace', 'mutualTrim', 'newSketch', 'offsetSurface', 'projectCurves', 'replaceFace', 'revolve', 'rib', 'ruledSurface', 'sheetMetalBendRelief', 'sheetMetalCorner', 'sheetMetalEnd', 'sheetMetalFlange', 'sheetMetalHem', 'sheetMetalMakeJoint', 'sheetMetalStart', 'sheetMetalTab', 'shell', 'splitPart', 'sweep', 'thicken', 'transform', 'trimCurve', 'wrap']
    features = {}
    renamed_count = 0
    number_of_features = len(feature_list['features'])

    for feature in feature_list['features']:
        try:
            features[feature['featureType']] += 1
        except:
            features[feature['featureType']] = 1

        feature_name = re.sub('[0-9]','',feature['name']).replace(" ","").lower()
        
        # don't check hole, variable, and custom feature
        if feature['featureType'] in types_to_check:
            if feature_name not in default_features:
                renamed_count += 1

    features = dict(sorted(features.items(), key=lambda x:x[1], reverse=True)) # re-order feature count by descending number
    renamed = [number_of_features, renamed_count]

    return features, renamed

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

# Extract array of mates and mate relations, including offsets and limits
def as_get_mate_summary(feature_list):
    mates = {}
    mate_relations = {}
    summary_msg = {
        'mates': 0,
        'mate_relations': 0,
    }

    for feature in feature_list['features']:
        if feature['featureType'] == 'mate' or feature['featureType'] == 'mateRelation':
            params = feature['parameters']
            for param in params:
                paramId = param['parameterId']
                if 'value' in param:
                    val = param['value']
                    if paramId == 'relationType':
                        summary_msg['mate_relations'] += 1
                        if val not in mate_relations:
                            mate_relations.update({val : 1})
                        else:
                            mate_relations[val] += 1
                    elif paramId == 'mateType':
                        summary_msg['mates'] += 1
                        if val not in mates:
                            mates.update({val : 1})
                        else:
                            mates[val] += 1
    
    return mates, mate_relations, summary_msg

# Extract array of mates and mate relations, including offsets and limits
def as_get_mate_details(feature_list):
    mate_details = []
    detail_msg = {
        'renamed': 0,
        'offsets': 0,
        'limits': 0
    }
    feature_types = {'mate', 'mateRelation'}

    for feature in feature_list['features']:
        if feature['featureType'] in feature_types:
            mate = {'name': feature['name'], 'type': feature['featureType']}
            params = feature['parameters']
            limits = []
            offsets = []
            limitsEnabled = False
            offsetEnabled = False
            renamed = False

            for param in params:
                paramId = param['parameterId']

                if paramId  == 'limitsEnabled':
                    limitsEnabled = param['value']
                elif paramId == 'mateOffsetEnabled':
                    offsetEnabled = param['value']
                elif paramId.startswith('mateOffsetD'):
                    offsetArr = [param['parameterId'], param['expression']]
                    offsets.append(offsetArr)
                elif paramId.startswith('limit') and 'nullValue' in param:
                    if param['nullValue'] == "":
                        limitArr = [param['parameterId'], param['expression']]
                        limits.append(limitArr)
                elif paramId  == 'relationType' or paramId == 'mateType':
                    val = param['value']
                    renamed = val.lower().replace("_", "") != re.sub('[0-9]','',feature['name']).replace(" ","").lower()

            if limitsEnabled:
                detail_msg['limits'] += 1
                mate.update({'limits': limits})
            
            if offsetEnabled:
                detail_msg['offsets'] += 1
                mate.update({'offsets': offsets})
            
            if renamed:
                detail_msg['renamed'] += 1

            mate.update({'renamed': renamed})
            mate_details.append(mate)

    return mate_details, detail_msg

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