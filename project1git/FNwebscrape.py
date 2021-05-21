from bs4 import BeautifulSoup
import re
import requests
import pandas as pd
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Safari/605.1.15Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Safari/605.1.15'
            }

#funct to get the urls to each recipe in the search
def geturlsFN(response ,text):
    """"
    scrapes urls for recipes that result when searching for a recipe of FN
    """
    reciperesult = text.find_all('section', attrs={'class': 'o-RecipeResult o-ResultCard'})
    recipe_urls = ['http:'+ tag.find('a').get('href') for tag in reciperesult]
    return recipe_urls
def getratingsFN(response ,text):
    """"
    scrapes ratings for recipes that result when searching for a recipe of FN
    """
    s=str(text.find_all('div', attrs={'class': 'o-ResultCard__m-MediaBlock m-MediaBlock'})).split('<div class="o-ResultCard__m-MediaBlock m-MediaBlock">')[1:]
    ratings=[(str(re.findall('title=\".*? of 5 stars',x))[9:-13]) for x in s]
    return ratings
def getnumreviewFN(response ,text):
    """"
    scrapes #reviews for recipes that result when searching for a recipe of FN
    """
    s=str(text.find_all('div', attrs={'class': 'o-ResultCard__m-MediaBlock m-MediaBlock'})).split('<div class="o-ResultCard__m-MediaBlock m-MediaBlock">')[1:]
    numratings=[(str(re.findall('gig-rating-ratingsum\"\>.*? Review',x))[24:-9]) for x in s]
    return numratings

#obtain urls ratings and #ratings for each page

def scraperecipeurls(searchurl):
    #gets the urls that result from the search and the num of
    #reviews and avg num of stars per recipe
    firstpage=f'{searchurl}{1}/CUSTOM_FACET:RECIPE_FACET'
    print(firstpage)
    response = requests.get(firstpage, headers=headers)
    text = BeautifulSoup(response.text, 'html.parser')

    numberofpages=int(re.sub(r"[\n\t\s]*", "", text.find_all('a', attrs={'class': 'o-Pagination__a-Button'})[-2].string) )
    allurls=[]
    allratings=[]
    allratingnums=[]
    for i in range(numberofpages):
        response = requests.get(f'{searchurl}{i+1}/CUSTOM_FACET:RECIPE_FACET', headers=headers)
        text = BeautifulSoup(response.text, 'html.parser')
        if response.status_code !=200:
            print(f"status trouble {i+1}")
        pageurls=geturlsFN(response ,text)
        allurls=allurls+pageurls
        pageratings=getratingsFN(response ,text)
        allratings=allratings+pageratings
        pageratingnums=getnumreviewFN(response ,text)
        allratingnums=allratingnums+pageratingnums
    return [allurls,allratings,allratingnums]



def getrecipedataFN(urls):
    """"
    funct that takes in a list of urls of recipes and extracts
    the title of the recipe, the ingredients of the cake portion and the number of servings it yields
    """
    title=[]
    servings=[]
    ingredients=[]
    for i in range(len(urls)):
        response = requests.get(urls[i], headers=headers)
        text = BeautifulSoup(response.text, 'html.parser')
        title.append(text.find_all('span', attrs={'class': 'o-AssetTitle__a-HeadlineText'})[0].string)
        try:
            servings.append(str(text.find_all('span',text=re.compile('Yield:'))[0].find_next_siblings())[43:-8])
        except:
            servings.append('NA')
        if text.find_all('h6',attrs={'class':'o-Ingredients__a-SubHeadline'})==[]:
            ingredients.append([str(re.findall('value=\".*?\"',str(x)))[9:-3] for x in text.find_all('input',attrs={'class':'o-Ingredients__a-Ingredient--Checkbox'})[1:]])
        else:
            s=str(text.find_all('div',attrs={'class':'o-Ingredients__m-Body'})).split("Frosting:")[0]
            ingredients.append([x[7:-1] for x in re.findall('value=\".*?\"',s)][1:])
    return [title,servings,ingredients]


#get attributes for each recipe- cost and calories will be calculated based on ingreidnts later
searchurl=['https://www.foodnetwork.com/search/white-cupcakes-/p/','https://www.foodnetwork.com/search/yellow-cupcakes-/p/']#'https://www.foodnetwork.com/search/vanilla-cupcakes-/p/']#'https://www.foodnetwork.com/search/lemon-cake-/p/']#'https://www.foodnetwork.com/search/white-cake-/p/','https://www.foodnetwork.com/search/yellow-cake-/p/','https://www.foodnetwork.com/search/angel-food-cake-/p/']#'https://www.foodnetwork.com/search/vanilla-cake-/p/']

alldata=[]
for i in range(len(searchurl)):

    [allurls,allratings,allratingnums]=scraperecipeurls(searchurl[i])
    [title,servings,ingredients]=getrecipedataFN(allurls)
    alldata=alldata+list(zip(title,servings,ingredients,allratings,allratingnums))

recipedf=pd.DataFrame(alldata,columns =['Recipe_title','servings','ingredients','stars','Num_of_reviews'])
recipedf.to_csv('recipes3.csv')
print('DONE')
