import requests
import os
import sys
from bs4 import BeautifulSoup
from notion_client import Client



#Format song, artist string for url

canzone = input("Inserire nome canzone\n")
artista= input("Inserire artista\n")


canzone_list = canzone.split()
artista_list = artista.split()

def check_char (input_list):
    for i in range(len(input_list)):
        for char in input_list[i]:
            match char:
                case "à":
                    input_list[i] = input_list[i].replace(char, 'a')
                    break
                case "è":
                    input_list[i] = input_list[i].replace(char, 'e')
                    break
                case "ì":
                    input_list[i] = input_list[i].replace(char, 'i')
                    break
                case "ò":
                    input_list[i] = input_list[i].replace(char, 'o')
                    break
                case "ù":
                    input_list[i] = input_list[i].replace(char, 'u')
                    break
                case "'":
                    input_list[i] = input_list[i].replace(char, '')
                    break
        
    return input_list


canzone_list = check_char(canzone_list)
artista_list = check_char(artista_list)

canzone_url = "-".join(canzone_list)
artista_url = "-".join(artista_list)


#Load request

try:
    r = requests.get(url="https://genius.com/"+artista_url+"-"+canzone_url+"-lyrics")
except:
    print("Nessuna risposta dal server")

#SOUP THE SONG

soup = BeautifulSoup(r.content, 'html.parser')

#Load song text
text_dom = soup.find_all('div', {'data-lyrics-container': "true", 'class': "Lyrics-sc-37019ee2-1 jRTEBZ"})



def exctract_text_str(dom_finded):          #Extract only string content of html dom of text_div
    text = []
    for index in dom_finded:
        text_div = []
        square_met = False
        for child in index.descendants:
            if(child.name == None):
                if(child.string[0] == "["): #Sometimes the text contains the name of verses bethween squares 
                    square_met = True
                    continue
                text_div.append(child.string)
            elif (child.name == "br"):
                if(square_met == True):
                    square_met = False
                    continue
                text_div.append("\n")
        text.append(text_div)
    
    text_str = ""
    for divs in text:
        for x in divs:
            text_str += x
    
    text_str += "~"
    
    return text_str



if(exctract_text_str(text_dom) == "~"):
    print("Testo non trovato")
    sys.exit()
    

columns_block_dict = {
      "object": "block",
      "type": "column_list",
      "column_list": {
        "children": [
          { 
            "object": "block",
            "type": "column",
            "column": {
              "children": [
                {
                  "object": "block",
                  "type": "paragraph",
                  "paragraph": {
                    "rich_text": [
                      {
                        "type": "text",
                        "text": {
                          "content": ""
                        }
                        
                      }
                    ]
                  }
                }
              ]
            }
          },
          {
            "object": "block",
            "type": "column",
            "column": {
              "children": [
                {
                  "object": "block",
                  "type": "paragraph",
                  "paragraph": {
                    "rich_text": [
                      {
                        "type": "text",
                        "text": {
                          "content": ""
                        }
                      }
                    ]
                  }
                }
              ]
            }
          }
        ]
      }
    }

def dict_costr(text_str, columns):          #text in a single column
    text_par = ""
    last_char = ""
    n_par = 0
    for char in text_str:
        if(last_char == char and last_char == "\n"):        #L'ultima strofa non contiene il carattere \n
            text_par = text_par[:-1]
            columns["column_list"]["children"][0]["column"]["children"][n_par]["paragraph"]["rich_text"][0]["text"]["content"] = text_par
            paragraph = {
                              "object": "block",
                              "type": "paragraph",
                              "paragraph": {
                                "rich_text": [
                                  {
                                    "type": "text",
                                    "text": {
                                      "content": ""
                                    }
                                  }
                                ]
                              }
                            }   
            columns["column_list"]["children"][0]["column"]["children"].append(paragraph)
            
            text_par = ""
            n_par += 1
        elif (char == "~"):
            columns["column_list"]["children"][0]["column"]["children"][n_par]["paragraph"]["rich_text"][0]["text"]["content"] = text_par
        else:
            text_par += char
            last_char = char
            
    
    return columns
        

columns_block_dict = dict_costr(exctract_text_str(text_dom), columns_block_dict)

n_par = (len(columns_block_dict["column_list"]["children"][0]["column"]["children"]))

def two_columns (columns, n_par):
    index_right = 0
    for i in range(n_par):
        if(i >= (n_par / 2 )):
            columns["column_list"]["children"][1]["column"]["children"][index_right]["paragraph"]["rich_text"][0]["text"]["content"] = columns["column_list"]["children"][0]["column"]["children"][i]["paragraph"]["rich_text"][0]["text"]["content"]
            paragraph = {
                              "object": "block",
                              "type": "paragraph",
                              "paragraph": {
                                "rich_text": [
                                  {
                                    "type": "text",
                                    "text": {
                                      "content": ""
                                    }
                                  }
                                ]
                              }
                            }   
            columns["column_list"]["children"][1]["column"]["children"].append(paragraph)
            columns["column_list"]["children"][0]["column"]["children"][i]["paragraph"]["rich_text"][0]["text"]["content"] = ""
            index_right += 1
    return columns


columns_block_dict = two_columns(columns_block_dict, n_par)



def call_API (key):
    os.environ["NOTION_KEY"] = key
    notion_response = Client(auth=os.environ["NOTION_KEY"])
    
    return notion_response

def add_song (notion, children, canzone):
    db = notion.blocks.retrieve("192e6e2d19b08036b5b7f8a10a4713e7")
    
    page_dict = {
        "cover": None,
        "icon": {
            "type": "emoji",
            "emoji": "📜"
        },
        "parent": {
            "type": "database_id",
            "database_id": db["id"]
        },
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": canzone
                        }
                    }
                ]
            },
        },
        "children": [children]
    }
    
    #try:
    notion.pages.create(cover=page_dict["cover"], icon=page_dict["icon"], parent=page_dict["parent"], properties=page_dict["properties"], children=page_dict["children"])
    print("Canzone inserita")
    #except:
     #   print("Canzone non inserita")

my_integration = "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"
add_song (call_API(my_integration), columns_block_dict, canzone)


