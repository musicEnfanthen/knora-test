import copy
import json
import requests
from datetime import datetime
from pprint import pprint
from typing import List, Set, Dict, Tuple, Optional

import time


class Converter:

    def __init__(self):
        self.selection_mapping: Dict[str, str] = {}
        self.selection_node_mapping: Dict[str, str] = {}
        self.hlist_node_mapping: Dict[str, str] = {}
        self.hlist_mapping: Dict[str, str] = {}


        # Retrieving the necessary informations from Webpages.
        self.salsahJson = requests.get('https://www.salsah.org/api/projects').json()
        self.r = requests.get(
            'https://raw.githubusercontent.com/dhlab-basel/dasch-ark-resolver-data/master/data/shortcodes.csv')
        self.salsahVocabularies = requests.get('https://www.salsah.org/api/vocabularies').json()

        # Testing stuff
        # self.req = requests.get('https://www.salsah.org/api/resourcetypes/')
        # result = self.req.json()
        # pprint(result)

    # ==================================================================================================================
    # Function that fills the shortname as well as the longname into the empty ontology. Uses https://www.salsah.org/api/projects for that
    def fillShortLongName(self, project):
        tmpOnto["project"]["shortname"] = project["shortname"]
        tmpOnto["project"]["longname"] = project["longname"]

    # ==================================================================================================================
    # Fill in the project id's to the corrisponging projects. Using https://raw.githubusercontent.com/dhlab-basel/dasch-ark-resolver-data/master/data/shortcodes.csv
    def fillId(self, project):
        lines = salsahJson.r.text.split('\n')
        for line in lines:
            parts = line.split(',')
            if len(parts) > 1 and parts[1] == project["shortname"]:
                tmpOnto["project"]["shortcode"] = parts[0]
                # print('Found Knora project shortcode "{}" for "{}"!'.format(tmpOnto["project"]["shortcode"], parts[1]))

    # ==================================================================================================================
    # Fill the description - if present - into the empty ontology
    def fillDesc(self, project):
        for vocabulary in salsahJson.salsahVocabularies["vocabularies"]:
            if vocabulary["description"] and vocabulary["shortname"].lower() == project["shortname"].lower():
                tmpOnto["project"]["descriptions"] = vocabulary["description"]

    # ==================================================================================================================
    # Fill in the vocabulary name and label
    def fillVocName(self, projects):
        for vocabulary in salsahJson.salsahVocabularies["vocabularies"]:
            if vocabulary["project_id"] == projects["id"]:
                tmpOnto["project"]["ontologies"][0]["name"] = vocabulary["shortname"]
                tmpOnto["project"]["ontologies"][0]["label"] = vocabulary["longname"]

    # ==================================================================================================================
    # Function responsible to get the keywords of the corresponding project
    def fetchKeywords(self, project):
        for vocabulary in salsahJson.salsahVocabularies["vocabularies"]:
            if vocabulary["project_id"] == projects["id"]:
                # fetch project_info
                req = requests.get('https://www.salsah.org/api/projects/{}?lang=all'.format(vocabulary["shortname"]))
                result = req.json()

                if 'project_info' in result.keys():
                    project_info = result['project_info']
                    if project_info['keywords'] is not None:
                        tmpOnto["project"]["keywords"] = list(
                            map(lambda a: a.strip(), project_info['keywords'].split(',')))
                    else:
                        tmpOnto["project"]["keywords"] = [result['project_info']['shortname']]
                else:
                    continue

    # ==================================================================================================================
    # Function that fetches the lists for a correspinding project
    def fetchLists(self, project):
        for vocabulary in salsahJson.salsahVocabularies["vocabularies"]:
            if vocabulary["project_id"] == projects["id"]:
                payload: dict = {
                    'vocabulary': vocabulary["shortname"],
                    'lang': 'all'
                }
                # fetch selections
                req = requests.get('http://salsah.org/api/selections/', params=payload)
                selection_results = req.json()
                selections = selection_results['selections']

                # Let's make an empty list for the lists:
                selections_container = []

                for selection in selections:
                    self.selection_mapping[selection['id']] = selection['name']
                    root = {
                        'name': selection['name'],
                        'labels': dict(map(lambda a: (a['shortname'], a['label']), selection['label']))
                    }
                    if selection.get('description') is not None:
                        root['comments'] = dict(
                            map(lambda a: (a['shortname'], a['description']), selection['description']))
                    payload = {'lang': 'all'}
                    req_nodes = requests.get('http://salsah.org/api/selections/' + selection['id'], params=payload)
                    result_nodes = req_nodes.json()

                    self.selection_node_mapping.update(
                        dict(map(lambda a: (a['id'], a['name']), result_nodes['selection'])))
                    root['nodes'] = list(map(lambda a: {
                        'name': 'S_' + a['id'],
                        'labels': a['label']
                    }, result_nodes['selection']))
                    selections_container.append(root)

                    # pprint(selections_container)
                    # time.sleep(15)

                #
                # now we get the hierarchical lists (hlists)
                #
                payload = {
                    'vocabulary': vocabulary["shortname"],
                    'lang': 'all'
                }
                # fetch hlists
                req = requests.get('http://salsah.org/api/hlists', params=payload)
                hlist_results = req.json()

                self.hlist_node_mapping.update(dict(map(lambda a: (a['id'], a['name']), hlist_results['hlists'])))

                hlists = hlist_results['hlists']

                # pprint(selections_container)
                # time.sleep(15)

                #
                # this is a helper function for easy recursion
                #
                def process_children(children: list) -> list:
                    newnodes = []
                    for node in children:
                        self.hlist_node_mapping[node['id']] = node['name']
                        newnode = {
                            'name': 'H_' + node['id'],
                            'labels': dict(map(lambda a: (a['shortname'], a['label']), node['label']))
                        }
                        if node.get('children') is not None:
                            newnode['nodes'] = process_children(node['children'])
                        newnodes.append(newnode)
                    return newnodes

                for hlist in hlists:
                    root = {
                        'name': hlist['name'],
                        'labels': dict(map(lambda a: (a['shortname'], a['label']), hlist['label']))
                    }
                    self.hlist_mapping[hlist['id']] = hlist['name']
                    if hlist.get('description') is not None:
                        root['comments'] = dict(
                            map(lambda a: (a['shortname'], a['description']), hlist['description']))
                    payload = {'lang': 'all'}
                    req_nodes = requests.get('http://salsah.org/api/hlists/' + hlist['id'], params=payload)
                    result_nodes = req_nodes.json()

                    root['nodes'] = process_children(result_nodes['hlist'])
                    selections_container.append(root)

                tmpOnto["project"]["lists"] = selections_container
                # pprint(selections_container)
                # pprint('==================================================================================================================')
                # pprint('==================================================================================================================')

    # ==================================================================================================================
    # Function that fetches all the resources that correspond to a vocabulary/ontology
    def fetchResources(self, project):

        superMap = {
            "movie": "MovingImageRepresentation",
            "object": "Resource",
            "image": "StillImageRepresentation"
        }

        for vocabulary in salsahJson.salsahVocabularies["vocabularies"]:
            if project["id"] == vocabulary["project_id"]:
                payload: dict = {
                    'vocabulary': vocabulary["shortname"],
                    'lang': 'all'
                }
                # fetch resourcetypes
                req = requests.get('http://salsah.org/api/resourcetypes/', params=payload)
                resourcetype_result = req.json()
                resourcetypes = resourcetype_result["resourcetypes"]

                # Here we type in the "name"
                for resourcetype in resourcetypes:
                    tmpOnto["project"]["ontologies"][0]["resources"].append({
                        "name": resourcetype["label"][0]["label"],
                        "super": "",
                        "labels": {},
                        "comments": {},
                        "cardinalities": []
                    })

                    # fill in the labels
                    for label in resourcetype["label"]:
                        tmpOnto["project"]["ontologies"][0]["resources"][-1]["labels"].update(
                            {label["shortname"]: label["label"]})

                    # fetch restype_info
                    req = requests.get('https://salsah.org/api/resourcetypes/{}?lang=all'.format(resourcetype["id"]))
                    resType = req.json()
                    resTypeInfo = resType["restype_info"]

                    # fill in the description of the resources as comments
                    if resTypeInfo["description"] is not None and isinstance(resTypeInfo["description"], list):
                        for descriptionId in resTypeInfo["description"]:
                            tmpOnto["project"]["ontologies"][0]["resources"][-1]["comments"].update({
                                descriptionId["shortname"]: descriptionId["description"]
                            })

                    # fill in super attributes of the resource. Default is "Resource"
                    if resTypeInfo["class"] is not None and resTypeInfo["class"] in superMap:
                        tmpOnto["project"]["ontologies"][0]["resources"][-1]["super"] = superMap[resTypeInfo["class"]]
                    else:
                        # TODO: check if correct?
                        # tmpOnto["project"]["ontologies"][0]["resources"][-1]["super"] = superMap["object"]
                        pprint(resTypeInfo["class"])
                        #     exit()

                    # fill in the cardinalities with propname and cardinality of occurences
                    for propertyId in resTypeInfo["properties"]:
                        # check vocabulary of propertyId
                        propertyName = ""
                        if propertyId["vocabulary"].lower() is not None and propertyId["vocabulary"].lower() == project["shortname"].lower():
                            propertyName = ":" + propertyId["name"]
                        elif propertyId["vocabulary"].lower() is not None:
                            propertyName = propertyId["vocabulary"].lower() + ":" + propertyId["name"]

                        tmpOnto["project"]["ontologies"][0]["resources"][-1]["cardinalities"].append({
                            "propname": propertyName,
                            # "gui_order": "",  # TODO gui_order not yet implemented by knora.
                            "cardinality": propertyId["occurrence"]
                        })
            else:
                continue

    # ==================================================================================================================
    def fetchProperties(self, project):
        controlList = []  # List to identify dublicates of properties. We dont want dublicates in the properties list
        propId = 0  # Is needed to save the property Id to get the guiElement
        resId = 0  # Is needed to save the resource Id to get the guiElement

        guiEleMap = {
            "text": "SimpleText",
            "textarea": "Textarea",
            "richtext": "Richtext",
            "": "Colorpicker",
            "date": "Date",
            "": "Slider",
            "geoname": "Geonames",
            "spinbox": "Spinbox",
            "": "Checkbox",
            "radio": "Radio",
            "": "List",
            "pulldown": "Pulldown",
            "hlist": "Pulldown",
            "searchbox": "Searchbox",
            "interval": "IntervalValue",
            "fileupload": "__FILEUPLOAD__"
        }  # Dict that maps the old guiname from salsa to the new guielement from knorapy

        objectMap = {
            "Text": "TextValue",
            "Richtext": "TextValue",
            "Iconclass": "TextValue",
            "": "ColorValue",
            "Date": "DateValue",
            "Time": "TimeValue",
            "Floating point number": "DecimalValue",
            "": "GeomValue",
            "Geoname": "GeonameValue",
            "Integer value": "IntValue",
            "": "BooleanValue",
            "": "UriValue",
            "": "IntervalValue",
            "Selection": "ListValue",
            "Hierarchical list": "ListValue",
            "Resource pointer": "LinkValue"
        }  # Dict that maps the old vt-name from salsa to the new Object type from knorapy
        # TODO right mapping from object map to super map
        superMap = {
            "": "hasValue",
            "LinkValue": "hasLinkTo",
            "ColorValue": "hasColor",
            "": "hasComment",
            "": "hasGeometry",
            "": "isPartOf",
            "": "isRegionOf",
            "": "isAnnotationOf",
            "": "seqnum"
        }  # Dict that maps the old the super corresponding to the object-type

        hlist_node_mapping = {}

        # fetch selections
        req = requests.get('http://salsah.org/api/selections/')
        selection_results = req.json()
        selections = selection_results["selections"]

        # fetch hlists
        req2 = requests.get('http://salsah.org/api/hlists/')
        hlist_results = req2.json()
        hlists = hlist_results["hlists"]

        for vocabulary in salsahJson.salsahVocabularies["vocabularies"]:
            if project["id"] == vocabulary["project_id"]:
                payload: dict = {
                    'vocabulary': vocabulary["shortname"],
                    'lang': 'all'
                }
                # fetch resourcetypes
                req = requests.get('http://salsah.org/api/resourcetypes/', params=payload)
                resourcetype_results = req.json()
                resourcetypes = resourcetype_results["resourcetypes"]

                controlList.clear()  # The list needs to be cleared for every project

                for resourcetype in resourcetypes:
                    for propertiesId in resourcetype["properties"]:
                        # for labelId in propertiesId["label"]: - If you want for every language a single property
                        if propertiesId["label"][0]["label"] in controlList:
                            continue
                        else:
                            # Fill in the name of the property as well as getting the framework done
                            tmpOnto["project"]["ontologies"][0]["properties"].append({
                                "name": "",
                                "super": [],
                                "object": "",
                                "labels": {},
                                "comments": {},
                                "gui_element": "",
                                "gui_attributes": {}
                            })
                            tmpOnto["project"]["ontologies"][0]["properties"][-1]["name"] = propertiesId["label"][0]["label"]
                            controlList.append(propertiesId["label"][0]["label"])

                            # Fill in the labels of the properties - Its all the different language-names of the property
                            for labelId in propertiesId["label"]:
                                tmpOnto["project"]["ontologies"][0]["properties"][-1]["labels"].update({
                                    labelId["shortname"]: labelId["label"]
                                })

                        # finding property name plus its id in order to fill in guiname
                        for labelId in propertiesId["label"]:
                            if labelId["label"] == tmpOnto["project"]["ontologies"][0]["properties"][-1]["name"]:
                                propId = propertiesId["id"]

                        req = requests.get(
                            'https://salsah.org/api/resourcetypes/{}?lang=all'.format(resourcetype["id"]))
                        resType = req.json()
                        resTypeInfo = resType["restype_info"]

                        for property in resTypeInfo["properties"]:
                            if "id" in property and property["id"] == propId:
                                # fill in the description of the properties as comments
                                if property["description"] is not None and isinstance(property["description"], list):
                                     for descriptionId in property["description"]:
                                         tmpOnto["project"]["ontologies"][0]["properties"][-1]["comments"].update({
                                             descriptionId["shortname"]: descriptionId["description"]
                                         })

                                # fill in gui_element
                                tmpOnto["project"]["ontologies"][0]["properties"][-1]["gui_element"] = guiEleMap[property["gui_name"]]

                                # fill in object (has to happen before attributes)
                                if "vt_name" in property and property["vt_name"] in objectMap:
                                    tmpOnto["project"]["ontologies"][0]["properties"][-1]["object"] = objectMap[property["vt_name"]]

                                    # fill in super attributes of the property. Default is "hasValue"
                                    if objectMap[property["vt_name"]] in superMap:
                                        tmpOnto["project"]["ontologies"][0]["properties"][-1]["super"].append(superMap[objectMap[property["vt_name"]]])
                                    else:
                                        tmpOnto["project"]["ontologies"][0]["properties"][-1]["super"].append("hasValue")

                                # fill in all attributes (gui_attributes and resource pointer)
                                if "attributes" in property and property["attributes"] != "" and property["attributes"] is not None:
                                    # split attributes entry
                                    finalSplit = []
                                    tmpstr = property["attributes"]
                                    firstSplit = tmpstr.split(";")
                                    for splits in firstSplit:
                                        finalSplit.append(splits.split("="))

                                    for numEle in range(len(finalSplit)): #  instead of the list id, insert the name of the list via the id .replace("selection", "hlist")
                                        numEleKey = finalSplit[numEle][0]
                                        numEleValue = finalSplit[numEle][1]

                                        if (numEleKey == "selection" or numEleKey == "hlist"):  # here the selections-id's are converted into the name
                                            numEleKey = "hlist"
                                            # add selections
                                            for selectionId in selections:
                                                if numEleValue == selectionId["id"] and selectionId["name"] != "":
                                                    numEleValue = selectionId["name"]
                                            # add hlists
                                            for hlistsId in hlists:
                                                if numEleValue == hlistsId["id"] and hlistsId["name"] != "":
                                                    numEleValue = hlistsId["name"]

                                        # convert gui attribute's string values to integers where necessary
                                        if (numEleKey == "size" or numEleKey == "maxlength" or numEleKey == "numprops" or numEleKey == "cols" or numEleKey == "rows" or numEleKey == "min" or numEleKey == "max"):
                                            try:
                                                numEleValue = int(numEleValue)
                                            except ValueError:
                                                numEleValue = numEleValue

                                        # fill in gui attributes (incl. hlists)
                                        tmpOnto["project"]["ontologies"][0]["properties"][-1]["gui_attributes"].update({
                                            numEleKey: numEleValue
                                        })

                                        # fill in ResourcePointer / LinkValue types
                                        if (numEleKey == "restypeid" and tmpOnto["project"]["ontologies"][0]["properties"][-1]["object"] == "LinkValue"):
                                            # get resource type by value of restypeid
                                            if numEleValue != '0':
                                                req = requests.get(
                                                    'https://salsah.org/api/resourcetypes/{}?lang=all'.format(
                                                        numEleValue))
                                                linkValueResType = req.json()
                                                linkValueResTypeInfo = linkValueResType["restype_info"]
                                                linkValueResName = linkValueResTypeInfo["name"]

                                                # if LinkValue is from the same vocabulary, remove vocabulary prefix
                                                if linkValueResName.startswith(vocabulary["shortname"], 0):
                                                    linkValueResName = linkValueResName.removeprefix(vocabulary["shortname"])

                                                # replace "LinkValue" with resolved resource type name
                                                tmpOnto["project"]["ontologies"][0]["properties"][-1]["object"] = linkValueResName

    # ==================================================================================================================


if __name__ == '__main__':

    # This is a "blank" ontology. the json file is in the form we need in the new knora
    emptyOnto = {
        "prefixes": {},
        "project": {
            "shortcode": "",
            "shortname": "",
            "longname": "",
            "descriptions": {},
            "keywords": [],
            "lists": [],
            "groups": [],
            "users": [],
            "ontologies": [{
                "name": "",
                "label": "",
                "properties": [],
                "resources": []
            }]
        }
    }

    # Create an empty ontology
    tmpOnto = copy.deepcopy(emptyOnto)

    # Creating the ontology object. This object will create the new jsons.
    salsahJson = Converter()

    # Get current date to append to file name
    now = datetime.today().strftime('%Y%m%d')

    # Here the ontology object is being filled
    for projects in salsahJson.salsahJson["projects"]:
        # do only extract model for Webern project (id=6)
        if projects["id"] == "6":
            #pprint("Making Deepcopy")
            tmpOnto = copy.deepcopy(
                emptyOnto)  # Its necessary to reset the tmpOnto for each project. Otherwhise they will overlap
            #pprint("FillShortLongName")
            salsahJson.fillShortLongName(projects)  # Fill the shortname as well as the longname into the empty ontology.
            #pprint("FillID")
            salsahJson.fillId(projects)  # Fill in the project id's (shortcode) to the corresponding projects.
            #pprint("FillDesc")
            salsahJson.fillDesc(projects)  # Fill in the vocabulary name and label
            #pprint("FillVocName")
            salsahJson.fillVocName(projects)  # Fill in the vocabulary name and label
            salsahJson.fetchKeywords(projects) #  Fills in the keywords of the corresponding project
            salsahJson.fetchLists(projects)
            #pprint("FetchRessources")
            salsahJson.fetchResources(projects)
            #pprint("FetchProperties")
            salsahJson.fetchProperties(projects)
            # Creating the new json files
            f = open(projects["shortname"] + "_" + now + ".json", 'w')
            f.write(json.dumps(tmpOnto, indent=4))
