#!flask/bin/python
from flask import Flask, make_response, jsonify, request, json
from selenium import webdriver
from selenium.webdriver.common.by import By
from ebaysdk.exception import ConnectionError
from ebaysdk.finding import Connection


app = Flask(__name__)

@app.route("/")
def app():
    return "REST API for getting products, in particular, by price filter from  eBay and Rozetka — Python developer" \
           " —- Python3, Flask, eBay API, Selenium"

def rozetka_list(url):
    try:
        driver = webdriver.Chrome()
        driver.get(url)
        driver.implicitly_wait(0.5)
        detailed_list = driver.find_elements(by=By.CSS_SELECTOR, value="div.goods-tile__inner")
        res = []
        for item in detailed_list:
            try:
                product_price = int(''.join(
                    item.find_element(by=By.CSS_SELECTOR, value="span.goods-tile__price-value").text[:-1].split(" ")))
                product_name = item.find_element(by=By.CSS_SELECTOR, value="span.goods-tile__title").text
                img_src = item.find_element(by=By.CSS_SELECTOR, value="img.ng-lazyloaded").get_attribute("src")
                product_link = item.find_element(by=By.CSS_SELECTOR, value="a.goods-tile__picture").get_attribute(
                    "href")
                res.append( {"product_name": product_name, "product_price": int(product_price), "img_src": img_src,
                        "product_link": product_link})
            except:
                continue
        driver.quit()
        return res
    except:
        raise "rozetka_exception"





#get request for getting short(product_name, product_price, img_src, product_link) list of products from rozetka
#url - url of products of category in rozetka
#example of using http://127.0.0.1:5000/get_rozetka_list_short/?url=https://rozetka.com.ua/ua/notebooks/c80004/page=67/
@app.route('/get_rozetka_list/', methods=['GET'])
def get_rozetka_list_get():
    try:
        url = request.args.get('url')
        return str(rozetka_list(url))
    except Exception as e:
        return make_response(jsonify({'error': e}), 500)


#get request for getting product(product_name, product_price, img_src, product_link) from rozetka by its number(optional, default = first)
#url - url of products of category in rozetka
@app.route('/get_rozetka_item/', defaults={"number": -1}, methods=['GET'])
@app.route('/get_rozetka_item/<int:number>/', methods=['GET'])
def get_rozetka_item(number):
    try:
        number = default_number(number)
        url = request.args.get('url')
        res = rozetka_list(url)
        if number < len(res):
            return res[number-1]
        else:
            return res[-1]
    except Exception as e:
        return make_response(jsonify({'error': e}), 500)


def filter(item, budget):
    if item["product_price"] <= budget:
        return True
    else:
        return False

def default_number(number):
    if number < 0:
        number = 0
    return number

#get request for getting product(product_name, product_price, img_src, product_link) from rozetka by budget and its number(optional, default = first)
#url - url of products of category in rozetka
@app.route('/get_rozetka_item_by_budget/<int:budget>/', defaults = {"number": -1}, methods=['GET'])
@app.route('/get_rozetka_item_by_budget/<int:budget>/<int:number>/', methods=['GET'])
def get_rozetka_item_by_budget(budget, number):
    try:
        number = default_number(number)
        url = request.args.get('url')
        res = rozetka_list(url)
        res1 = []
        for item in res:
            if filter(item, budget):
                res1.append(item)
        print(res1)
        if (len(res1) == 0):
            return []
        if number < len(res1):
            return res1[number]
        else:
            return res1[-1]

    except Exception as e:
        return make_response(jsonify({'error': e}), 500)


#function for eBay API connection
def eBay_api ():
    try:
        return Connection(domain='svcs.sandbox.ebay.com', debug=False, appid="MarynaUl-Tobi-SBX-aa11a70e7-f515c3eb", config_file="ebay.yaml")
    except ConnectionError as e:
        raise "eBayAPI_conection_exception"

def get_eBay_product_list(category):
    try:
        url = request.args.get('url')
        api = eBay_api()
        response = api.execute('findItemsAdvanced', {'keywords': category})
        if response.reply.ack == "Success":
            search_result = response.reply.searchResult
        else:
            search_result = []
        return search_result
    except:
        raise Exception("eBay_product_list_exception")

#get request for getting product list from eBay by category name
@app.route("/get_eBay_product_list/<category>", methods= ['GET'])
def get_eBay_product_list_view(category):
    try:
        return str(get_eBay_product_list(category))
    except:
        raise Exception("eBay_product_list_exception")

def get_eBay_product_list_by_budget(category, budget):
    api = eBay_api()
    response = api.execute('findItemsAdvanced', {'keywords': category, "itemFilter": [
        {"name": "MaxPrice", "value": budget}]}, )
    if response.reply.ack == "Success":
        search_result = response.reply.searchResult
    else:
        search_result = []
    return search_result

#get request for getting product list from eBay by category name and budget
@app.route("/get_eBay_product_list/<category>/<int:budget>", methods= ['GET'])
def get_eBay_product_list_by_budget_view(category, budget):
    try:
       return str(get_eBay_product_list_by_budget(category, budget))
    except:
        raise Exception("eBay_product_list_exception")



#get request for getting product from eBay by its number(optional) and category name
@app.route("/get_eBay_product/<category>/<int:number>", methods=['GET'])
@app.route("/get_eBay_product/<category>",  defaults = {"number": -1}, methods=['GET'])
def get_eBay_product(category, number):
    try:
        number = default_number(number)
        product_list = get_eBay_product_list(category)
        if len(product_list.item) == 0:
            return []
        elif number < len(product_list.item):
            return str(product_list.item[number])
        else:
            return str(product_list.item[-1])
    except:
        raise Exception("get_eBay_product_exception")

#get request for getting product from eBay by its category name, number(optional) and budget
@app.route("/get_eBay_product_by_budget/<category>/<int:budget>/<int:number>", methods=['GET'])
@app.route("/get_eBay_product_by_budget/<category>/<int:budget>/",  defaults = {"number": -1}, methods=['GET'])
def get_eBay_product_by_budget(category, budget, number):
    try:
        number = default_number(number)
        product_list = get_eBay_product_list_by_budget(category, budget)
        if len(product_list.item) == 0:
            return []
        elif number < len(product_list.item):
            return str(product_list.item[number])
        else:
            return str(product_list.item[-1])
    except:
        raise Exception("get_eBay_product_exception")



if __name__ == '__main__':
    app.run(debug=True, port=8000)