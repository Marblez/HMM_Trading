import operator
from math import ceil,floor


class GrowthMultifactor(QCAlgorithm):

    def Initialize(self):
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Cash)
        self.SetStartDate(2014, 12, 1)  # Set Start Date
        self.SetEndDate(2017, 10, 1)    # Set End Date
        self.SetCash(100000)          # Set Strategy Cash
        self.flag1 = 1
        self.flag2 = 0
        self.flag3 = 0
        self.UniverseSettings.Resolution = Resolution.Minute
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
        self.AddEquity("SPY")
        self.numberOfSymbols = 300
        self.numberOfSymbolsFine = 10
        self.num_portfolios = 6
        self._changes = None
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.AfterMarketOpen("SPY"), Action(self.Rebalancing))
        self.Schedule.On(self.DateRules.EveryDay(), \
                 self.TimeRules.BeforeMarketClose("SPY"), \
                 self.MarketClose)
        self.daily_return = 0
        self.prev_value = self.Portfolio.TotalPortfolioValue

    def CoarseSelectionFunction(self, coarse):
        if self.flag1:
            CoarseWithFundamental = [x for x in coarse if x.HasFundamentalData]
            sortedByDollarVolume = sorted(CoarseWithFundamental, key=lambda x: x.DollarVolume, reverse=True)
            top = sortedByDollarVolume[:self.numberOfSymbols]
            return [i.Symbol for i in top]
        else:
            return []


    def FineSelectionFunction(self, fine):
        if self.flag1:
            self.flag1 = 0
            self.flag2 = 1

            filtered_fine = [x for x in fine if x.EarningReports.TotalDividendPerShare.ThreeMonths
                                            and x.ValuationRatios.PriceChange1M
                                            and x.ValuationRatios.BookValuePerShare
                                            and x.ValuationRatios.FCFYield]

            sortedByfactor1 = sorted(filtered_fine, key=lambda x: x.EarningReports.TotalDividendPerShare.ThreeMonths, reverse=True)
            sortedByfactor2 = sorted(filtered_fine, key=lambda x: x.ValuationRatios.PriceChange1M, reverse=False)
            sortedByfactor3 = sorted(filtered_fine, key=lambda x: x.ValuationRatios.BookValuePerShare, reverse=True)
            sortedByfactor4 = sorted(filtered_fine, key=lambda x: x.ValuationRatios.FCFYield, reverse=True)

            num_stocks = floor(len(filtered_fine)/self.num_portfolios)

            stock_dict = {}

            for i,ele in enumerate(sortedByfactor1):
                rank1 = i
                rank2 = sortedByfactor2.index(ele)
                rank3 = sortedByfactor3.index(ele)
                rank4 = sortedByfactor4.index(ele)
                score = [ceil(rank1/num_stocks),
                         ceil(rank2/num_stocks),
                         ceil(rank3/num_stocks),
                         ceil(rank4/num_stocks)]
                score = sum(score)
                stock_dict[ele] = score
            #self.Log("score" + str(score))
            self.sorted_stock = sorted(stock_dict.items(), key=lambda d:d[1],reverse=True)
            sorted_symbol = [self.sorted_stock[i][0] for i in range(len(self.sorted_stock))]
            topFine = sorted_symbol[:self.numberOfSymbolsFine]

            self.flag3 = self.flag3 + 1

            return [i.Symbol for i in topFine]

        else:
            return []


    def OnData(self, data):
        if self.flag3 > 0:
            if self.flag2 == 1:
                self.flag2 = 0
                # if we have no changes, do nothing
                if self._changes == None: return
                # liquidate removed securities
                for security in self._changes.RemovedSecurities:
                    if security.Invested:
                        self.Liquidate(security.Symbol)

                for security in self._changes.AddedSecurities:
                    self.SetHoldings(security.Symbol, 0.8/float(len(self._changes.AddedSecurities)))

                self._changes = None

    # this event fires whenever we have changes to our universe
    def OnSecuritiesChanged(self, changes):
        self._changes = changes

    def Rebalancing(self):
        self.flag1 = 1

    def MarketClose(self):
        self.daily_return = 100*((self.Portfolio.TotalPortfolioValue - self.prev_value)/self.prev_value)
        self.prev_value = self.Portfolio.TotalPortfolioValue
        self.Log(self.daily_return)
        return
