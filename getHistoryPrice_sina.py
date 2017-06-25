import urllib.request
import re
import datetime
import decimal
from html.parser import HTMLParser
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s')


def getHistoryTradeData_CQ(symbol, end_date=r'end_date=99999999', begin_date=r'begin_date=00000000'):
    location = r'http://biz.finance.sina.com.cn/stock/flash_hq/kline_data.php'
    symbolAssembled  = r'symbol=' + symbol
    historyDataCQ_url = location + r'?&' + symbolAssembled + r'&' + end_date + r'&' + begin_date
    logging.info('request: ' + historyDataCQ_url)

    req = urllib.request.Request(historyDataCQ_url)
    response = urllib.request.urlopen(req)
    the_page = response.read()
    contain = str(the_page).split(r'\n\t')

    parsedData = []
    parsedData.append([r'日期', r'开盘价', r'最高价', r'收盘价', r'最低价', r'成交量'])

    pattern = re.compile(r'<content d="(\d{4}-\d{2}-\d{2})" o="(\d*\.\d*?)" h="(\d*\.\d*?)" '
                         r'c="(\d*\.\d*?)" l="(\d*\.\d*?)" v="(\d*?)" bl="" />')

    for line in contain:
        historyData = pattern.findall(line)
        if len(historyData) < 1:
            continue
        if len(historyData[0]) < 6:
            logging.error("ERROR DATA")
            continue;
        date = datetime.datetime.strptime(historyData[0][0], '%Y-%m-%d').date()
        decimal.getcontext().prec = 3
        opnPrice = decimal.Decimal(historyData[0][1])
        hghPrice = decimal.Decimal(historyData[0][2])
        clsPrice = decimal.Decimal(historyData[0][3])
        lowPrice = decimal.Decimal(historyData[0][4])
        volmsLot = int(historyData[0][5])
        parsedData.append([date, opnPrice, hghPrice, clsPrice, lowPrice, volmsLot])
        logging.debug(parsedData[-1])
    return parsedData


QFQ_HFQ = {'qfq':'qfq', 'hfq':'hfq'}


def getHistoryFqFactor(symbol, qfq_hfq):
    if qfq_hfq != 'qfq' and qfq_hfq != 'hfq':
        return None

    location = r'http://finance.sina.com.cn/realstock/newcompany/'
    qfqFactor_url = location + symbol + r'/p' + qfq_hfq + r'.js'
    logging.info('request: ' + qfqFactor_url)

    req = urllib.request.Request(qfqFactor_url)
    response = urllib.request.urlopen(req)
    the_page = response.read()
    contain = str(the_page).split(r',')

    parsedData = []
    parsedData.append([r'日期', r'前复权因子'])

    pattern = re.compile(r'_(\d{4}_\d{2}_\d{2}):"(\d*\.\d*?)"')

    for line in contain:
        historyData = pattern.findall(line)
        if len(historyData) < 1:
            continue
        date = datetime.datetime.strptime(historyData[0][0], '%Y_%m_%d').date()
        decimal.getcontext().prec = 6
        qfqFactor = decimal.Decimal(historyData[0][1])
        parsedData.append([date, qfqFactor])
        logging.debug(parsedData[-1])
    return parsedData


def getHistoryFhData(symbol):
    location = r'http://money.finance.sina.com.cn/corp/go.php/vISSUE_ShareBonus/stockid/'
    symbolBrief = symbol[-6:]
    historyFh_url = location + symbolBrief + r'.phtml'
    logging.info('request: ' + historyFh_url)

    req = urllib.request.Request(historyFh_url)
    response = urllib.request.urlopen(req)
    the_page = response.read().decode("gb2312")

    tableBgnPos = the_page.find(r'<table id="sharebonus_1">')
    tableEndPos = the_page.find(r'</table>', tableBgnPos)
    pageNeedParse = the_page[tableBgnPos:tableEndPos]
    logging.debug(pageNeedParse)

    class parseFH(HTMLParser):
        parsedData = []
        __isDataStart = False
        __isReady4Data = False
        __isGettingData = False
        __tmpData = []
        __count = 0

        def __init__(self):
            print(self.__class__.__module__)
            HTMLParser.__init__(self)
            self.parsedData.append([r'公告日期', r'股权登记日', r'送股(10股)', r'转增(10股)', r'派息(10股)税前'])

        def handle_starttag(self, tag, attrs):
            if tag == 'tbody':
                self.__isDataStart = True
            if self.__isDataStart is True and tag == 'tr':
                self.__isReady4Data = True
                self.__tmpData.clear()
                self.__count = 0
            if self.__isReady4Data is True and tag == 'td':
                self.__isGettingData = True

        def handle_endtag(self, tag):
            if tag == 'tbody':
                self.__isDataStart = False
            if self.__isDataStart is True and tag == 'tr':
                self.__isReady4Data = False
                import copy
                self.parsedData.append(copy.deepcopy(self.__tmpData))
            if self.__isReady4Data is True and tag == 'td':
                self.__isGettingData = False
                self.__count = self.__count + 1

        def handle_data(self, data):
            if self.__isGettingData is True:
                logging.debug("分红方案 :" + str(data))
                if self.__count in [0, 1, 2, 3]:
                    self.__tmpData.append(data)
                if self.__count in [6]:
                    self.__tmpData.insert(1, data)

    parseFhHtml = parseFH()
    parseFhHtml.feed(pageNeedParse)
    return parseFhHtml.parsedData


if __name__ == "__main__":
    historyTradeData = getHistoryTradeData_CQ('sz000333')
    #logging.info(historyTradeData)

    historyQfqFactorData = getHistoryFqFactor('sz000333', QFQ_HFQ['qfq'])
    historyQfqFactorData = getHistoryFqFactor('sz000333', QFQ_HFQ['hfq'])
    #logging.info(historyQfqFactorData)

    historyFhData = getHistoryFhData(r'sz000333')
    logging.info(historyFhData)
