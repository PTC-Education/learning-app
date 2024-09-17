import os 
import requests
from datetime import timedelta, datetime
from math import floor, log10
from html import unescape
from typing import Union 
import json
import re

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse 
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, HttpResponseNotFound, JsonResponse
from django.utils import timezone 
from django.utils.datastructures import MultiValueDictKeyError
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import register

from .models import * 
from .api import *

import traceback

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
        # Refresh token
        user.refresh_oauth_token() 
            
    except ObjectDoesNotExist: 
        # Create a new user 
        try:
            user = AuthUser.objects.get(os_user_id=user_id).delete()
        except:
            pass
        user = AuthUser(os_user_id=user_id)
    
    try:
        user.os_domain = request.GET.get('server')
        user.did = request.GET.get('did')
        user.wv = request.GET.get('wvm')
        user.wvid = request.GET.get('wvmid')
        user.eid = request.GET.get('eid')
        user.etype = request.GET.get('etype')
        user.save() 
    except:
        user.etype = "grant"
        user.save() 
        pass
    
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
    try:
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
    except:
        return HttpResponse(
            "User authentication failed!\nError getting access token for user."
        )
    
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
    elif user.etype == "grant":
        return HttpResponse("App successfully authorized! Please return to Onshape and open the CAD Checker app from the right panel.")
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

def home(request: HttpRequest, os_user_id=None):
    """ 
    The home page that can be accessed either logged in in-app or as a standard URL without login information. 
    
    The page documents more extensive user instructions, some technical tips, and a documentation on all data collections from the users. 

    **Arguments:**
        
    **Template:**

    :template:`grader/home.html`
    """
    context = {"user": None} 
    if os_user_id: 
        curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
        context['user'] = curr_user
    return render(request, "grader/home.html", context=context)

def url_input_page(request: HttpRequest, os_user_id: str , user_type:str):
    """ 

   This function will open the url_input.html customized for single url and multiurl+upload csv function for student and educators use. 


    **Arguments:**
        
    - ``os_user_id``: identify the :model:`grader.AuthUser` model with the user's login information.
    - ``user_type:str``: type of user , options are student, educator, and scioly

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

def check_model(request: HttpRequest, os_user_id: str):
    """ 
    This function is renders the best practice checker page

    **Arguments:**
        
    - ``os_user_id``: identify the :model:`grader.AuthUser` model with the user's login information.

    **Template:**

    :template:`grader/doc_info_checker.html`
    """
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    context={
        "user": curr_user,       
    }

    return render(request, "grader/checker.html", context=context)

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
    image = None
    elements_info = get_element_info(curr_user.os_domain, curr_user.did, "w", doc_wid, "", auth_token=curr_user.access_token)
    for element in elements_info:
        if element['elementType'] == "PARTSTUDIO":
            #image = get_shaded_views(curr_user.os_domain, curr_user.did, "w", doc_wid, element['id'], "partstudios", auth_token=curr_user.access_token)
            element_dict = {'etype': 'partstudios', 'id': element['id'], 'name': element['name'], 'image': image}
            element_list.append(element_dict)
        elif element['elementType'] == "ASSEMBLY":
            #image = get_shaded_views(curr_user.os_domain, curr_user.did, "w", doc_wid, element['id'], "assemblies", auth_token=curr_user.access_token)
            element_dict = {'etype': 'assemblies', 'id': element['id'], 'name': element['name'], 'image': image}
            element_list.append(element_dict)
    context={
        "user": curr_user, 
        "doc_wid": doc_wid,
        "element_list":element_list,
       
    }

    return render(request, "grader/doc_info_checker.html", context=context)

def doc_info_checker_image_update(request: HttpRequest, os_user_id: str):
    '''
    This functions dynamically updates the thumbnails in the list of elements on doc_info_checker page
     **Arguments:**
      - ``os_user_id``: identify the :model:`grader.AuthUser` model with the user's login information and reviewer status. 
    '''
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token()
    doc_wid = request.GET.get("doc_wid")
    eid = request.GET.get("eid")
    etype = request.GET.get("etype")
    image = get_shaded_views(curr_user.os_domain, curr_user.did, "w", doc_wid, eid, etype, auth_token=curr_user.access_token)
   
    context={ 
        "image": image,
    }


    return HttpResponse(
        json.dumps(context),
        content_type="application/json"
    )

def doc_info_checker_results_update(request: HttpRequest, os_user_id: str):
    '''
    This functions dynamically updates the results for selected element on doc_info_checker page
     **Arguments:**
      - ``os_user_id``: identify the :model:`grader.AuthUser` model with the user's login information and reviewer status. 
    '''
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token()

    doc_wid = request.GET.get("doc_wid")
    element = request.GET.get('elements')

    try:
        etype = element.split(" ")[0]
        eid = element.split(" ")[1]
    except:
        pass

    error_message = ""
    mates_summary = {}
    count_summary = {}
    features_details = {}
    mate_details = {}

    if element:
        # Get feature list of model the user currently has opened
        feature_list = get_feature_list(
                curr_user.os_domain, etype, curr_user.did, "w", doc_wid, eid, auth_token=curr_user.access_token
            )
        if not feature_list: # API error 
            error_message = "An unexpected error has occurred. Please check internet connection and try relaunching the app (CT0 ERROR)."

        if etype == "partstudios":
            features_details = ps_feature_list_helper(feature_list)

        elif etype == "assemblies":
            # check_message += as_feature_list_helper(feature_list)
            mates_summary = as_get_mate_summary(feature_list)
            mate_details = as_get_mate_details(feature_list)
    
    if element:
        # Get parts list of model the user currently has opened
        if etype == "partstudios":
            part_list = get_part_list(
                    curr_user.os_domain, curr_user.did, "w", doc_wid, eid, auth_token=curr_user.access_token
                )
            if not part_list: # API error 
                error_message = "An unexpected error has occurred. Please check internet connection and try relaunching the app (CT1 P ERROR)."

            count_summary = part_list_helper(part_list)

            sketch_info = get_sketch_info(
                curr_user.os_domain, curr_user.did, "w", doc_wid, eid, auth_token=curr_user.access_token
            )


        elif etype == "assemblies":
            assembly_def = get_assembly_definition(
                    curr_user.os_domain, curr_user.did, "w", doc_wid, eid, auth_token=curr_user.access_token
                )
            if not assembly_def: # API error 
                error_message = "An unexpected error has occurred. Please check internet connection and try relaunching the app (CT1 A ERROR) ."

            count_summary = instance_list_helper(assembly_def)
            sketch_info = None

    ## count_summary contents depends on etype - 
    #   For part studios the summary contains information about parts
    #   {
    #    "title": "Part Checking",  
    #    "part_count": part_count, 
    #    "part_rename_count": part_rename_count, 
    #    "part_material_count":part_material_count, 
    #    "part_surface_count": surface_count
    #   }
    #   For assemblies the summary contains  information about instances
    #  {
    #   "title":"Instance Checking", 
    #   "instance_count": instance_count, 
    #   "part_instance_count": part_instance_count, 
    #   "assemby_instance_count":assemby_instance_count
    #   }

    ## features_details contains information about features in a part studio -
    #   {
    #   "features": features, 
    #   "renamed": renamed , 
    #   "error_count": error_count
    #   }
    #   - features is an array of dict {"feature name X ", number of times  feature X is used}
    #   - renamed is an array of  [number_of_features, renamed_count]
    #   - error_count is total number of errors in the features
    #
    ## mates_summary -
    #   {
    #   "mates": mates,
    #   "mate_relations" : mate_relations,
    #   "summary_msg" : summary_msg,
    #   "error_count" :error_count
    #   }
    #   - mates is an array of dict  {"mate name M ", number of mates M}
    #   - mate_relations is a array of dict {"mate relations R", number of mate relations R}
    #   - "summary_msg" = {"mates" : number of mates  "mate_relations" : number of mate relations}
    #   - error_count is total number of errors in the mates
    #
    ## mate_details contains information about mate featurs and instances
    #   {
    #     "mate_details": mate_details, 
    #     "detail_msg": detail_msg
    #   }
            
    # - detail_msg is a dict  contained  {'renamed': 0, 'offsets': 0, 'limits': 0 }
    # - mate_details is an array of details about mates
    #        mate names
    #        mate type
    #        mate limit
    #        offsets
    #        renamed (boolean)

    context={
        "etype" : etype,
        "error_message": error_message,
        "count_summary": count_summary, 
        "features_details": features_details,
        "sketch_details": sketch_info,
        "mates_summary": mates_summary,
        "mate_details": mate_details,
    }
  
    return HttpResponse(
        json.dumps(context),
        content_type="application/json"
    )

def list_classes(request: HttpRequest, os_user_id: str,  user_type:str):
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
    error_message=False

    #get information about classrooms created by the user
    try:
        classinfo = get_class_list(curr_user.os_domain,auth_token=curr_user.access_token) 
        items = classinfo["items"]
        for item in items:
            if(item["resourceType"]=="classroom"):
                class_id = item["id"]
                class_name = item["name"].replace("/", "%2F")
                number_of_assignment = item["numberOfAssignments"]
                number_of_members = item["numberOfMembers"]
                classes.append([class_id, class_name, number_of_assignment, number_of_members]) # Append all classroom id, name,  number of assignments and number of members
    except:
       error_message = "We encountered an issue. Please check your internet connection."
    
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
            "user_type": user_type,
            "classes":classes,
             "error_message" : error_message
        }
    return render(
        request, "grader/c_and_a.html", 
        context=context
    )

@register.filter
def unslash(value):
    return value.replace("%2F", "/")

def list_assignments(request: HttpRequest, os_user_id: str, user_type:str, class_id:str , class_name:str):
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
    offset = 0
    next_assignments = ""
    try:
        while next_assignments != None:
            assignment_list = get_assignment_list(curr_user.os_domain, class_id, offset, auth_token = curr_user.access_token)
            items = assignment_list["items"]
            next_assignments = assignment_list['next']
            for item in items:
                assignment_id = item["id"]
                assignment_name = item["name"].replace("/", "%2F")
                status = item["stateName"]
                in_progress = item["numberOfSubmissionsInProgress"]
                submitted = item["numberOfSubmissionsSubmitted"]
                not_submitted = item["numberOfSubmissionsNotStarted"]
                description = item["description"]
                description = (description[:400] + '...') if len(description) > 400 else description
                published_date = item["publishedDate"]
                assignments.append([assignment_id, assignment_name, status, submitted, not_submitted, in_progress, published_date, description,])
            offset += 20

    except:
        print("Error in assignment") #need better error message here

    context={
            "user": curr_user, 
            "user_type": user_type,
            "page": "assignments",
            "assignments": assignments,
            "class_name": class_name,
            "class_id":class_id
        }
    return render(
        request, "grader/c_and_a.html", 
        context=context
    )

def assignment_doc_info(request: HttpRequest, os_user_id: str): 
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    type_dict = {"partstudios":"PARTSTUDIO", "assemblies":"ASSEMBLY"}

    # Refresh token if needed 
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 

    tabs = []
    wv = "v"
    did = request.GET.get('did')
    wvid = request.GET.get('vid')
    eid = request.GET.get('eid')
    
    if wvid == None or eid == None:
        versions = get_versions(curr_user.os_domain, did, auth_token=curr_user.access_token)
        wvid = versions[len(versions)-1]['id']

    # get tab info for ALL of the tabs
    element_info = get_element_info(curr_user.os_domain, did, wv, wvid, "", auth_token=curr_user.access_token)

    correct_etypes = []

    for element in element_info:
        if element['elementType'] == type_dict[curr_user.etype]:
            correct_etypes.append([element['elementType'],element['name'],element['id']])
    
    for e in correct_etypes:
        tab_type = e[0]
        tab_name = e[1]
        eid = e[2]
        tab_image = get_shaded_views(curr_user.os_domain, did, wv, wvid, eid, curr_user.etype, auth_token=curr_user.access_token)
        tab_url = curr_user.os_domain + "/documents/" + did + "/" + wv + "/" + wvid + "/e/" + eid
        tab = {'tab_name': tab_name, 'tab_image': tab_image, 'tab_type': tab_type, 'tab_url': tab_url}
        tabs.append(tab)

    # send back all tabs (tab name, tab thumb, tab type, tab url) of correct element type
    return JsonResponse({'tabs': tabs})

def list_members(request: HttpRequest, os_user_id: str,  user_type:str, class_id:str, class_name:str, assignment_id:str, assignment_name:str):
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
    error_message=False

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
            member_name = submission["memberName"].replace("'", "").replace('"', '')
            state_name = submission["stateName"]

            # require_user_action = True 
            number_of_attempts = 0
            # tab_names_and_ids =[]  
            
            #If the document is submitted
            if (state_name == "Submitted"):
                doc_name = submission["documents"][0]["metadata"]["dn"].replace("'", "").replace('"', '')
                url = submission["documents"][0]["viewRef"]
                number_of_attempts = submission["numberOfAttempts"]
                # splitted_url = url.split("/documents/")[1].split("/")
                # did = splitted_url[0]
                
                # if(len(splitted_url)==1): # url has a document id only
                #     doc_info = get_doc_info(curr_user.os_domain, did, auth_token=curr_user.access_token)
                #     wv = "w"
                #     wvid = doc_info["defaultWorkspace"]["id"]
                # else:
                #     wv      = splitted_url[1]
                #     wvid    = splitted_url[2]

                # if user_type == "scioly":
                #     require_user_action = False  #dont require action from user
                #     tab_name = "scioly"
                #     tab_image = get_document_thumbnail(curr_user.os_domain, did, '70x40', auth_token=curr_user.access_token) 
                #     tab_names_and_ids.append([url, tab_name, tab_image])  # bundle the  url ,  name and image each tab
                #     submitted_student_works.append([member_id, member_name, number_of_attempts, doc_name, url, tab_names_and_ids])

                # else:
                #     if not url.find("/e/") < 0: # if there is an element id in the url of the submitted document
                #         # tab_id = splitted_url[4].split("?")[0]
                #         # tab_info = get_element_info(curr_user.os_domain, did, wv, wvid, tab_id, auth_token=curr_user.access_token)
                #         # tab_type = tab_info[0]["elementType"]

                #         #if the type of eid in the url is the same as the current user etype
                #         if( tab_type == type_dict[curr_user.etype]):
                #             require_user_action = False  #dont require action from user
                #             tab_name = tab_info[0]["name"]
                #             tab_image   = get_shaded_views(curr_user.os_domain, did, wv, wvid, tab_id, curr_user.etype, auth_token=curr_user.access_token) 
                #             tab_names_and_ids.append([url, tab_name, tab_image])  # bundle the  url ,  name and image each tab
                #             submitted_student_works.append([member_id, member_name, number_of_attempts, doc_name, url, tab_names_and_ids])
                #         else:
                #             require_user_action = True #require action from user
                                        
                #     else:  # if there is no element id in the url of the submitted document
                #         require_user_action = True #require action from user
                submitted_student_works.append([member_id, member_name, number_of_attempts, doc_name, url])   
                # if require_user_action:
                #     tab_infos = get_element_info(curr_user.os_domain, did, wv, wvid, " ", auth_token=curr_user.access_token) #get all tab info
                    
                #     for tab_info in tab_infos:
                #         tab_type = tab_info["elementType"]
                #         if( tab_type == type_dict[curr_user.etype]): # Only get information of the tabs that have same element type as the user document
                #             tab_name    = tab_info["name"]
                #             tab_id      = tab_info["id"]
                #             tab_image   = get_shaded_views(curr_user.os_domain, did, wv, wvid, tab_id, curr_user.etype, auth_token=curr_user.access_token)
                #             tab_url = curr_user.os_domain + "/documents/" + did + "/" + wv + "/" + wvid + "/e/" + tab_id
                #             tab_names_and_ids.append([tab_url, tab_name, tab_image])  # bundle the  url ,  name and image each tab
                    

                #     url = tab_names_and_ids[0][0] # update the url to point to the first tab of the document  
                #     if(len(tab_names_and_ids) == 1): #If there is only one tab
                #         submitted_student_works.append([member_id, member_name, number_of_attempts, doc_name, url, tab_names_and_ids])
                #     else:
                #         action_required_student_works.append([member_id, member_name, number_of_attempts, doc_name, url, tab_names_and_ids])

            #If the document is in progress
            else:
                doc_name = "Not included"
                url = ""
                if submission["documents"]: # if the user has started a document
                    doc_name = submission["documents"][0]["metadata"]["dn"].replace("'", "").replace('"', '')
                    url = submission["documents"][0]["viewRef"]
                    
                inprogress_student_works.append([member_id, member_name, state_name, doc_name, url])
    except:
         error_message = "We encountered an issue. Please check your internet connection. "
    context={
            "user": curr_user, 
            "user_type": user_type,
            "etype": type_dict[curr_user.etype],
            "page": "submissions",
            "submitted_student_works": submitted_student_works,
            # "action_required_student_works": action_required_student_works,
            "inprogress_student_works": inprogress_student_works,
            "class_name": class_name,
            "class_id": class_id,
            "assignment_name": assignment_name,
            "error_message" : error_message
        }
    return render(
        request, "grader/c_and_a.html", 
        context = context
    )

def grade_model(request: HttpRequest, os_user_id: str): 
    """ 
    When a user submits, urls to compare with the model are collected and returned to the basic results page. 
    The page renders for the number of urls returned. 
    
    **Arguments:**
    
    - ``os_user_id``: the unique ID linked to the user's :model:`grader.AuthUser` profile
    
    **Template:**
    
    :template:`grader/basic_results.html`
    """
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)

    #grab reference urls , possibly in a csv format, from the generic_grader.html
    cs_ref_urls = request.POST.getlist('ref_url')
    #parse the csv file into array of urls
    ref_urls = convert_cs_to_array(cs_ref_urls) 
    
    ref_url_ids = []
    for url in ref_urls:
        ref = get_ref_url_ids(url)
        ref_url_ids.append(ref)

    context={
        "user": curr_user, 
        "ref_urls": ref_url_ids
    }
    return render(
        request, "grader/basic_results.html", 
        context=context
    )

def user_data_on_result_page(request: HttpRequest, os_user_id: str): 
    """ 
    This function returns the user mass properties and document details. It is called from a AJAX function and it returns a JSON 
    string containing error message, if any, and user properties.    
    
    **Arguments:**
    
    - ``os_user_id``: the unique ID linked to the user's :model:`grader.AuthUser` profile
    
    **Template:**
    
    :template:`grader/basic_results.html`
    """
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    props = [] 

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

    error_msg = None
    # Set list of props - different for each etype
    try:
        if curr_user.etype == "partstudios":
            # Get parts list for part studio and create dictionary of IDs to names
            part_list = get_part_list(curr_user.os_domain, curr_user.did, curr_user.wv, curr_user.wvid, curr_user.eid, curr_user.access_token)
            partId_to_name = {} 
            
            for item in part_list: 
                if 'material' in item:
                    material = item['material']['displayName']
                else: 
                    material = "No material"
                partId_to_name[item['partId']] = [item['name'], material]
            

            mass_props = ignore_surfaces(mass_props)

            # partstudios props = [[mass, vol, periphery, principalInertia, partName],[...]] sorted by vol decending
            props = make_props(mass_props, partId_to_name)

        elif curr_user.etype == "assemblies":
            # assemblies props = [mass, vol, periphery, principalInertia]
            props = make_props(mass_props, None)

        # Get all additional info from the reference document
        url = curr_user.os_domain + "/documents/" + curr_user.did + "/"+ curr_user.wv + "/" + curr_user.wvid + "/e/" + curr_user.eid
        image = get_shaded_views(curr_user.os_domain, curr_user.did, curr_user.wv, curr_user.wvid, curr_user.eid, curr_user.etype, auth_token=curr_user.access_token)
        element_info = get_element_info(curr_user.os_domain, curr_user.did, curr_user.wv, curr_user.wvid, curr_user.eid, auth_token=curr_user.access_token)
        element_name = element_info[0]["name"]
        doc_info = get_doc_info(curr_user.os_domain, curr_user.did, auth_token=curr_user.access_token)
        user_name = doc_info["createdBy"]["name"]
        doc_name = doc_info['name']
        doc_time = elapsed_time(doc_info['defaultWorkspace']['createdAt'],doc_info['defaultWorkspace']['modifiedAt'])
        
        # Insert first element of array 
        props.insert(0,[user_name, doc_name, element_name, doc_time, image, url])

    except:
        # If anything above failed, add url to the fairled URL list
        error_msg = "Something went wrong."
    
    context = {
        'etype': curr_user.etype,
        'error_msg': error_msg,
        'user_props': props, 
    }

    return HttpResponse(
        json.dumps(context),
        content_type="application/json"
    )

def update_result_page(request: HttpRequest, os_user_id: str): 
    """ 
    This function returns mass properties and results for one document at a time. It is called from an AJAX function
    There are three checks to make sure it returns correct information.
    1. Check for document access
        - on failure > returns with error message conveying inaccessible document
    2. Check for element type
        - on failure > returns with error message conveying mismatched type
    3. Check for successful property retrieval 
        - on failure > returns with error message converying something was wrong

    **Arguments:**
    
    - ``os_user_id``: the unique ID linked to the user's :model:`grader.AuthUser` profile
    
    **Template:**
    
    :template:`grader/basic_results.html`
    """
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)
    domain = request.GET.get('domain')
    did = request.GET.get('did')
    wv = request.GET.get('wv')
    wvid = request.GET.get('wvid')
    eid = request.GET.get('eid')
    url = domain + "/documents/" + did + "/"+ wv + "/" + wvid + "/e/" + eid

    props = [] 
    failed_url = "None"
    error_msg = None

    element_info = get_element_info(domain, did, wv, wvid, eid, auth_token=curr_user.access_token)
    # Get all additional info from the reference document
    try:
        elementType = element_info[0]['elementType']
        element_name = element_info[0]["name"]
        doc_info = get_doc_info(domain, did, auth_token=curr_user.access_token)
        user_name = doc_info["createdBy"]["name"]
        doc_name = doc_info['name']
        doc_time = elapsed_time(doc_info['defaultWorkspace']['createdAt'],doc_info['defaultWorkspace']['modifiedAt'])
        image = get_shaded_views(domain, did, wv, wvid, eid, curr_user.etype, auth_token=curr_user.access_token)
        
    except:
        error_msg = "Couldn't access the document. Make sure it is shared with you."
        return HttpResponse(
            json.dumps({'failed_url': url, 'error_msg': error_msg}),
            content_type="application/json"
            )
 
    # Refresh token if needed 
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 

    # Throw a proper error when the element type doesn't match    
    type_dict = {"partstudios":"PARTSTUDIO", "assemblies":"ASSEMBLY"}
    if( not elementType == type_dict[curr_user.etype]):
        error_msg = 'The element types mismatched.'
        return HttpResponse(
            json.dumps({'failed_url': url, 'error_msg': error_msg}),
            content_type="application/json"
            )

    # Get mass props of model the user currently has opened
    mass_props = get_mass_props(
            curr_user.os_domain, did, wv, wvid, eid, curr_user.etype, 
            massAsGroup=False, auth_token=curr_user.access_token
        )
    
    if not mass_props: # API error 
        error_msg = "Couldn't access the mass properties."
        return HttpResponse(
            json.dumps({'failed_url': url, 'error_msg': error_msg }),
            content_type="application/json"
        )

    # Set list of props - different for each etype
    try:
        if curr_user.etype == "partstudios":
            # Get parts list for part studio and create dictionary of IDs to names
            part_list = get_part_list(curr_user.os_domain, did, wv, wvid, eid, curr_user.access_token)
            partId_to_name = {}     

            for item in part_list: 
                if 'material' in item:
                    material = item['material']['displayName']
                else: 
                    material = "No material"
                partId_to_name[item['partId']] = [item['name'], material]
  
            mass_props = ignore_surfaces(mass_props)

            # partstudios props = [[mass, vol, periphery, principalInertia, partName],[...]] sorted by vol decending
            props = make_props(mass_props, partId_to_name)

            #if the props returns -1, it means there were no parts in the part studio
            if(props == -1):
                error_msg = "No parts were detected in the Part Studio."
                return HttpResponse(
                    json.dumps({'failed_url': url, 'error_msg': error_msg }),
                    content_type="application/json"
                )
            
        elif curr_user.etype == "assemblies":
            # assemblies props = [mass, vol, periphery, principalInertia]
            props = make_props(mass_props, None)
            if(props == -1):
                error_msg = "No instances were detected in the Assembly."
                return HttpResponse(
                    json.dumps({'failed_url': url, 'error_msg': error_msg }),
                    content_type="application/json"
                )
        
    except:
        # If anything above failed, add url to the fairled URL list
        failed_url = url
        error_msg = 'Unknown error has occured. Click the link to investigate the document.'
    
    props.insert(0,[user_name, doc_name, element_name, doc_time, image, url])
    context={ 
        "etype": curr_user.etype,
        "failed_url": failed_url,
        'error_msg': error_msg,
        "ref_props": props, 
    }

    return HttpResponse(
        json.dumps(context),
        content_type="application/json"
    )

def microversions_checker(request: HttpRequest, os_user_id: str):
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)

    # Refresh token if needed 
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 

    context={
        "user": curr_user,
    }

    return render(
        request, "grader/microversions_checker.html",
        context=context
    )

def update_html(request: HttpRequest, os_user_id: str, wm: str, wmid: str): 
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)

    # Refresh token if needed 
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 

    doc_info = get_doc_info(curr_user.os_domain, curr_user.did, auth_token=curr_user.access_token)
    # wm = "w"
    if wm == 'w':
        wmid = doc_info["defaultWorkspace"]["id"]

    context={
        "user": curr_user,
    }

    latest_microversions = get_microversions(curr_user.os_domain, curr_user.did, wm, wmid, auth_token=curr_user.access_token)
    next_microversion = ""
    # s = "<table class='item_summary'>"
    # s += "<thead><tr><th>Date</th><th>Description</th><th>User Name</th></tr></thead>"
    # s += "<tbody>"
    usernames = {}
    oldest_microversion = ""
    newest_microversion = latest_microversions[0]['date'].split('.')[0]
    for microversion in latest_microversions:
        username = microversion['username']
        # s += "<tr>"
        # date_arr = microversion['date'].split('.')
        # s += "<td>" + date_arr[0].replace('T', ' ') + "</td>"
        # s += "<td>" + microversion['description'] + "</td>"
        # s += "<td>" + username + "</td>"
        # s += "</tr>"
        next_microversion = microversion['nextMicroversionId']
        if username != "System":
            if username not in usernames:
                usernames.update({username : 1})
            else:
                usernames[username] += 1
        date_arr = microversion['date'].split('.')
        oldest_microversion = date_arr[0]
    # s += "</tbody>"
    # s += "</table>"
    s = "<table class='item_summary'>"
    s += "<thead><tr><th>Document Edits</th><th>Count</th></tr></thead>"
    s += "<tbody>"
    totaledits = 0
    for key, value in usernames.items():
        s += "<tr><td>" + str(key) + "</td><td>" + str(value) + "</td></tr>"
        totaledits += value
    s += "<tr><td><strong>Total</strong></td><td><span id='total-edits'>" + str(totaledits) + "</span></td></tr>"
    s += "</tbody>"
    s += "</table>"
    updated_html = s
    usernames_json = json.dumps(usernames)
    # Return the updated HTML
    return JsonResponse({'updated_html': updated_html, 'next_microversion': next_microversion, 'oldest_microversion': oldest_microversion, 'newest_microversion': newest_microversion, 'usernames_json' : usernames_json})

def grade_scioly(request: HttpRequest, os_user_id: str): 
    """ 
    When a user submits, urls to compare with the model are collected and returned to the basic results page. 
    The page renders for the number of urls returned. 
    
    **Arguments:**
    
    - ``os_user_id``: the unique ID linked to the user's :model:`grader.AuthUser` profile
    
    **Template:**
    
    :template:`grader/basic_results.html`
    """
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)

    #grab reference urls , possibly in a csv format, from the generic_grader.html
    cs_ref_urls = request.GET.getlist('ref_url')
    #parse the csv file into array of urls
    ref_urls = convert_cs_to_array(cs_ref_urls) 

    # Get all the relevant elements of the model that the user currently has open (PS and Assemblies)
    user_elems = get_element_info(curr_user.os_domain, curr_user.did, curr_user.wv, curr_user.wvid, "", auth_token=curr_user.access_token)
    type_dict = {"PARTSTUDIO":"partstudios", "ASSEMBLY":"assemblies"}
    
    if not user_elems: # API error 
        return HttpResponse("An unexpected error has occurred. Please check internet connection and try relaunching the app.")
    
    user_props = [] # a 3D array that lists all the PS and Assemblies in a document along with their corresponding mass properties
    # first indexing is an array of the element labels and the corresponding mass property [eType, name, [mass/center of mass]]
    # second indexing of the mass property is [mass] for part studios or [COM_xaxis, COM_yaxis, COM_zaxis] for assemblies
    key_answers = {}
    elems_to_grade = []
    for elem in user_elems:
        if (elem["elementType"] == "PARTSTUDIO" or elem["elementType"] == "ASSEMBLY") and "source" not in elem["name"].lower():
            elems_to_grade.append(elem["name"])
            mass_props = get_mass_props(
                    curr_user.os_domain, curr_user.did, curr_user.wv, curr_user.wvid, elem["id"], type_dict[elem["elementType"]], 
                    massAsGroup=True, auth_token=curr_user.access_token
                )
            elem_mass_prop = [] #initialize
            if elem["elementType"] == "PARTSTUDIO":
                if mass_props["bodies"] == {} or mass_props["bodies"]["-all-"]["hasMass"] == False: # checks if the PS is empty or material is not assigned
                    return HttpResponse("The Answer Key's Part Studio(s) are empty or do not have a material assigned. Please check the current document and regrade.")
                else:
                    elem_mass_prop = sig_figs(mass_props["bodies"]["-all-"]["mass"][0], 3)
                    #key_answers.append(elem_mass_prop)
                    key_answers[elem['name']] = elem_mass_prop
            else: #elem["elementType"] == "ASSEMBLY"
                if mass_props["hasMass"] == False: #checks if the assembly is empty or if ALL parts do not have material assigned.
                    return HttpResponse("The Answer Key's Assembly is empty or does not have a materials assigned. Please check the current document and regrade.")
                else:
                    elem_mass_prop = [str(sig_figs(val, 3)) for val in mass_props["centroid"][0:3]] # this array has 3 values: first three are COM best fit for xyz.  round to 4 decimal places
                    if "%g" % float(elem_mass_prop[0]) == '0' or "%g" % float(elem_mass_prop[1]) == '0' or "%g" % float(elem_mass_prop[2]) == '0': #checks the HIGHLY IMPROBABLE case that the COM of the answer key is 0 on any axis.
                        return HttpResponse("The Answer Key's Assembly Center of Mass has a zero in it. Please check the current document and regrade.")
                    #key_answers.append(elem_mass_prop)
                    key_answers[elem['name']] = elem_mass_prop
                    elem_mass_prop = ', '.join(elem_mass_prop)
                    
            elem_props = [elem["elementType"], elem["name"], elem_mass_prop, 20.00] # last item in array is the full points for that part/assembly.
            user_props.append(elem_props)
            
    # Get info about the document the user currently has opened
    user_doc_info = get_doc_info(curr_user.os_domain, curr_user.did, auth_token=curr_user.access_token)
    user_doc_name = user_doc_info['name']
    user_user_name = user_doc_info["createdBy"]["name"]
    user_doc_time = elapsed_time(user_doc_info['defaultWorkspace']['createdAt'],user_doc_info['defaultWorkspace']['modifiedAt'])
    totalpoints = 20.00 * float((len(user_props))) # This will be the max score, since its the total points of the answer key

    user_url = curr_user.os_domain + "/documents/" + curr_user.did + "/"+ curr_user.wv + "/" + curr_user.wvid + "/e/" + curr_user.eid

    # Append user related information along with mass properties
    user_props.insert(0, [user_doc_name, user_user_name, user_doc_time, user_url, totalpoints])
    context={
        "user": curr_user, 
        "user_props": user_props,
        "key_answers": key_answers,
        "ref_urls": ref_urls,
        "elems_to_grade": elems_to_grade 
    }
    return render(
        request, "grader/scioly_results.html", 
        context=context
    )

def grade_scioly_results(request: HttpRequest, os_user_id: str):
    '''the purpose of this is to grade the science olympiad cases.
    **Arguments:**
    
    - ``os_user_id``: the unique ID linked to the user's :model:`grader.AuthUser` profile
    - ``ref_urls``: the reference element for the model to be compared to
    
    **Template:**
    
    :template:`grader/results.html`'''
    curr_user = get_object_or_404(AuthUser, os_user_id=os_user_id)

    # Refresh token if needed 
    if curr_user.expires_at < timezone.now() + timedelta(minutes=20): 
        curr_user.refresh_oauth_token() 
        
    url = request.GET.get('ref_url') 
    key_string = request.GET.get('key_answers').replace('&#x27;','')
    key_answers = string_to_json(key_string)
    elems_to_grade = request.GET.get('elems_to_grade').replace('&#x27;','')[1:-1]
    #answerArray = string_to_array(key_answers)
    toGradeArray = elems_to_grade.split(', ')
    ref_url = get_scioly_ref_url_ids(url)

    ## Initialize arrays for ref docs
    ref_props = [] # 3D array - each 2D array corresponds to one URL
    # First element of each 2D array is an array of doc info [user_name, doc_name, element_name, doc_time, image, url]
    # Rest is model props [[mass, vol, periphery, principalInertia, partName],[...]] (without partName for assemblies)
    failed_url = "None" # Array of all URLs that we failed to get info from

    type_dict = {"PARTSTUDIO":"partstudios", "ASSEMBLY":"assemblies"}
    # Get info and mass props for ref urls
    try:
        ref_elems = get_element_info(curr_user.os_domain, ref_url['did'], ref_url['wv'], ref_url['wvid'], "", auth_token=curr_user.access_token) # get all the elems from the URL
        ref_props=[] # initialize empty array of ref props
        ref_names=[]
        for elem in ref_elems:
            ref_names.append(elem['name'])

        # First, we chek that the student has all of the necessary elements
        toGradeArray = [unescape(elem).replace("\"", "").replace("'", "") for elem in toGradeArray]
        key_answers = {unescape(key).replace("\"", "").replace("'", ""): value for key, value in key_answers.items()}
        ref_names = [elem.replace("\"", "").replace("'", "") for elem in ref_names]
        for name in toGradeArray:
            if name not in ref_names:
                raise Exception("Missing element")     
        elemcount = 1
        totalpoints = 0

        # Next, we grade only those elements
        for elem in ref_elems:
            elem_name = elem['name'].replace("\"", "").replace("'", "")
            if (elem["elementType"] == "PARTSTUDIO" or elem["elementType"] == "ASSEMBLY") and elem_name in toGradeArray:
                mass_props = get_mass_props(
                        curr_user.os_domain, ref_url['did'], ref_url['wv'], ref_url['wvid'], elem['id'], type_dict[elem["elementType"]], 
                        massAsGroup=True, auth_token=curr_user.access_token
                    )
                elem_mass_prop = 0 #initialize
                points = 0
                if elem["elementType"] == "PARTSTUDIO":
                    
                    if mass_props["bodies"] == {} or mass_props["bodies"]["-all-"]["hasMass"] == False: # checks if the PS is empty or material is not assigned
                        elem_mass_prop = 0
                    else:
                        elem_mass_prop = sig_figs(mass_props["bodies"]["-all-"]["mass"][0], 3) #round to 4 decimal places
                    ans = sig_figs(key_answers[elem_name], 3)
                    points = 20 - 100*abs((elem_mass_prop - ans)/ans)
                    if points < 0:
                        points = 0
                    points = round(points, 2)
                    
                else: #elem["elementType"] == "ASSEMBLY"
                    if mass_props["hasMass"] == False: #checks if the assembly is empty or if ALL parts do not have material assigned.
                        elem_mass_prop = [0,0,0]
                    else:
                        elem_mass_array = [sig_figs(float(string),3) for string in mass_props["centroid"][0:3]] # this array has 3 values: first three are COM best fit for xyz. 
                        elem_mass_prop = ', '.join(map(str, elem_mass_array))
                    ans = key_answers[elem_name]
                    ans = [sig_figs(i, 3) for i in ans]
                    points = 20 - 100*(((1/3)*abs((elem_mass_array[0] - ans[0])/ans[0])) + ((1/3)*abs((elem_mass_array[1] - ans[1])/ans[1])) + ((1/3)*abs((elem_mass_array[2] - ans[2])/ans[2])))
                    if points < 0:
                        points = 0
                    points = round(points, 2)
                    
                ref_elem_props =  [elem["elementType"], elem["name"], elem_mass_prop, points]
                ref_props.append(ref_elem_props)
                totalpoints = totalpoints + points
                elemcount = elemcount + 1

        # Get all additional info from the reference document
        totalpoints = round(totalpoints, 2)
        image = get_document_thumbnail(curr_user.os_domain, ref_url['did'], '300x300', auth_token=curr_user.access_token)
        element_info = get_element_info(curr_user.os_domain, ref_url['did'], ref_url['wv'], ref_url['wvid'], "", auth_token=curr_user.access_token)
        element_name = element_info[0]["name"]
        ref_doc_info = get_doc_info(curr_user.os_domain, ref_url['did'], auth_token=curr_user.access_token)
        user_name = ref_doc_info["createdBy"]["name"]
        doc_name = ref_doc_info['name']
        doc_time = elapsed_time(ref_doc_info['defaultWorkspace']['createdAt'],ref_doc_info['defaultWorkspace']['modifiedAt'])
        # Insert first element of array 
        ref_props.insert(0,[doc_name,user_name, element_name, doc_time, image, url, totalpoints])
    except Exception as error:
        # If anything above failed, add url to the fairled URL list
        print(f"Error: {error}")
        traceback.print_exc()
        failed_url = ref_url
            
    context={
        "failed_url": failed_url,
        "ref_props": ref_props
    }
    
    return HttpResponse(
        json.dumps(context),
        content_type="application/json"
    )

#################### Other helper functions ####################
def sig_figs(x, precision):
    x = float(x)
    return round(x, -int(floor(log10(abs(x)))) + (precision - 1))

def elapsed_time(start_time: str, stop_time: str):
    createdAt = datetime.strptime(start_time.replace("T"," ").split("+")[0],'%Y-%m-%d %H:%M:%S.%f')
    modifiedAt = datetime.strptime(stop_time.replace("T"," ").split("+")[0],'%Y-%m-%d %H:%M:%S.%f')
    delta = modifiedAt - createdAt
    # start_time looks like this: 2024-01-10T22:31:30.577+00:00
    time_formatted = str(delta).split(".")[0].split(":")
    if "days" in time_formatted[0]:
        return time_formatted[0].split(" days,")[0] + "D" + time_formatted[0].split(" days,")[1] + "H" + time_formatted[1] + "M" + time_formatted[2] + "S"
    else:
        return time_formatted[0] + "h " + time_formatted[1] + "m " + time_formatted[2] + "s "

def get_ref_url_ids(ref_url: str):
    try:
        ref = dict()
        ref['domain'] = ref_url.split("/documents/")[0]
        ref['did'] = ref_url.split("documents/")[1].split("/")[0]
        ref['wv'] = ref_url.split("documents/")[1].split("/")[1].split("/")[0]
        ref['wvid'] = ref_url.split("/e/")[0].split("/")[-1]
        ref['eid'] = ref_url.split("/e/")[1].split("?")[0]
        return ref
    except:
        return None
    
def get_scioly_ref_url_ids(ref_url: str):
    try:
        ref = dict()
        ref['domain'] = ref_url.split("/documents/")[0]
        ref['did'] = ref_url.split("documents/")[1].split("/")[0]
        ref['wv'] = ref_url.split("documents/")[1].split("/")[1].split("/")[0]
        ref['wvid'] = ref_url.split("/e/")[0].split("/")[-1]
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
        if(mass_props['bodies']):
            # partstudios user_props = [[mass, vol, periphery, principalInertia, partName, centroid],[...]] sorted by vol decending
            try:
                user_props = [
                    [prt['mass'][0] for prt in mass_props['bodies'].values()], 
                    [prt['volume'][0] for prt in mass_props['bodies'].values()], 
                    [prt['periphery'][0] for prt in mass_props['bodies'].values()], 
                    [prt['principalInertia'][0] for prt in mass_props['bodies'].values()], 
                    [partId_to_name[prt] for prt in mass_props['bodies'].keys()],
                    [prt['centroid'][0:3] for prt in mass_props['bodies'].values()],
                ]
                user_props = sorted([
                    [
                        user_props[0][i], user_props[1][i], 
                        user_props[2][i], user_props[3][i], 
                        user_props[4][i], user_props[5][i]
                    ] 
                    for i in range(len(user_props[0]))
                ], key=lambda x : x[1])
                return user_props
            except:
                return None
        else:
            return -1 #indicates no parts in the part studio
    else:
        if('mass' in mass_props):
            # assemblies ref_props = [mass, vol, periphery, principalInertia,centroid]
            try: 
                ref_props = [[
                    mass_props['mass'][0], 
                    mass_props['volume'][0], 
                    mass_props['periphery'][0],
                    mass_props['principalInertia'][0],
                    mass_props['centroid'][0:3]
                ]]
                return ref_props
            except:
                return None
        else:
            return -1 #indicates no instances in the assembly


# Extract useful information from featurelist for partstudios
def ps_feature_list_helper(feature_list):
    default_features = ['sketch', 'extrude', 'revolve', 'sweep', 'loft', 'thicken', 'fill', 'enclose', 'fillet', 'faceblend', 
                        'chamfer', 'draft', 'shell', 'rib', 'externalthread', 'curvepattern', 'linearpattern', 'circularpattern', 
                        'plane', 'mirror', 'boolean', 'split', 'wrap', 'transform', 'deletepart', 'moveface', 'replaceface', 'offsetsurface', 
                        'boundarysurface', 'moveboundary', 'ruledsurface', 'transform', 'mutualtrim', 'helix', '3dfitspline', 
                        'projectedcurve', 'bridgingcurve', 'compositecurve', 'intersectioncurve', 'trimcurve', 'isocline', 'mateconnector', 
                        'derived', 'transform', 'compositepart', 'sheetmetalmodel', 'flange', 'hem', 'tab', 'flange', 'makejoint', 'corner', 
                        'bendrelief', 'finishsheetmetalmodel', 'frame', 'frametrim', 'gusset', 'endcap', 'cutlist', 'dfitspline', 'decal']
    
    # types_to_check is every feature type except holes and variables.  it also filters out custom features
    types_to_check = ['booleanBodies', 'boundarySurface', 'bridgingCurve', 'chamfer', 'circularPattern', 'compositeCurve', 'compositePart', 
                      'cPlane', 'curvePattern', 'cutlist', 'deleteBodies', 'draft', 'decal', 'enclose', 'endcap', 'extendSurface', 'externalThread', 
                      'extrude', 'faceBlend', 'fill', 'fillet', 'fitSpline', 'frame', 'frameTrim', 'gusset', 'helix', 'importDerived', 
                      'intersectionCurve', 'isocline', 'linearPattern', 'loft', 'mateConnector', 'mirror', 'moveFace', 'mutualTrim', 'newSketch', 
                      'offsetSurface', 'projectCurves', 'replaceFace', 'revolve', 'rib', 'ruledSurface', 'sheetMetalBendRelief', 'sheetMetalCorner', 
                      'sheetMetalEnd', 'sheetMetalFlange', 'sheetMetalHem', 'sheetMetalMakeJoint', 'sheetMetalStart', 'sheetMetalTab', 
                      'shell', 'splitPart', 'sweep', 'thicken', 'transform', 'trimCurve', 'wrap']
    
    keyMap = {'booleanBodies' : 'Boolean', 'boundarySurface' : 'Boundary surface', 'bridgingCurve' : 'Bridging curve', 'chamfer' : 'Chamfer', 
              'circularPattern' : 'Circular pattern', 'compositeCurve' : 'Composite curve', 'compositePart' : 'Composite part', 'cPlane' : 'Plane', 
              'curvePattern' : 'Curve pattern', 'cutlist' : 'Cut list', 'deleteBodies' : 'Delete part', 'draft' : 'Draft', 'decal' : 'Decal', 
              'enclose' : 'Enclose', 'endcap' : 'End cap', 'extendSurface' : 'Move boundary', 'externalThread' : 'External thread', 'extrude' : 'Extrude', 
              'faceBlend' : 'Face blend', 'fill' : 'Fill', 'fillet' : 'Fillet', 'fitSpline' : 'Fit spline', 'frame' : 'Frame', 'frameTrim' : 'Frame trim', 
              'gusset' : 'Gusset', 'helix' : 'Helix', 'importDerived' : 'Derived', 'intersectionCurve' : 'Intersection curve', 'isocline' : 'Isocline', 
              'linearPattern' : 'Linear pattern', 'loft' : 'Loft', 'mateConnector' : 'Mate connector', 'mirror' : 'Mirror', 'moveFace' : 'Move face', 
              'mutualTrim' : 'Mutual trim', 'newSketch' : 'Sketch', 'offsetSurface' : 'Offset surface', 'projectCurves' : 'Projected curve', 
              'replaceFace' : 'Replace face', 'revolve' : 'Revolve', 'rib' : 'Rib', 'ruledSurface' : 'Ruled surface', 'sheetMetalBendRelief' : 
              'Sheet metal bend relief', 'sheetMetalCorner' : 'Sheet metal corner', 'sheetMetalEnd' : 'Finish sheet metal model', 'sheetMetalFlange' : 
              'Sheet metal flange', 'sheetMetalHem' : 'Sheet metal hem', 'sheetMetalMakeJoint' : 'Sheet metal make joint', 'sheetMetalStart' : 
              'Sheet metal model', 'sheetMetalTab' : 'Sheet metal tab', 'shell' : 'Shell', 'splitPart' : 'Split part', 'sweep' : 'Sweep', 'thicken' : 
              'Thicken', 'transform' : 'Transform', 'trimCurve' : 'Trim curve', 'wrap' : 'Wrap'}
    
    features = {}
    renamed_count = 0
    number_of_features = len(feature_list['features'])
    featureIds =[] #store all feature ids
    for feature in feature_list['features']:
        try:
            features[feature['featureType']] += 1
        except:
            features[feature['featureType']] = 1
        featureIds.append(feature['featureId'])

        feature_name = re.sub('[0-9]','',feature['name']).replace(" ","").lower()
        
        # don't check hole, variable, and custom feature
        if feature['featureType'] in types_to_check:
            if feature_name not in default_features:
                renamed_count += 1
    error_count = 0

    for featureId in featureIds:
        if(feature_list['featureStates'][featureId]['featureStatus']) == "ERROR" or (feature_list['featureStates'][featureId]['featureStatus']) == "WARNING":
            error_count +=1

    features = dict(sorted(features.items(), key=lambda x:x[1], reverse=True)) # re-order feature count by descending number
    prettyFeatures = {keyMap.get(k, k): v for k, v in features.items()}
    renamed = [number_of_features, renamed_count]

    return {"features": prettyFeatures, "renamed": renamed , "error_count": error_count}

# Extract useful information from featurelist for assemblies
def as_feature_list_helper(feature_list):
    mate_count = 0
    mate_relation_count = 0

    for feature in feature_list['features']:
       
        if feature['featureType'] == "mate":
            mate_count += 1
        elif feature['featureType'] == "mateRelation":
            mate_relation_count += 1

    return {"mate_count":mate_count, "mate_relation_count": mate_relation_count}


# Extract array of mates and mate relations, including offsets and limits
def as_get_mate_summary(feature_list):
    mates = {}
    mate_relations = {}
    summary_msg = {
        'mates': 0,
        'mate_relations': 0,
        'groups': 0
    }
    featureIds =[] #store all feature ids

    for feature in feature_list['features']:
        featureIds.append(feature['featureId'])
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
        elif  feature['featureType'] == 'mateGroup':
            summary_msg['groups'] += 1
    
    mates_cap = {}
    mate_relations_cap = {}

    for key, value in mates.items():
        new_key = key.capitalize().replace('_', ' ')
        mates_cap[new_key] = value
    
    for key, value in mate_relations.items():
        new_key = key.capitalize().replace('_', ' ')
        mate_relations_cap[new_key] = value

    error_count = 0
    for featureId in featureIds:
        if(feature_list['featureStates'][featureId]['featureStatus']) == "ERROR" or (feature_list['featureStates'][featureId]['featureStatus']) == "WARNING":
            error_count +=1
    return {"mates": mates_cap, "mate_relations": mate_relations_cap, "summary_msg": summary_msg , "error_count" : error_count}

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
        elif  feature['featureType'] == 'mateGroup':
            renamed = False
            if re.sub('[0-9]', '', feature['name'].lower().replace(' ', '')) != "group":
                renamed = True
                detail_msg['renamed'] += 1
            mate = {'name' : feature['name'], 'type' : 'group', 'limits': [], 'offsets': [], 'renamed': renamed}
            mate_details.append(mate)

    return {"mate_details": mate_details, "detail_msg": detail_msg}

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

    return {"title": "Part Checking", "part_count": part_count, "part_rename_count": part_rename_count, "part_material_count":part_material_count, "part_surface_count": surface_count}

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


    return {"title":"Instance Checking", "instance_count": instance_count, "part_instance_count": part_instance_count, "assemby_instance_count":assemby_instance_count}

# Turn URL string into multidimensional array
def string_to_array(s):
    newStr = ''
    semiColon = False
    for i in s:
        if i == '[' or i == ']':
            semiColon = not semiColon
        else:
            if semiColon:
                if i == ',':
                    newStr += ';'
                else:
                    newStr += i
            else:
                newStr += i
            
    newStr = newStr[1:]
    newStr = newStr[:-1]

    myArr = newStr.split('; ')
    for i, elem in enumerate(myArr):
        if ',' in elem:
            strArray = elem.split(', ')
            myArr[i] = [float(string) for string in strArray]
        else:
            myArr[i] = float(elem)

    return myArr

def string_to_json(s):
    s = s.replace(':', '":')
    s = s.replace('{', '{"')

    inArray = False
    skipNext = False
    s_fixed = ""
    for i in range(0, len(s)):
        c = s[i]
        if c == "[":
            inArray = True
        elif c == "]":
            inArray = False
        if c == "," and not inArray:
            s_fixed += ', "'
        else:
            s_fixed += c
    s_fixed = s_fixed.replace('" ', '"')

    j = json.loads(s_fixed)
    return j