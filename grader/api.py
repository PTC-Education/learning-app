import os 
import requests
from datetime import timedelta, datetime
from typing import Union 
import json
import re

from .models import * 

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
    domain: str, did: str, wv: str, wvid: str, eid: str, auth_token: str
) -> Any: 
    """ Get all parts in an element
    """
    response = requests.get(
        os.path.join(domain, "api/parts/d/{}/{}/{}/e/{}".format(did, wv, wvid, eid)), 
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
    domain: str, did: str, wv: str, wvid: str, eid: str, auth_token: str
) -> Any: 
    """ Get all parts in an element
    """
    response = requests.get(
        os.path.join(domain, "api/assemblies/d/{}/{}/{}/e/{}".format(did, wv, wvid, eid)), 
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
    domain: str, did: str, wv: str, wvid: str, eid: str, auth_token: str
) -> Any: 
    """ Get the blob content of the given element
    """
    response = requests.get(
        os.path.join(domain, "api/blobelements/d/{}/{}/{}/e/{}".format(did,wv,wvid,eid)), 
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
    domain: str, did: str, wv:str, wvid:str, eid:str, etype:str,  auth_token: str
) -> Any: 
    """Get a thumbnail image of the question for display 
    """
    response = requests.get(
        os.path.join(domain, "api/{}/d/{}/{}/{}/e/{}/shadedviews".format(etype, did, wv, wvid, eid)), 
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


def get_assignment_list(
    domain: str, classid: str, auth_token: str
) -> Any: 

    response = requests.get(
        os.path.join(
            domain, 
            "api/classrooms/{}/assignments".format(classid)
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

def get_submission_list(
    domain: str, classid:str , assignmentid: str, auth_token: str
) -> Any: 
    response = requests.get(
        os.path.join(
            domain, 
            "api/classrooms/{}/assignments/{}".format(classid, assignmentid)
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
    domain: str, did: str, wv: str, wvid: str, eid: str, auth_token: str, thumbnails="false"
) -> Any: 
    """ Get information about element 
    """
    response = requests.get(
        os.path.join(domain, "api/documents/d/{}/{}/{}/elements?elementId={}&withThumbnails={}".format(did, wv, wvid, eid, thumbnails)), 
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

def get_microversions(
    domain: str, did: str, wm: str, wmid: str, auth_token: str
) -> Any: 
    """ Get microversions
    """
    response = requests.get(
        os.path.join(domain, "api/documents/d/{}/{}/{}/documenthistory".format(did, wm, wmid)), 
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