

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from operator import itemgetter
from statsmodels.api import OLS
from statsmodels.tsa.stattools import coint, adfuller
from hurst import compute_Hc as hurst_exponent
from scipy.stats import zscore

from sklearn.cluster import OPTICS
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler, StandardScaler


from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.pntx import TwoPointCrossover
from pymoo.operators.mutation.bitflip import BitflipMutation
from pymoo.operators.sampling.rnd import BinaryRandomSampling
from pymoo.optimize import minimize

from tqdm import tqdm
# from tqdm.auto import tqdm  # notebook compatible
import time



class Pairs:

    """
    A class used to represent trading Pairs

    """
    __PLOT=False

    def __init__(self, data):

        
        self.__all_pairs = []
        self.__data = data
        self.__tickers = data.keys()
        self.__start = data.index[0]._date_repr
        self.__end = data.index[-1]._date_repr

    def __is_stationary(self,signal, threshold):

        signal=np.asfarray(signal)
        return True if adfuller(signal)[1] < threshold else False

    
    def __nsga2(self):

    

        algorithm = NSGA2(pop_size=100,
                        sampling=BinaryRandomSampling(),
                        crossover=TwoPointCrossover(),
                        mutation=BitflipMutation(),
                        eliminate_duplicates=True)

        res = minimize(self.__cointegrated_pairs,
                    algorithm,
                    ('n_gen', 500),
                    seed=1,
                    verbose=False)


    def __distance_pairs(self,pair_number =  20):

        data = self.__data
        tickers = self.__tickers
        N = len(tickers)

        dic = {}

        
        for i in tqdm(range(N)):

            signal1 = data[tickers[i]]

            for j in range(i+1, N):

                signal2 = data[tickers[j]]
                
                ssd=sum((np.array(signal1) - np.array(signal2))**2)

                
                dic[tickers[i], tickers[j]]=ssd


        self.__all_pairs = list(dict(sorted(dic.items(), key = itemgetter(1))[:pair_number]).keys())

        

    def __cointegrated_pairs(self, pvalue_threshold = 0.05,hurst_threshold = 0.5):

        data = self.__data
        tickers = self.__tickers
        N = len(tickers)

        pairs = []

        for i in tqdm(range(N)):

            signal1 = data[tickers[i]]

            for j in range(i+1, N):

                signal2 = data[tickers[j]]
                
                if self.__Engle_Granger(signal1, signal2, pvalue_threshold, hurst_threshold):
                    pairs.append((tickers[i], tickers[j]))

        self.__all_pairs = pairs

    

    def __Engle_Granger(self, signal1, signal2, pvalue_threshold=0.05, hurst_threshold=0.5):

        beta = OLS(signal2, signal1).fit().params[0]
        spread = signal2-beta*signal1
        result = coint(signal1, signal2)
        score = result[0]
        pvalue = result[1]
        hurst, _, _ = hurst_exponent(spread)
  
        if(self.__PLOT and pvalue <= pvalue_threshold and hurst <= hurst_threshold):
            plt.figure(figsize=(12, 6))
            normalized_spread = zscore(spread)
            normalized_spread.plot()
            standard_devitation = np.std(normalized_spread)
            plt.axhline(zscore(spread).mean())
            plt.axhline(standard_devitation, color='green')
            plt.axhline(-standard_devitation, color='green')
            plt.axhline(2*standard_devitation, color='red')
            plt.axhline(-2*standard_devitation, color='red')
            plt.xlim(self.__start,
                     self.__end)
            plt.show()

        return True if pvalue <= pvalue_threshold and hurst <= hurst_threshold else False

    def find_pairs(self,model,verbose=False):

        function = {'COINT':self.__cointegrated_pairs,'DIST':self.__distance_pairs,}
        function[model]()
        
        if verbose:   
            print("\n************************************************\n",
                    "\nModel: ",model,
                    "\nTotal number of elements: ", len(self.__tickers),
                    "\nNumber of pairs: ", len( self.__all_pairs),
                    "\nNumber of unique elements in pairs: ",len( np.unique(self.__all_pairs)),
                    "\nPairs: ",self.__all_pairs,
                    "\n\n************************************************\n")
                    
        return self.__all_pairs


    # def __cointegrated_pairs(self):

    #     data = self.__data
    #     tickers = self.__tickers
    #     n_pairs = len(tickers)

    #     adfuller_threshold = 0.1
    #     pvalue_threshold = 0.05
    #     hurst_threshold = 0.5  # mean reversing threshold

    #     pairs = []

    #     for i in range(n_pairs):

    #         signal1 = data[tickers[i]]

    #         if self.__is_stationary(signal1, adfuller_threshold):

    #             for j in range(i+1, n_pairs):

    #                 signal2 = data[tickers[j]]

    #                 if self.__is_stationary(signal2, adfuller_threshold):
                
    #                     beta = OLS(signal2, signal1).fit().params[0]
    #                     spread = signal2-beta*signal1

    #                     if self.__is_stationary(spread, adfuller_threshold):

    #                         hurst, _, _ = hurst_exponent(spread)

                            
    #                         if hurst<hurst_threshold:
    #                             pairs.append((tickers[i], tickers[j]))

    #     self.__all_pairs = pairs




