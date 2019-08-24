#!/usr/bin/env python
# coding: utf-8

# In[15]:


from string import digits
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
from nltk.corpus import cmudict,stopwords

# In[4]:


def clean_text(text):    
    #remove digits with decimal points
    text=re.sub(r"[0-9]+\.+[0-9]+","",text)
    #remove digits
    remove_digits=str.maketrans("", "",digits)
    text=text.translate(remove_digits)
    #remove punctuations except periods
    text=re.sub(r'[^\w\.\s]',"",text)
    #remove array of periods
    text=re.sub(r"\.\.+","",text)
    #remove extra spaces
    text=" ".join(text.split())
    return text


# In[5]:


def report_constraints(text,constraints):
    '''
    count number of constraints in the report
    '''
    #count words in the text
    split_words=text.split()
    #remove periods from the list
    clean_list=list(map(lambda x:re.sub(r"[^a-zA-Z\']","",x),split_words))
    clean_list=list(filter(None,clean_list))
    
    constraint_count=sum(word in constraints for word in clean_list)
    return constraint_count


# In[6]:


def score(clean_list,df,stopword_gen):
    #remove generic stopwords
    clean_list=[word.upper() for word in clean_list if word not in stopword_gen]
    #count positive and negative words in the list
    positive=0
    negative=0
    for word in clean_list:
        if word in list(df.Word):
            if df.loc[df["Word"]==word, "Positive"].iloc[0] != 0:
                positive+=1
            else:
                negative+=1  
    #polarity score
    polarity_score=(positive - negative)/((positive + negative) + 0.000001)   
    #subjectivity score
    subjectivity_score=(positive+negative)/((len(clean_list))+0.000001)
    
    return positive,negative,polarity_score,subjectivity_score        


# In[7]:


#sentiment category
def category(polarity):
    if polarity <= -0.5:
        cat="Most Negative"
    elif -0.5 < polarity < 0:
        cat="Negative"
    elif polarity == 0:
        cat="Neutral"
    elif 0 < polarity < 0.5:
        cat="Positive"
    else:
        cat="Very Positive"
    return cat    


# In[8]:


#count syllables
def syllable_count(word,d):
    try:
        count=max([len(list(y for y in x if y[-1].isdigit())) for x in d[word.lower()]])
        return count
    except KeyError:
        word=word.lower()
        count=0
        vowels="aeiouy"
        #count if first letter is vowel
        if word[0] in vowels:
            count+=1   
        for index in range(1, len(word)):
            #count the vowel in only if previous letter is not vowel
            if index==(len(word) - 2) and (word[index]+word[index+1]=="ed" or word[index]+word[index+1]=="es"): 
                break    
            if word[index] in vowels and word[index - 1] not in vowels:
                count+=1    
        if word.endswith("e"):
            count-=1
        if count==0:
            count+=1
        return count


# In[9]:


def readability(string,clean_list,complex_words):   
    '''analysis of readability'''
    #average sentence length
    string=string.replace("U.S.","")
    num_sent=string.split(".")
    avg_sent_length=len(clean_list)/len(num_sent)
    avg_sent_length=round(avg_sent_length,2)

    #fraction of complex words
    frac=complex_words/len(clean_list)

    #fog index
    fog=0.4*(avg_sent_length+frac)
    fog=round(fog,2)
    
    return fog,avg_sent_length,frac


# In[13]:


def personal_pronoun(string):    
    #count personal pronouns
    pers_pronoun=["i","we","ours","us"]
    t="i am we"
    pattern="|".join(r"\b%s\b" % w for w in pers_pronoun)
    match=re.compile(pattern,flags=re.IGNORECASE)
    pro_count=len(match.findall(string))
    return pro_count


# In[16]:


#passive auxillary verbs
aux_verb=["to be", "to have", "will be", "has been", "have been", "had been", "will have been",
               "being", "am", "are", "is", "was", "were"]
#create list of irregular verbs(past participle)
verb_url="https://www.worldclasslearning.com/english/irregular-verb-forms.html"
html=requests.get(verb_url)
soup=BeautifulSoup(html.content,"lxml")
verb_text=soup.prettify()

tr=soup("tr")[1:]
irr_verb=[tag.find_all("td")[3].get_text() for tag in tr]#remove double words pending


# In[17]:


def PassiveWords(string):    
    #passive words
    #find passive auxillary verbs
    verb_pattern="|".join(r"\b%s\b" % w for w in aux_verb)
    verb_match=re.compile(verb_pattern,flags=(re.IGNORECASE))
    find_verb=verb_match.findall(string)

    #find passive words
    passive_words=0
    for verb in find_verb:
        irreg_verb=re.compile(r"\b"+verb+" (\w+)")
        next_word=irreg_verb.findall(string)
        for word in next_word:
            if word in irr_verb or word.endswith("ed"):
                passive_words+=1
    return passive_words 

