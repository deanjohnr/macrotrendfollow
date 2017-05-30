# macrotrendfollow
Momentum and position based trading strategy analysis

### Summary
This project uses Google Finance and CFTC position data to measure and backtest various momentum and position based predictive factors. The system was designed to be a brute force method, letting the data determine the important factors. Predictive power of factors is measured by comparing forward asset returns of the top and bottom quantiles of each factor. Additionally, there is a parameter optimization process that gridsearches feature selection parameters such as factor counts, factor performance metrics, and factor performance thresholds.

### Trading Strategy
The actual trading strategy rebalances a portfolio every Tuesday at market close according to mean factor zscores for each asset. Portfolio returns are benchmarked against an even allocation of contributing assets that also rebalances every Tuesday at market close.

![alt text](https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 1")

### Default Results
Cloning and running should give a strategy that produces the following 2016 backtest results:

| Portfolio Return | 10.7% |
| Index Return | -4.6% |
| Excess Return | 15.3% |

#### Strategy
The strategy trades X assets, 
|        asset     | feature |
-------------------------------
|    INDEXCBOE:SPX |              Change_in_Lev_Money_Spread_All |  
|    INDEXCBOE:SPX |          ma_Traders_Other_Rept_Long_All_100 |  
|    INDEXCBOE:SPX |      momo_Pct_of_OI_Asset_Mgr_Spread_All_20 |  
|    INDEXCBOE:SPX |         ma_Change_in_Asset_Mgr_Short_All_20 |  
|    INDEXCBOE:SPX |        ma_Traders_Dealer_Long_Short_Diff_20 |  
|    INDEXCBOE:SPX |          mo_Change_in_Tot_Rept_Short_All_20 |  
|    INDEXCBOE:SPX |          ma_Change_in_Dealer_Spread_All_100 |  
|    INDEXCBOE:SPX |                ma_Traders_Dealer_Net_20/100 |  
|    INDEXCBOE:SPX |      ma_Change_in_Dealer_Short_Ratio_20/100 |  
|    INDEXCBOE:SPX |                momo_Pct_of_OI_Dealer_Net_20 |  
|INDEXDJX:USDOLLAR |          ma_Change_in_Dealer_Short_Ratio_20 |  
|INDEXDJX:USDOLLAR |           mo_Pct_of_OI_NonRept_Short_All_20 |  
|  INDEXNASDAQ:NDX | momo_Pct_of_OI_Asset_Mgr_Long_Short_Diff_20 |  
|INDEXNIKKEI:NI225 |        ma_Change_in_Lev_Money_Spread_All_20 |  
| INDEXNYSEGIS:MID |          ma_Change_in_Dealer_Spread_All_100 |  
|     NYSEARCA:DJP |                               momo_Close_20 |  
|     NYSEARCA:DJP |                                momo_High_20 |  
|     NYSEARCA:DJP |                                momo_Open_20 |  
|     NYSEARCA:DJP |                              ma_Open_20/100 |  
|     NYSEARCA:DJP |                              ma_High_20/100 |  
|     NYSEARCA:DJP |                               ma_Low_20/100 |  
|     NYSEARCA:EFA |      ma_Lev_Money_Positions_Long_All_20/100 |  
|     NYSEARCA:VXX |                Traders_Other_Rept_Short_All |

### How To Execute

```python build_factors.py```

```python test_factors.py```
Outputs ```results/parameter_returns.csv```, which can be analyzed to find best factor selection parameters. These parameters can then be used to analyze the resulting strategy.

### Code Breakdown
#### Section 1
* Scrapes data from Google Finance
* Loads CFTC data
* Cleans date
* Defines feature set

#### Section 2
* Builds features
* Calculates rolling bin and zscore factors for each feature
* Records quantile returns for each bin factor
* Records test data for backtesting

#### Section 3
* Performs factor selection parameter gridsearch to optimize backtest returns
