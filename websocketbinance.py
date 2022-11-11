import websockets
import asyncio
import json
from binancebot import BB

class WebBinance():
    def __init__(self, symbol):
        self.curentprice = 0
        self.fin_ask = {}
        self.fin_bid = {}
        self.s_ask = {}
        self.s_bid = {}
        self.symbol = symbol
        self.top_plot = []
        self.bot = BB(symbol)
    
    # получение фючерсного стакана заявод
    async def stakanf(self, urls = None):
        a, b = self.bot.orderboock(f"https://fapi.binance.com/fapi/v1/depth?symbol={self.symbol.upper()}&limit=50")
        self.fin_ask, self.fin_bid = filter(a, b, self.fin_ask, self.fin_bid)
        if urls == None:
            url = f"wss://fstream.binance.com/stream?streams={self.symbol.lower()}@depth"
        async with websockets.connect(url) as client:
            while True:
                data = json.loads(await client.recv())
                a = data["data"]["a"]
                b = data['data']['b']
                self.fin_ask, self.fin_bid = filter(a, b, self.fin_ask, self.fin_bid)

    # получение спотового стакана заявок
    async def stakans(self):
        a, b = self.bot.orderboock(f"https://api.binance.com/api/v3/depth?symbol={self.symbol.upper()}&limit=50")
        self.s_ask, self.s_bid = filter(a, b, self.s_ask, self.s_bid)
        url = f"wss://stream.binance.com:9443/ws/{self.symbol.lower()}@depth@1000ms"
        async with websockets.connect(url) as client:
            while True:
                data = json.loads(await client.recv())
                a = data["a"]
                b = data['b']
                self.s_ask, self._bid = filter(a, b, self.s_ask, self.s_bid)
                
    # поиск плотностей в полученых данных
    async def plotnost(self):
        top_plot = []
        while True:
            try:
                Len = len (self.s_ask) # Взять количество пар ключ-значение в словаре
                Sum = sum (self.s_ask.values()) # Взять сумму соответствующих значений ключей в словаре
                Avg = Sum / Len
                top_plot = []

                for key, value in self.s_ask.items():
                    if value >= Avg*5:
                        top_plot.append(f"{key} : {value}")
                    if len(top_plot) >= 5:
                        break
            except:
                pass
            print(top_plot)
            await asyncio.sleep(0.1)




# преобразование данных полученых от stakanf stakans         
def filter(a, b, ask, bid):
    for i in a:
        key = float(i[0])
        val = float(i[1])
        if val != 0:
            ask[key] = val
        else:
            try:
                del ask[key]
            except:
                pass

    for i in b:
        key = float(i[0])
        val = float(i[1])
        if val != 0:
            bid[key] = val
        else:
            try:
                del bid[key]
            except:
                pass
    return ask, bid



if __name__ == "__main__":
    bot = WebBinance("ETHTUSD")
    loop = asyncio.get_event_loop()
    #loop.create_task(stakanf())
    loop.create_task(bot.stakans())
    #loop.create_task(bot.getcurentprice())
    loop.create_task(bot.plotnost())
    loop.run_forever()

