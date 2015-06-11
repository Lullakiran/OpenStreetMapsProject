# -*- coding: utf-8 -*-


import xml.etree.ElementTree as ET
import codecs
import json
import re
import io


def get_root(fname):
    tree = ET.parse(fname)
    return tree.getroot()

input_ankara = "ankara_turkey.osm"
#root = get_root(input_ankara)


def count_tags(root,tag):
    tag_count = 0
    for i in root.findall(tag):
        tag_count += 1
    return tag_count


def count_users(root):
    user = set()
    for i in root.findall('node') :
        try:
            user.add(i.attrib['user'])
        except:
            pass
    for i in root.findall('way'):
        try:
            user.add(i.attrib['user'])
        except:
            pass
    return  len(user) 
 
 

counts = {}
#for i in ['node', 'way', 'relation' ]:
#    counts[i] = count_tags(root,i)
#counts['user'] = count_users(root)
#print counts



def extend_abbrevations(word):
    
    abbrevations = { 'Cd.': 'Caddesi', 'Cad.':'Caddesi', 'Cd':'Caddesi', 'Sk.':'Sokak', 
                    'Mah.':'Mahallesi', 'Blv.':'Bulvari', 'Bul.':'Bulvari'}   #u'Bulvar\u0131
    for i in word.split():
        try:
            word = word.replace(i,abbrevations[i])
        except:
            pass
    return word




def correct_postcode(postcode):  #postcodes must start with 06, and must be 5 digits long
    if len(postcode) != 5: # found short postcodes like 0600, 65 in the data
        return None
    elif re.match(r'(06\d\d\d)',postcode)  == None: #check if all digits (i.e. not Esma 3 Sokak) and starts with 06
        print 'postcode', postcode
        return None
    return postcode
    


def get_value(element, attribute): #inspired from http://goo.gl/1n3xO5, assigns value if the field exists
    try:
        return element.attrib[attribute]
    except:
        return None


# ## Problems ##
# 1) Abbreviated street, avenue names (e.g. 'Cad.', 'Cd', 'Sk.')
# 
# 2) Capitalization problems (e.g. 'cad.', u'kalekap\u0131s\u0131', 'ANKARA') 
# 
# 3) Postcodes should consist of exactly 5 digits, and should start with 06.


def convert_to_unicode(input_dict):
    result = {}
    for key, val in input_dict.iteritems():
        if type(val) == type('a'):
            result[key]  = input_dict[key].encode('utf-8')
        elif type(val) == type({}):
            return convert_to_unicode(val)
    return result

    
def shape_element(element):
     
    node = {}
    lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
    problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

    if element.tag == "node" or element.tag == "way" :
        node['type'] = element.tag
        node['id'] =  element.attrib['id']
        
        node['created'] = { 'timestamp' : get_value(element,'timestamp'),
                            'version': get_value(element,'version'),
                            'changeset': get_value(element,'changeset'), 
                            'user':get_value(element,'user'), 
                            'uid': get_value(element,'uid')}
        node['visible'] =  get_value(element,'visible')
        
        try:    
            node['pos'] = [float(get_value(element,'lat')), float(get_value(element,'lon'))]
        except:
            pass
        
        
        for i in element:
        
            if element.tag=="way":
                try:
                    node.setdefault('node_refs',[]).append(i.attrib['ref'])        #http://stackoverflow.com/questions/12905999/python-dict-how-to-create-key-or-append-an-element-to-key
                except:
                    pass
            
            try:
                if "addr" in i.attrib['k']:
                    addr, field = lower_colon.match(i.attrib['k']).group().split(':') 
                    length = len(lower_colon.match(i.attrib['k']).group().split(':'))
                    v = i.attrib['v']

                    if  length <= 2 and addr=='addr' and problemchars.match(v) == None:   
                        if field == 'postcode':
                            v = correct_postcode(v)
                        node.setdefault('address',{}).update({ field: extend_abbrevations(v).title()    }) 
                else:
                     
                    if i.attrib['k'] != 'type': #some entries have <tag k = "type" v=...>
                        node[i.attrib['k']] = i.attrib['v'] 
                    
            except:
                pass
        
        return node
    else:
  
        return None


def process_map(file_in, pretty = False):
 
    file_out = "Ankara.json" #.format(file_in)
    data = []
    with codecs.open(file_out, "w", "utf-8") as fo:
        for _, element in ET.iterparse(file_in):
            el  = shape_element(element)
            if el:
                data.append(el)
                
                if pretty:
                    fo.write(json.dumps(el, indent=2, ensure_ascii=False) +"\n") #http://stackoverflow.com/questions/18337407/saving-utf-8-texts-in-json-dumps-as-utf8-not-as-u-escape-sequence
                else:
                    fo.write(json.dumps(el, ensure_ascii=False)   + "\n")
    
    return data


clean_ankara = process_map("ankara_turkey.osm")

