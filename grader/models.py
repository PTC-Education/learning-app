"""
Development Guide

Initial model only contains AuthUser

"""

import io 
import os 
import requests
import base64
from datetime import datetime, timedelta
from typing import Optional, Iterable, Union, Tuple, Dict, Any

import numpy as np 
import numpy.typing as npt 
from matplotlib.figure import Figure 
from matplotlib.backends.backend_agg import FigureCanvasAgg

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy 
from django.core.exceptions import ObjectDoesNotExist, ValidationError


#################### Create your models here ####################
class ElementType(models.TextChoices): 
    # The corresponding values will be used for API calls 
    NA = "N/A", gettext_lazy("Not Applicable")
    PARTSTUDIO = "partstudios", gettext_lazy("Part Studio")
    ASSEMBLY = "assemblies", gettext_lazy("Assembly")
    ALL = "all", gettext_lazy("All Types")

class AuthUser(models.Model): 
    """
    Every unique Onshape user who has used this app has one and only one row entry in this table. 
    
    It stores informations including: 
    
    - User authentication tokens for API calls 
    - User working Onshape environment to locate resources 
    """
    os_user_id = models.CharField(max_length=30, default=None, unique=True)
    
    # Onshape working environment of the user 
    os_domain = models.URLField(
        max_length=100, null=True, 
        help_text="https://cad.onshape.com for non-enterprise Onshape accounts"
    )
    did = models.CharField(max_length=30, null=True, help_text="Onshape document ID")
    wv = models.CharField(max_length=30, null=True, help_text="Onshape workspace or version")
    wvid = models.CharField(max_length=30, null=True, help_text="Onshape workspace or version ID")
    eid = models.CharField(max_length=30, null=True, help_text="Onshape element ID")
    etype = models.CharField(
        max_length=40, choices=ElementType.choices, null=True, 
        help_text="Onshape element type"
    )

    # Tokens and expiry tracking from Onshape OAuth 
    access_token = models.CharField(max_length=100, null=True)
    refresh_token = models.CharField(max_length=100, null=True)
    expires_at = models.DateTimeField(null=True)
    
    def refresh_oauth_token(self) -> None: 
        """
        When a user's ``access_token`` is expired or about to expire, tracked by the user's ``expires_at``, this function can be called to use the ``refresh_token`` to exchange for a new ``access_token``.  
        """
        response = requests.post(
            os.path.join(
                os.environ['OAUTH_URL'], 
                "oauth/token"
            ) + "?grant_type=refresh_token&refresh_token={}&client_id={}&client_secret={}".format(
                self.refresh_token.replace('=', '%3D'), 
                os.environ['OAUTH_CLIENT_ID'].replace('=', '%3D'), 
                os.environ['OAUTH_CLIENT_SECRET'].replace('=', '%3D')
            ), 
            headers={'Content-Type': "application/x-www-form-urlencoded"}
        )
        response = response.json() 

        self.access_token = response['access_token']
        self.refresh_token = response['refresh_token']
        self.expires_at = timezone.now() + timedelta(seconds=response['expires_in'])
        self.save() 
        return None 

    def __str__(self) -> str:
        return self.os_user_id

#################### Helper API calls ####################
