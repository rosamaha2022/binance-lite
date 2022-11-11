import time
import asyncio
from rich.console import Group
from rich.align import Align
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live

from binancebot import BB
import asyncio
import keyboard
from aioconsole import ainput
 
async def generate_layaut(bot):
    layout = Layout(name="root")
    layout['root'].split_column(
        Layout(name="price", size = 5),
        Layout(name="data", size = 5),
        Layout(name ="log", size = 20),
        Layout(name="balance", size = 2),
        )
    layout['price'].split_row(
        Layout(name="curentprice"),
        Layout(name="startprice"),
        Layout(name="quantity"),
        )
    layout['data'].split_row(
        Layout(name="stoploss"),
        Layout(name="takeprofit"),
        Layout(name="autostoploss"),
        Layout(name="margin"),
        Layout(name="levelage"),
        )
    layout['log']. split_row(
        Layout(name="openorder"),
        Layout(name="logline"),
        )

    with Live(layout, auto_refresh=True) as live:
        while True:
            for i in bot.openorderlist:
                if i[0] == "STOP_MARKET":
                    bot.stoploss = i[3]
                if i[0] == "TAKE_PROFIT_MARKET":
                    bot.takeprofit = i[3]
            
            layout["curentprice"].update(generate_panel("curentprice", str(bot.curentprice)))
            layout["startprice"].update(generate_panel("startprice", str(bot.startprice)))
            layout["quantity"].update(generate_panel("quantity", str(bot.quantity)))
            layout["balance"].update(generate_panel("balance", str(bot.balance)))
            layout["stoploss"].update(generate_panel("stoploss", str(bot.stoploss)))
            layout["takeprofit"].update(generate_panel("takeprofit", str(bot.takeprofit)))
            layout["autostoploss"].update(generate_panel("autostoploss", str(bot.curentautostop)))
            layout["margin"].update(generate_panel("margin", bot.curentmarge))
            layout["levelage"].update(generate_panel("levelage", str(bot.curentleverage)))
            line = ''
            for i in bot.logs[-10:]:
                line += str(i) + "\n"
            layout["logline"].update(generate_panel("log", line))
            line = ''
            for i in bot.openorderlist:
                line += str(i)+"\n"
            layout["openorder"].update(generate_panel("openorder", line))
            live.update(layout)
            await asyncio.sleep(0.1)

def generate_panel(title, target_task):
    message_panel = Panel(
        Align.center(
            Group(target_task),
            vertical="middle",
        ),
        title=title,
        border_style="bright_blue",
    )
    return message_panel

async def asyncinput(bot):
    while True:
        comand = await ainput(">>> ")
        if comand != None:
            comandlist = comand.split(" ")
            if comandlist[0] == "m":
                side = ""
                if comandlist[1] == "s": side = "SELL"
                elif comandlist[1] == "b": side = "BUY"
                bot.postopenorder(side = side, quantity = float(comandlist[2]), typeorder = "MARKET")
                #data = bot.getallOrders(limit = 5, orderid = bot.openorderlist[0][1])
                #bot.startprice = data[0]['avgPrice']
            elif comandlist[0] == "c":
                bot.postcloseposition()
            elif comandlist[0] == "sl":
                if comandlist[1][0] == "%": bot.autoloss("STOP_MARKET", float(comandlist[1][1:]))
                else: bot.postopenorder(typeorder = "STOP_MARKET", stopPrice = float(comandlist[1]))
            elif comandlist[0] == "tp":
                if comandlist[1][0] == "%": bot.autoloss("TAKE_PROFIT_MARKET", float(comandlist[1][1:]))
                else: bot.postopenorder(typeorder = "TAKE_PROFIT_MARKET", stopPrice = float(comandlist[1]))
            elif comandlist[0] == "ast":
                bot.autostopllos(float(comandlist[1]))
            elif comandlist[0] == "mar":
                margin = ""
                if comandlist[1] == "0": margin = "CROSSED"
                elif comandlist[1] == "1": margin = "ISOLATED"
                bot.marginType_metod(margin)
                bot.getmargimleverage()
            elif comandlist[0] == "lev":
                bot.leverage_metod(int(comandlist[1]))
                bot.getmargimleverage()
            elif comandlist[0] == "co":
                if comandlist[1] == "sl":
                    for i in bot.openorderlist:
                        if i[0] == "STOP_MARKET":
                              bot.deleteorder(i[1])
                if comandlist[1] == "tp":
                    for i in bot.openorderlist:          
                        if i[0] == "TAKE_PROFIT_MARKET":
                              bot.deleteorder(i[1])
            elif comandlist[0] == 'as':
                if comandlist[1] == '0':
                    bot.autostoplloson = False
                else:
                    bot.stopval = float(comandlist[1])
                    bot.autostoplloson = True
            elif comand[0] == 'l':
                side = ""
                if comandlist[1] == "s": side = "SELL"
                elif comandlist[1] == "b": side = "BUY"
                bot.postopenorder(side = side, quantity = float(comandlist[2]), typeorder = "LIMIT", price = float(comandlist[3]))
        bot.logs.append(comand)
        comand = None
        await asyncio.sleep(0.1)              
            
            
if __name__ == "__main__":
    symbol = input("symbol: ")
    #symbol = "btcusdt"
    bot = BB(symbol)
    bot.getinfo()
    bot.getmargimleverage()
    loop = asyncio.get_event_loop()
    loop.create_task(bot.getcurentprice())
    loop.create_task(bot.getopenposition())
    loop.create_task(bot.autostopllos())
    loop.create_task(generate_layaut(bot))
    loop.create_task(asyncinput(bot))
    loop.run_forever()