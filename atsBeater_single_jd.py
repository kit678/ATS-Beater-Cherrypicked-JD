# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 02:35:35 2019

@author: Pulkit-OldLenovo
"""

from __future__ import unicode_literals
import pandas as pd
import nltk
import re
from collections import Counter
from textblob import TextBlob
import logging
from difflib import SequenceMatcher
import numpy as np

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def cleanList(list):
    listTemp = ' '.join(list)
    listTemp = re.sub(regex, ' ', listTemp)
    return listTemp.split()

def getSimpleScore(jdList, resList):
    intersection = list(set(jdList) & set(resList))
    return (len(intersection) / len(jdList)) * 100

def isEEO(jd):
    return ['Yes' if re.search(EEOregex, j, re.IGNORECASE) else 'Not Sure' for j in jd]
    
def extractJobAge(ageColumnList):
    jobAgeList = []

    for i in ageColumnList:
        number = re.search(r"\b\d+\+?\b",i).group(0)
        if re.search(r"\bdays?\b", i): jobAgeList.append(int(number))
        elif re.search(r"\bmonths?", i): jobAgeList.append(int(number)*30)

    return jobAgeList

def getKeywordsList(text):
    text = re.sub(r"[*]",' ',text.lower()) #this could be used in conjuction with other unwanted characters, for both res and jd
    blob = TextBlob(text)
        
    #get nouns and proper nouns
    #blob = TextBlob(jnew_words)
    wordListFromInput = [(n,t) for n,t in blob.tags if (t == 'NN' or t == 'NNP' or t == 'NNS')]
    
    powerwordListFromInput = [(n,t) for n,t in blob.tags if (t == 'JJ' or t == 'VB' or t == 'VBP')]
    powerwordListFromInput = [(n,t) for n,t in blob.tags if n.lower() in powerwordsListFromFile ]
    
    wordListFromInput = wordListFromInput + powerwordListFromInput
    wordListFromInput = [n for (n,t) in wordListFromInput if n not in stopwords ]
    
    skillsFromInputLOL = [[i for i in s if nltk.tag.pos_tag(i.split()[0].split())[0][1] not in ['DT','JJ','PRP','PRP$','IN']] for s in [re.findall(r"[\w-]+\s+"+re.escape(w), text) for w in bigramWords]]
    skillsFromInput = [i.split()[0] for li in skillsFromInputLOL for i in li]
    return list(set(wordListFromInput)) + list(set(skillsFromInput))


# Logging code taken from http://rare-technologies.com/word2vec-tutorial/
logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', 
    level=logging.INFO)

# Initializing variables and data structures
stopwords = nltk.corpus.stopwords.words('english')
actionVerbsListFromFile = [line.rstrip('\n') for line in open('actionverbs.txt')]
adjectivesListFromFile = [line.rstrip('\n') for line in open('poweradj.txt')]
powerwordsListFromFile = actionVerbsListFromFile + adjectivesListFromFile
powerwordsListFromFile = [x.lower() for x in powerwordsListFromFile]
bigramWords = ['skills','experience','development','services', 'professionals', 'associate','manager','analyst']
regex = "[|%/\d–*\"]|march|may|january|april|september|misc|delhi|champaign|stamford|\\b\w\\b|\\bct\\b|\\bil\\b|july|june|york|new|illinois|urbana|august"
EEOregex = "\\b(?:eeo|eoe)\\b|\\b(?:equal\s+(?:opportunity|employment))\\b"
# Resume Handling
# new resume reading code copied from Doc_similarity
import os
from docx import Document
resumes = [ (x,Document('resumes_docx/'+ x)) for x in os.listdir('resumes_docx') if not x.startswith('~')]
resumes = dict(resumes)

# convert docs to unicode text
for key in resumes:   
    fullText = []
    for para in resumes[key].paragraphs[3:]:
        #print(para.text + "   LINE ENDS\n")
        fullText.append(para.text)

    resumes[key] = " ".join(fullText)

from lxml import html
import requests
titles = []
descriptions = []
urls = [line.rstrip('\n') for line in open('joburls.txt')]

for url in urls:
    get_response = requests.get(url)
    doc = html.fromstring(get_response.content)
    try:
        title = doc.xpath('/html/body//h3[@class="icl-u-xs-mb--xs icl-u-xs-mt--none jobsearch-JobInfoHeader-title"]//text()')[0]
        jdesc = doc.xpath('/html/body//div[@class="jobsearch-JobComponent-description icl-u-xs-mt--md"]//text()')
    except:
        pass
    jdesc = ''.join(jdesc)
    titles.append(title)
    descriptions.append(jdesc)

assert len(titles) == len(descriptions)

df = pd.DataFrame()
#df = df.drop(df.columns[[0, 1, 2,8,9]], axis=1)
#df['age'] = extractJobAge(df['age'].tolist())
df['EEO'] = isEEO(descriptions)
#df['links-href'] = [short_url.encode_url(int(link)) for link in df['links-href'].tolist()]
df['links'] = urls
df['title'] = titles
df['jdesc'] = descriptions

df['bestResume'] = np.nan
df['bestScore'] = np.nan
df['jdKeywords'] = np.nan


resumeKeywordsDic = {}
for key in resumes:
    resList = cleanList(getKeywordsList(resumes[key]))
    resumeKeywordsDic[key] = resList
    
jdKeywordsList = []
for index, row in df.iterrows():
    jdList = cleanList(getKeywordsList(row['jdesc']))
    jdKeywordsList.append(jdList)
df['jdKeywords'] = jdKeywordsList

for key in resumes:
    scoreList = []
    for index, row in df.iterrows():
        score = getSimpleScore(row['jdKeywords'], resumeKeywordsDic[key])
        scoreList.append(score)
    df[key]= scoreList


bestResumeList = []
for index, row in df.iterrows():
    highestScore = 0
    for key in resumes:
        if row[key] > highestScore: 
            highestScore = row[key]
            bestResume = key
    bestResumeList.append((bestResume, highestScore))

df['bestResume'] = [r for r,s in bestResumeList]
df['bestScore'] = [s for r,s in bestResumeList]

df.to_csv('singlejds.csv', encoding="utf-8")




