import os 
import requests
from datetime import timedelta, datetime
from typing import Union 
import json
import re
import base64

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
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADwAAAA8CAYAAAA6/NlyAAAACXBIWXMAABYlAAAWJQFJUiTwAAAGLmlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgOS4xLWMwMDEgNzkuMTQ2Mjg5OTc3NywgMjAyMy8wNi8yNS0yMzo1NzoxNCAgICAgICAgIj4gPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4gPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6ZXhpZj0iaHR0cDovL25zLmFkb2JlLmNvbS9leGlmLzEuMC8iIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIiB4bWxuczpwaG90b3Nob3A9Imh0dHA6Ly9ucy5hZG9iZS5jb20vcGhvdG9zaG9wLzEuMC8iIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvbW0vIiB4bWxuczpzdEV2dD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL3NUeXBlL1Jlc291cmNlRXZlbnQjIiBleGlmOlBpeGVsWERpbWVuc2lvbj0iMjQ2IiBleGlmOlBpeGVsWURpbWVuc2lvbj0iMjIyIiBleGlmOlVzZXJDb21tZW50PSJTY3JlZW5zaG90IiB4bXA6Q3JlYXRlRGF0ZT0iMjAyNC0wMS0xOVQwOToyODoyMy0wNTowMCIgeG1wOk1vZGlmeURhdGU9IjIwMjQtMDEtMTlUMDk6MzA6MTktMDU6MDAiIHhtcDpNZXRhZGF0YURhdGU9IjIwMjQtMDEtMTlUMDk6MzA6MTktMDU6MDAiIGRjOmZvcm1hdD0iaW1hZ2UvcG5nIiBwaG90b3Nob3A6Q29sb3JNb2RlPSIzIiB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOjdjYWY5YWRiLTFlZGUtNDkzMS1hYzI4LWI0NjYzOTVmNjExZSIgeG1wTU06RG9jdW1lbnRJRD0iYWRvYmU6ZG9jaWQ6cGhvdG9zaG9wOmYyYTkzZDc0LTY1N2ItMzM0MC05ZGVjLWNiMTI2MjI3ODNhNSIgeG1wTU06T3JpZ2luYWxEb2N1bWVudElEPSJ4bXAuZGlkOmU3YTFiYjEyLWUxMWYtNDc2MC05MzQwLWM0ZDRhNzY4OGEyYSI+IDx4bXBNTTpIaXN0b3J5PiA8cmRmOlNlcT4gPHJkZjpsaSBzdEV2dDphY3Rpb249InNhdmVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmU3YTFiYjEyLWUxMWYtNDc2MC05MzQwLWM0ZDRhNzY4OGEyYSIgc3RFdnQ6d2hlbj0iMjAyNC0wMS0xOVQwOTozMDoxOS0wNTowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDI1LjMgKE1hY2ludG9zaCkiIHN0RXZ0OmNoYW5nZWQ9Ii8iLz4gPHJkZjpsaSBzdEV2dDphY3Rpb249InNhdmVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjdjYWY5YWRiLTFlZGUtNDkzMS1hYzI4LWI0NjYzOTVmNjExZSIgc3RFdnQ6d2hlbj0iMjAyNC0wMS0xOVQwOTozMDoxOS0wNTowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDI1LjMgKE1hY2ludG9zaCkiIHN0RXZ0OmNoYW5nZWQ9Ii8iLz4gPC9yZGY6U2VxPiA8L3htcE1NOkhpc3Rvcnk+IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5kPSJyIj8+pe2p6QAACWhJREFUaIHlm8tvG1Ubh5+5j+2MXTtOSOumUmk3LQ2qaAgt9wpIK8GCil3Z8L+hhk2ACgmqLlBYcAmqkIBWoERNakJDG8d2k/gymRnPDIt+M2TiC76kl/D9dj6ec/w+c27v+55jwff9FWAc2OS/LREwZCD5v4LUEzTmsUl80gY8bsm7C+7fv89vv/2G4zhIkvQkbALA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" 
        #return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABmJLR0QA/wD/AP+gvaeTAAAAy0lEQVRIie2VXQ6CMBCEP7yDXkEjeA/x/icQgrQcAh9czKZ0qQgPRp1kk4ZZZvYnFPhjJi5ABfRvRgWUUwZLxIe4asEsMOhndmzhqbtZSdDExxh0EhacRBIt46V5oJDwEd4BuYQjscc90ATiJ8UfgFvEXPNNqotCKtEvF8HZS87wLAeOijeRTwhahsNoWmVi4pWRhLweqe4qCp1kLVUv3UX4VgtaX7IXbmsU0knuzuCz0SEwWIovvirqFTSrKbLkcZ8v+RecVyjyl3AHdAl3ObMLisAAAAAASUVORK5CYII="

def get_document_thumbnail(
    domain: str, did: str, sz: str, auth_token: str
) -> Any: 
    """Get a thumbnail image of the question for display 
    """
    response = requests.get(
        os.path.join(domain, "api/thumbnails/d/{}".format(did)), 
        headers={
            "Content-Type": "application/json", 
            "Accept": "application/vnd.onshape.v2+json;charset=UTF-8;qs=0.09", 
            "Authorization": "Bearer " + auth_token
        }
    )
    if response.ok:
        sizes = response.json()['sizes']
        href = ''
        for size in sizes:
            if size['size'] == sz:
                href = size['href']
        
        response2 = requests.get(
            href, 
            headers={
                "Accept": "image/png, text/plain", 
                "Authorization": "Bearer " + auth_token
            }
        )
            
        if response2.ok:
            image_base64 = base64.b64encode(response2.content).decode("utf-8")
            return "data:image/png;base64,"+image_base64
        else:
            return response2.content
    else:
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADwAAAA8CAYAAAA6/NlyAAAACXBIWXMAABYlAAAWJQFJUiTwAAAGLmlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgOS4xLWMwMDEgNzkuMTQ2Mjg5OTc3NywgMjAyMy8wNi8yNS0yMzo1NzoxNCAgICAgICAgIj4gPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4gPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6ZXhpZj0iaHR0cDovL25zLmFkb2JlLmNvbS9leGlmLzEuMC8iIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIiB4bWxuczpwaG90b3Nob3A9Imh0dHA6Ly9ucy5hZG9iZS5jb20vcGhvdG9zaG9wLzEuMC8iIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvbW0vIiB4bWxuczpzdEV2dD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL3NUeXBlL1Jlc291cmNlRXZlbnQjIiBleGlmOlBpeGVsWERpbWVuc2lvbj0iMjQ2IiBleGlmOlBpeGVsWURpbWVuc2lvbj0iMjIyIiBleGlmOlVzZXJDb21tZW50PSJTY3JlZW5zaG90IiB4bXA6Q3JlYXRlRGF0ZT0iMjAyNC0wMS0xOVQwOToyODoyMy0wNTowMCIgeG1wOk1vZGlmeURhdGU9IjIwMjQtMDEtMTlUMDk6MzA6MTktMDU6MDAiIHhtcDpNZXRhZGF0YURhdGU9IjIwMjQtMDEtMTlUMDk6MzA6MTktMDU6MDAiIGRjOmZvcm1hdD0iaW1hZ2UvcG5nIiBwaG90b3Nob3A6Q29sb3JNb2RlPSIzIiB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOjdjYWY5YWRiLTFlZGUtNDkzMS1hYzI4LWI0NjYzOTVmNjExZSIgeG1wTU06RG9jdW1lbnRJRD0iYWRvYmU6ZG9jaWQ6cGhvdG9zaG9wOmYyYTkzZDc0LTY1N2ItMzM0MC05ZGVjLWNiMTI2MjI3ODNhNSIgeG1wTU06T3JpZ2luYWxEb2N1bWVudElEPSJ4bXAuZGlkOmU3YTFiYjEyLWUxMWYtNDc2MC05MzQwLWM0ZDRhNzY4OGEyYSI+IDx4bXBNTTpIaXN0b3J5PiA8cmRmOlNlcT4gPHJkZjpsaSBzdEV2dDphY3Rpb249InNhdmVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmU3YTFiYjEyLWUxMWYtNDc2MC05MzQwLWM0ZDRhNzY4OGEyYSIgc3RFdnQ6d2hlbj0iMjAyNC0wMS0xOVQwOTozMDoxOS0wNTowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDI1LjMgKE1hY2ludG9zaCkiIHN0RXZ0OmNoYW5nZWQ9Ii8iLz4gPHJkZjpsaSBzdEV2dDphY3Rpb249InNhdmVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjdjYWY5YWRiLTFlZGUtNDkzMS1hYzI4LWI0NjYzOTVmNjExZSIgc3RFdnQ6d2hlbj0iMjAyNC0wMS0xOVQwOTozMDoxOS0wNTowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDI1LjMgKE1hY2ludG9zaCkiIHN0RXZ0OmNoYW5nZWQ9Ii8iLz4gPC9yZGY6U2VxPiA8L3htcE1NOkhpc3Rvcnk+IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5kPSJyIj8+pe2p6QAACWhJREFUaIHlm8tvG1Ubh5+5j+2MXTtOSOumUmk3LQ2qaAgt9wpIK8GCil3Z8L+hhk2ACgmqLlBYcAmqkIBWoERNakJDG8d2k/gymRnPDIt+M2TiC76kl/D9dj6ec/w+c27v+55jwff9FWAc2OS/LREwZCD5v4LUEzTmsUl80gY8bsm7C+7fv89vv/2G4zhIkvQkbALA8zwURWFsbIxnn30WTdP2pN0I8NLSErOzszQaDWS56V08VgmCgO/7eJ5HJpPhzJkzTE5ODtxuhOr7778HYHR0lGq1iud5CIIw8I/0qqB34/E4AKZp8tVXX7G4uMilS5eIxWJ9tx0CW5ZFo9FAURQkSeLdd98lFovhOM7gBD0qFouxurrK/Pw8iqKgKAqjo6Pk83lmZma4fPly39CRHhYEIRzOR48eRVGUPQHoV77v47ousViMWq1GJpOhVCpx5coVPvzww76gw1U6GLqCIOB5Hr7v753lfSiwoVqtcuzYMd566y3K5TKGYVAul5mZmcE0zZ7bfeq3Jd/3qdVqnDhxggsXLoTQxWKRmZkZ6vV6T+099cDwsLcBzpw5w/T0NOVymWQySalU4pNPPukJel8A79SLL77IO++8w8bGBqlUimKx2BP0vgMGmJqa4tVXX2VtbY10Oh1CdzOn9yUwwGuvvcbZs2cpFAohdDcL2b4FBpienmZqaopCoUAmk6FYLHLlypWO0PsaGJqhS6VSx57e98DwEHpycpK1tTWGh4dZW1vjs88+a/nsvgDuxp+/cOEC58+fp1qtks1mWVpaYm5urum5JxsSdSFd19nY2GB+fh7XdVt6gJ7nkUwmEUURXdfxPI90Os3vv//OSy+9FAYh8BQD+75Po9EgFotRKpW4c+dOx572PA9N0zAMA0EQ0HWdUqlEPp/n5MmT4XNPNbDjOAiCgCRJGIbRVT3LspBlGVVVEQSBtbW1/QE8OjrK5cuXEQShp5g8kUhw+/ZtvvvuOwAajUbk+z0B9jyPcrmMZVlsb2+HQyoej3PgwIG+2tQ0jfHx8b7qZrPZ0P/e/bIGAr579y43b95kfX2dSqWC4zi4rguAoiioqkoqlSKXy3H69GmSyeS/tLg36hTe9gXsOA5ff/01v/76K67rEo/HURQFXdfDN+p5Hq7rcu/ePZaXl/npp5+Ynp7mueee659kD9QzsOu6zM7Osri4yDPPPIMkSS3fpiRJSJKEoigYhkG9Xufzzz/HsixeeOGFPTG+H/XseHzzzTfcvn2bQ4cOIYpiBDbIMgbzZ2d5MJ+vXbtGPp8f2PB+1RPw/fv3+fnnnxkeHo6AiqJIrVZjc3MT27axLIsHDx5g2zai+PAnfN9H0zRUVeXbb7/dW4oe1NOQXlhYwLIskslkCCyKIltbW2SzWV555RXS6TSe5/HHH3/www8/UK/XicVi+L6P7/skk0lWV1dZWlri2LFjjwSqk7oG9n2fP//8k3g8Hunder2OYRh88MEHJBKJsDybzZJKpfjiiy8i+e0gwb6yshIC+77fdq/1PI9SqYRpmoiiSCqV6toJaaWugdfX13nw4EHTkYdpmkxOTkZgAx0/fpwjR46wsrLC0NBQWK4oCuvr6+Hn69evs7q6SjweZ2tri5dffpmJiQnm5ubI5/NUKpVwu1NVlWw2y9TUFEePHn10wPV6HcdxUFU1LPM8D1VVOXz4cNt6uVyO5eXlSJmqqlSr1TAHXi6X+euvvzAMg0ajwfz8PD/++COFQoF4PI6maeGLdl2XO3fusLi4yPvvv8/ExERPwF0vWuVymUajERl6ruui63pHhyKbzTZ7O7JMrVZja2sLeBgRJRKJcCW3bRvTNBkZGSEejyNJUuhiyrLM8PAwqVSK69evUywWHw2wZVlN+20Qoei63raeqqrIshzZqoJkf6tjnOBcKehRx3GoVCpNK34sFsO27abR82/qGthxnJbAqqpGhvluaZqGLMtNdYNjlJZGiSKNRoNSqYQsyxw/fpxkMolt25H6kiRRrVa7RQB6XKVblf1bJCNJUpODArTtYQDbtpFlmbfffptTp06h6zpLS0tcvXqVRCIR9nQ7uzqp6x7u96ypU72dhu9UvV7n8OHDTE5OhtMlFou1PLNu10bb3+z2QVmWm3oz2FO7Uau6vahdeqdXdQ3c6vqDKIrYth2ZW7u1vb0dZi52ShCEjsexj+r0smtgTdOajBZFMQz628k0TRzHiQy9YLFr5aw8anUNnE6nm0JBSZIwTZONjY229YrFYlNvBfv3IFcX+lXXwIlEAkVRIvtpMKTv3r3btt69e/eaFhvHcUgkEk/k4kzXwKOjo2QymabhOzQ0xK1btyiXy011FhYWwoAjkCAIWJbFwYMHBzC7s3ZOvYFyWuPj42EgEAxTXdepVCp8+umnnD17lnQ6jSAI5PN5bty4gSzLkangeR6iKJLL5QblCtuDf7KTsixHMpW7p1NPwBMTE/zyyy9YlhV6V57nhSmcL7/8Ek3TwpyyYRioqhrJIG5ubpLL5fYkFj5w4AD5fJ6PP/44BAsu5iQSCba2tpqcm56AM5kMp0+fZm5ujkOHDkV6Tdf18JgD/nEIdsJub2/TaDR48803BwINJEkStm1TqVTCoev7PrIsh774QD0M8Prrr1MsFrl58yYjIyMoitKU7tktQRCoVqtUq1Xee++9juFkL/I8D0mSImtEoD1N0166dInh4WFu3LiBbdvouh7u0zvftOd5bG9vY1kW6XSaixcvcuLEiab2TNOkVquFL6tWq2FZVuQZ13Wp1WrhGtBOQbTVLoLrC1gQBN544w1OnjzJrVu3KBQKbG5u4jhOGDNLkoSu64yNjXHkyBGef/75tkaMjIxg23bYU4ZhkE6nI89omkYul0PTtI7AgTMURFF7evIwMjLC+fPnAahUKpimieu6YaA+NDTUMVYOND093VS2e0gePHiQjz76qCu7lpeXuXr1aujR7dSe7fyGYQyUXNutR3WpdV/cABhEu0dKE3A3Qf3Trk72h0M6OCIJshO2baOqasfQ72mUqqqRcHT3sU8ILEkSrusiyzKO4zA7O/t4Ld0jCYKA67oMDQ1RKBSa4vgQWFEUTp06xbVr18IE25O6ET+IAk8r+M/G7uPZyCp97tw5HMdhYWEhTL7tRwWXys+dO8fY2FjkO8H3/Q12/WfJdd2mpPt+k6IoLe1vuQ8Hh9n/RcnAFg97+P/ir3h/A1vkYlMdIZ7XAAAAAElFTkSuQmCC" 

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
        os.path.join(domain, "api/globaltreenodes/magic/15?limit=50"), 
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
    domain: str, classid: str, offset: str, auth_token: str
) -> Any: 

    response = requests.get(
        os.path.join(
            domain, 
            "api/classrooms/{}/assignments?offset={}&limit=20".format(classid, offset)
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