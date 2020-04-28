from QuantConnect.Data.UniverseSelection import *

class LongShortBookValue(QCAlgorithm):

    def __init__(self):
    # set the flag for rebalance
        self.reb = 1
    # Number of stocks to pass CoarseSelection process
        self.num_coarse = 500
    # Number of stocks to long/short
        self.winsorize = 10
        self.num_fine = 50
        self.symbols = None
    # Return
        self.daily_return = 0
        self.prev_value = self.Portfolio.TotalPortfolioValue

    def Initialize(self):
        self.SetWarmup(timedelta(20))
        self.SetCash(100000)
        self.SetStartDate(2014, 12, 1)
        self.SetEndDate(2017, 10, 1)
        #self.SetEndDate(2016,12,5)

        self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol

        self.UniverseSettings.Resolution = Resolution.Daily

        self.AddUniverse(self.CoarseSelectionFunction,self.FineSelectionFunction)

    # Schedule the rebalance function to execute at the begining of each month
        self.Schedule.On(self.DateRules.MonthStart(self.spy),
        self.TimeRules.AfterMarketOpen(self.spy,5), Action(self.rebalance))

        self.Schedule.On(self.DateRules.EveryDay(), \
                 self.TimeRules.BeforeMarketClose("SPY"), \
                 self.MarketClose)

    def CoarseSelectionFunction(self, coarse):
    # if the rebalance flag is not 1, return null list to save time.
        if self.reb != 1:
            return self.long + self.short

    # make universe selection once a month
    # drop stocks which have no fundamental data or have too low prices
        selected = [x for x in coarse if (x.HasFundamentalData)
                    and (float(x.Price) > 5)]

        sortedByDollarVolume = sorted(selected, key=lambda x: x.DollarVolume, reverse=True)
        top = sortedByDollarVolume[:self.num_coarse]
        return [i.Symbol for i in top]

    def FineSelectionFunction(self, fine):
    # return null list if it's not time to rebalance
        if self.reb != 1:
            return self.long + self.short

        self.reb = 0

    # drop stocks which don't have the information we need.
    # you can try replacing those factor with your own factors here

        filtered_fine = [x for x in fine if x.ValuationRatios.BookValuePerShare]

        # rank stocks by three factor.
        sortedByfactor = sorted(filtered_fine, key=lambda x: x.ValuationRatios.BookValuePerShare, reverse=True)
        sortedByfactor = sortedByfactor[self.winsorize:]
        sortedByfactor = sortedByfactor[:len(sortedByfactor)-self.winsorize]
        stock_dict = {}

        # assign a score to each stock, you can also change the rule of scoring here.
        for i,ele in enumerate(sortedByfactor):
            rank = i
            stock_dict[ele] = rank

        # sort the stocks by their scores
        self.sorted_stock = sorted(stock_dict.items(), key=lambda d:d[1],reverse=False)
        sorted_symbol = [x[0] for x in self.sorted_stock]

        # sotre the top stocks into the long_list and the bottom ones into the short_list
        self.long = [x.Symbol for x in sorted_symbol[:self.num_fine]]
        self.short = [x.Symbol for x in sorted_symbol[-self.num_fine:]]

        return self.long + self.short

    def OnData(self, data):
        pass

    def MarketClose(self):
        self.daily_return = 100*((self.Portfolio.TotalPortfolioValue - self.prev_value)/self.prev_value)
        self.prev_value = self.Portfolio.TotalPortfolioValue
        self.Log(self.daily_return)
        return

    def rebalance(self):
    # Liquidate all stocks at end of month
        self.Liquidate()

        for i in self.long:
            self.SetHoldings(i, 0.9/self.num_fine)

        for i in self.short:
            self.SetHoldings(i, -0.9/self.num_fine)

        self.reb = 1
