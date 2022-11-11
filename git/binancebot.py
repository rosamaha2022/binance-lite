import hashlib
import time
from urllib.parse import urlencode
import requests
import hmac
import json
import asyncio
import websockets

with open("data.txt", "r") as f:
    datalist = f.read().split("\n")

class BB():
    def __init__(self, symbol):
        self.logs = []
        self.curentmarge = ""
        self.curentleverage = 0
        self.curentprice = 0
        self.startprice = 0
        self.stoploss = 0
        self.takeprofit = 0
        self.curentautostop = 0
        self.symbol = symbol
        self.side = "BUY"
        self.quantity = 0
        self.symbolsdata = []
        self.openorderlist = []
        self.balance= []
        self.autostoplloson = False
        self.stopval = 0
        self.API = datalist[0]
        self.SECRET = datalist[1]
        self.header= {
            "X-MBX-APIKEY": self.API
        }
        
    # аутентифиация и отправка зароса
    def send(self, values, metodst, urls):
        values['timestamp'] = int(time.time() * 1000)
        values['recvWindow'] = 6000
        body = urlencode(values, True).replace("%40", "@")
        sign = hmac.new(self.SECRET.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()
        if metodst == "get":
            response = requests.get(url=f"{urls}?{body}&signature={sign}", headers=self.header)
        elif metodst == "post":
            response = requests.post(url=f"{urls}?{body}&signature={sign}", headers=self.header)
        elif metodst == "delete":
            response = requests.delete(url=f"{urls}?{body}&signature={sign}", headers=self.header)
        data = json.loads(response.text)
        if "code" in data:
            self.logs.append(data)
        return response
    
#future
    # аутентификация для стрима
    def streamauth(self):
        values = dict()
        url = "https://fapi.binance.com/fapi/v1/listenKey"
        resource = self.send(values, "post", url).text
        data = json.loads(resource)
        listenKey = data['listenKey']
        return listenKey
    
    # получаем базовую информацио обо всех торговых парах на бирже (в основном нужно для точонсти цены)
    def getinfo(self):
        responce = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo").text
        data = json.loads(responce)
        self.symbolsdata = data
     
    # получение стакана заявок 
    def getorderboock(self, url):
        responce = requests.get(url).text
        data = json.loads(responce)
        try:
            #print(data)
            a = data["asks"]
            b = data["bids"]
            return a, b
        except:
            return(data)
        
    # получение актуальной цены для торговой пары
    def httpgetcurentprice(self):
        values = dict()
        values['symbol'] = self.symbol
        url = "https://fapi.binance.com/fapi/v1/premiumIndex"
        resource = self.send(values, "get", url)
        data = json.loads(resource.text)        
        self.curentprice = data['markPrice']
        return data['markPrice']


    # изменение типа паржи изолированная перекресная
    def marginType_metod(self, marginType):
        values = dict()
        values['marginType'] = marginType
        values['symbol'] = self.symbol
        url = "https://fapi.binance.com/fapi/v1/marginType"
        resource = self.send(values, "post", url)
        
    # изменение кредитного плеча
    def leverage_metod(self, leverage):
        values = dict()
        values['leverage'] = leverage
        values['symbol'] = self.symbol
        url = "https://fapi.binance.com/fapi/v1/leverage"
        resource = self.send(values, "post", url)
        
    # открытие позиции или ордера для торговли
    def postopenorder(self, **kwargs):
        values = dict()
        values['symbol'] = self.symbol
        values['type'] = kwargs['typeorder']        
        if kwargs['typeorder'] == "MARKET":
            values['side'] = kwargs['side']
            values['quantity'] = kwargs['quantity']
            self.side = values['side']
        elif kwargs['typeorder'] == 'LIMIT':
            values["timeInForce"] = "GTC"
            values['price'] = kwargs['price']
            values['side'] = kwargs['side']
            values['quantity'] = kwargs['quantity']
            self.side = values['side']
        elif kwargs['typeorder'] == "STOP_MARKET" or kwargs['typeorder'] == "TAKE_PROFIT_MARKET":
            for i in self.openorderlist:
                if i[0] == kwargs['typeorder']:
                      self.deleteorder(i[1])
            if self.side == "BUY" : values['side'] = "SELL"
            if self.side == "SELL" : values['side'] = "BUY"
            values['stopPrice'] = kwargs['stopPrice']
            values['closePosition'] = 'true'           
        url = "https://fapi.binance.com/fapi/v1/order"
        resource = self.send(values, "post", url).text
        self.getopenOrders(10)
        
        
    # закрытие позиции по рынку
    def postcloseposition (self):
        values = dict()
        values['symbol'] = self.symbol
        values['type'] = "MARKET"
        values['reduceOnly'] = 'true'
        if self.side == "BUY" : values['side'] = "SELL"
        if self.side == "SELL" : values['side'] = "BUY"
        values['quantity'] = abs(self.quantity) 
        url = "https://fapi.binance.com/fapi/v1/order"
        resource = self.send(values, "post", url).text
        self.deletecloseallorders()
        self.getopenOrders(10)
        
    # закрытие открытых ордеров
    def deletecloseallorders(self):
        values = dict()
        values['symbol'] = self.symbol
        url = "https://fapi.binance.com/fapi/v1/allOpenOrders"
        resource = self.send(values, "delete", url).text
        self.getopenOrders(10)
        
    
    def deleteorder(self, orderid):
        values = dict()
        values['symbol'] = self.symbol
        values['orderId'] = orderid
        url = "https://fapi.binance.com/fapi/v1/order"
        resource = self.send(values, "delete", url)
        self.stoploss = 0
        self.takeprofit = 0
        self.getopenOrders(10)
    
    # получение списка открытых ордеров
    def getopenOrders(self, limit):
        values = dict()
        values['symbol'] = self.symbol
        values['limit'] = limit
        url = "https://fapi.binance.com/fapi/v1/openOrders"
        resource = self.send(values, "get", url).text
        data = json.loads(resource)
        self.openorderlist = []
        if  "code" in data:
            pass
        else:
            for i in data:    
                self.openorderlist.append([i['type'], i["orderId"], i["avgPrice"], i["stopPrice"]])
        
        
    # получение истории торгов
    def getallOrders(self, **kwargs):
        values = dict()
        values['symbol'] = self.symbol
        values['limit'] = kwargs['limit']
        values['orderId'] = kwargs['orderid']
        url = "https://fapi.binance.com/fapi/v1/allOrders"
        resource = self.send(values, "get", url).text
        data = json.loads(resource)
        return data
        
    # выставление стоп-лосса и тейк-профита от текущей цены в процентном соотношении
    def autoloss(self, typeorder, stopval):
        pricePrecision = 0
        for i in range(len(self.symbolsdata)-1):   #достаем значение точности цены для торговой пары
            if self.symbolsdata["symbols"][i]["symbol"] == self.symbol.upper():
                pricePrecision = self.symbolsdata["symbols"][i]["pricePrecision"]
        price = float(self.httpgetcurentprice())    #получаем актуальную цену
        if self.side == "BUY":
            if typeorder == "STOP_MARKET":
                stopPrice = round(price - (price*(stopval/100)), pricePrecision)
                #print(price, stopPrice)
            if typeorder == "TAKE_PROFIT_MARKET":
                stopPrice = round(price + (price*(stopval/100)), pricePrecision)
                #print(price, stopPrice)
        elif self.side == "SELL":
            if typeorder == "STOP_MARKET":
                stopPrice = round(price + (price*(stopval/100)), pricePrecision)                
                #print(price, stopPrice)
            if typeorder == "TAKE_PROFIT_MARKET":
                stopPrice = round(price - (price*(stopval/100)), pricePrecision)
                #print(price, stopPrice)
        self.postopenorder(typeorder = typeorder, stopPrice = stopPrice)
        
    # функция следит за актуальной ценой и закрывает позицию по рынку если цена вкатила в - (в порцентах)
    async def autostopllos(self):
        maxprice = self.curentprice
        stopprice = 0
        oldspotprice = 0
        while True:
            while self.autostoplloson:
                if self.side == "BUY":
                    if self.curentprice > maxprice:
                        maxprice = self.curentprice
                    stopprice = maxprice-(maxprice*(self.stopval/100))
                    if stopprice > self.curentprice:
                        self.postcloseposition()
                        self.curentautostop = 0
                        self.autostoplloson = False
                if self.side == "SELL":
                    if self.curentprice < maxprice or maxprice == 0:
                        maxprice = self.curentprice
                    stopprice = maxprice+(maxprice*(self.stopval/100))
                    if stopprice < self.curentprice:
                        self.postcloseposition()
                        self.curentautostop = 0
                        self.autostoplloson = False
                if stopprice != oldspotprice:               
                    oldspotprice = stopprice
                    self.curentautostop = stopprice
                await asyncio.sleep(0.1)
            await asyncio.sleep(0.1)

        
    # получение данных об изменениях в открытых позициях
    async def getopenposition (self):
        listenkey = self.streamauth()
        url = f"wss://fstream.binance.com/ws/{listenkey}"
        async with websockets.connect(url) as client:
            while True:
                data = json.loads(await client.recv())
                self.balance = []
                if data['e'] == 'ACCOUNT_UPDATE':
                    for i in data['a']['B']:
                        self.balance.append(f"{i['a']} : {i['wb']}/{i['cw']}")
                    for i in data['a']['P']:
                        if i['s'] == self.symbol.upper():
                            self.quantity = float(i['pa'])
                            self.startprice = float(i['ep'])
                await asyncio.sleep(0.1)
                            
                    
                    
                
    # получение актуальной цены торговой пары с интервало 1с   
    async def getcurentprice(self):
        url = f"wss://fstream.binance.com/ws/{self.symbol.lower()}@markPrice@1s"
        async with websockets.connect(url) as client:
            while True:
                data = json.loads(await client.recv())
                self.curentprice = float(data['p'])
        
    def main1(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.getcurentprice())
        loop.run_forever()
        
    def getmargimleverage (self):
        values = dict()
        url = "https://fapi.binance.com/fapi/v2/account"
        resource = self.send(values, "get", url).text
        data = json.loads(resource)
        for i in data['positions']:
            if i['symbol'] == self.symbol.upper():
                if i["isolated"] == False:
                    self.curentmarge = "CROSSED"
                elif i["isolated"] == True:
                    self.curentmarge = "ISOLATED"
                self.curentleverage = i['leverage']


if __name__ == "__main__":
    botbinance = BB("btcusdt")
    #botbinance.getinfo()
    #botbinance.marginType_metod("ISOLATED", "BTCUSDT")  # ISOLATED, CROSSED
    #botbinance.leverage_metod(5, "BTCUSDT")
    #botbinance.allOrders("BTCUSDT", 2)
    #botbinance.streamauth()
    #botbinance.openorder(side = "BUY", quantity = 0.001, typeorder = "MARKET")
    #botbinance.openorder(symbol = "BTCUSDT", side = "BUY", typeorder = "STOP_MARKET", stopPrice = 21450)
    #botbinance.openorder(symbol = "BTCUSDT", side = "BUY", typeorder = "TAKE_PROFIT_MARKET", stopPrice = 21350)
    #botbinance.getcurentprice()
    #botbinance.autoloss("STOP_MARKET", 0.1)
    #botbinance.autoloss("TAKE_PROFIT_MARKET", 2)
    #time.sleep(2)
    #botbinance.closeposition("BTCUSDT", "SELL", 0.0005)    
    #botbinance.autostopllos(0.1)
    #botbinance.allOrders(limit = 5, orderid = 71053089494)
    loop = asyncio.get_event_loop()
    loop.create_task(botbinance.getopenposition())
    loop.run_forever()