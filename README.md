# macrotrendfollow

### Summary
This project aims to measure and backtest various momentum and position based predictive factors from Google Finance and CFTC position data for 8 tickers. The system was designed to be a brute force method, letting the data determine the important factors. Predictive power of factors is measured by comparing forward asset returns of the top and bottom quantiles of each factor. Additionally, there is a parameter optimization process that gridsearches feature selection parameters such as factor counts, factor performance metrics, and factor performance thresholds. Below is a walkthrough of the process that led to a manual analysis that proved more valuable than automation, resulting in a trading strategy that consistently produces returns in excess of the index based on a 2016 backtest.

### Trading Strategy
The actual trade execution strategy rebalances a portfolio every Tuesday at market close according to mean factor zscores for each asset. Portfolio returns are benchmarked against an even allocation of contributing assets that also rebalances every Tuesday at market close. The trading return results assume no execution slippage or transactions fees.

### Automated Method
(see bottom for code commentary)

Although the process is fairly robust in building and examining a large number of features, the asset level quantile difference method for measuring feature significance returns poor results. In theory the default process should choose factors that are predictive of both long and short returns resulting in excess returns over the benchmark, but the parameter permutation results show an average negative excess return across nearly all parameter types. This means that the current feature selection process is not selecting significant feature combinations.

Parameter permutation average returns by factor type:

| Factor Type | Portfolio Return | Index Return | Excess Return |
|---|:---:|:---:|:---:|
| mean | -5.0% | -4.6% | -0.4% |
| zscore | -5.3% | -3.8% | -1.5% |

### Manual Analysis

#### Generalize
Given the poor mean results, there is something wrong with the feature selection method. The first thought is a potential overfitting problem because feature selection chooses the features with the most significant signal or return for a given asset. Averaging feature results across assets should generalize the results and reduce variance. However, purely averaging across the assets and running the same automated selection of top 20 features resulted in negative excess returns.

#### Feature Groups
Adding intuitiion to the equation, the feature groups of momentum (mo), derivative momentum (momo), and short over long moving average (20/100) features are likely be better indicators of future returns than simple moving average features because the features capture changes in trends. Averaging z scores by feature group, forward return direction, and qunatile we start to see evidence of signals.

This graph shows the mean quantile z score for long derivative momentum features. The bowl shape of the graph indicates that values farther from the median are more predictive of forward returns than values near the median.

![alt text](https://github.com/deanjohnr/macrotrendfollow/blob/master/analysis/bowlchart.png?raw=true "mean quantile z score for long derivative momentum features")

Using this we can narrow in on several features that are likely to produces returns in excess of the index. Leveraging the asset generalization logic to find derivative momentum features with superior historical performace across assets, the resulting feature set produces returns in excess of the index.

| Feature List |
|---|
| momo_Close_20 |
| momo_Dealer_Positions_Long_All_20 |
| momo_Pct_of_OI_Dealer_Long_All_20|
| momo_Conc_Gross_LE_4_TDR_Short_All_20 |
| momo_Pct_of_OI_Lev_Money_Net_20 |
| momo_Pct_of_OI_Lev_Money_Short_Ratio_20 |
| momo_Pct_of_OI_Other_Rept_Long_All_20 |

Backtested Returns

| Metric | 2016 Return |
|---|:---:|
| Portfolio Return | -0.8% |
| Index Return | -4.6% |
| Excess Return | 3.8% |

Backtested Returns Plot

![alt text](https://github.com/deanjohnr/macrotrendfollow/blob/master/analysis/momoreturns.png?raw=true "2016 returns")

### Conclusion
Manual analysis guided by intuition produced the best feature selection results. This feature selection method could then be incorporated into the automated system to potentially produce better automated strategy building. The most predictive feature types were relative moving average and derivative momentum. Leveraging the config file system it would be easy, but time consuming, to thoroughly explore the effect of time periods on these two features. Overall the CFTC data seems to have fairly strong predictive power that is capable of producing returns that beat the benchmark.

#### Next Steps
* Rebuild the automated feature selection logic to add more generalization
* Gridsearch optimal period lengths for moving average and momentum features
* Build cross investor type features
* Build machine learning based ensemble features

### Automated Results
Cloning and running should give a strategy that produces the following 2016 backtest results:

![alt text](https://github.com/deanjohnr/macrotrendfollow/blob/master/results/returns.png?raw=true "Returns plot")

| Metric | 2016 Return |
|---|:---:|
| Portfolio Return | 10.7% |
| Index Return | 8.6% |
| Excess Return | 2.1% |

#### Winning Feature Selection

| Asset | Feature |
|---|:---:|
|     INDEXCBOE:SPX |              ma_Other_Rept_Positions_Net_20 |
|     INDEXCBOE:SPX |        Pct_of_OI_Other_Rept_Long_Short_Diff |
|     INDEXCBOE:SPX |                    Pct_of_OI_Other_Rept_Net |
|     INDEXCBOE:SPX |  ma_Pct_of_OI_Other_Rept_Long_Short_Diff_20 |
|     INDEXCBOE:SPX |              ma_Pct_of_OI_Lev_Money_Net_100 |
|     INDEXCBOE:SPX |        Other_Rept_Positions_Long_Short_Diff |
|     INDEXCBOE:SPX |  ma_Other_Rept_Positions_Long_Short_Diff_20 |
|     INDEXCBOE:SPX |                    Other_Rept_Positions_Net |
|     INDEXCBOE:SPX |              ma_Lev_Money_Positions_Net_100 |
|     INDEXCBOE:SPX |       ma_Pct_of_OI_Lev_Money_Spread_All_100 |
|   INDEXNASDAQ:NDX |         ma_Traders_Other_Rept_Short_All_100 |
|   INDEXNASDAQ:NDX |                                        High |
|   INDEXNASDAQ:NDX |                                         Low |
|   INDEXNASDAQ:NDX |                                        Open |
| INDEXNIKKEI:NI225 |       ma_Change_in_Lev_Money_Spread_All_100 |
| INDEXNIKKEI:NI225 |               mo_Change_in_Lev_Money_Net_20 |
| INDEXNIKKEI:NI225 |               Pct_of_OI_Other_Rept_Long_All |
| INDEXNIKKEI:NI225 | ma_Change_in_Other_Rept_Long_Short_Diff_100 |
| INDEXNIKKEI:NI225 |   ma_Change_in_Asset_Mgr_Short_Ratio_20/100 |
| INDEXNIKKEI:NI225 |             ma_Change_in_Other_Rept_Net_100 |
| INDEXNIKKEI:NI225 |         ma_Pct_of_OI_Asset_Mgr_Long_All_100 |
| INDEXNIKKEI:NI225 |           ma_Pct_of_OI_NonRept_Long_All_100 |
| INDEXNIKKEI:NI225 |  ma_Pct_of_OI_Asset_Mgr_Long_Short_Diff_100 |
| INDEXNIKKEI:NI225 |                    Pct_of_OI_Other_Rept_Net |
|  INDEXNYSEGIS:MID |      mo_Pct_of_OI_Dealer_Long_Short_Diff_20 |
|  INDEXNYSEGIS:MID |      mo_Dealer_Positions_Long_Short_Diff_20 |
|  INDEXNYSEGIS:MID |       ma_Change_in_Asset_Mgr_Spread_All_100 |
|  INDEXNYSEGIS:MID |               Conc_Gross_LE_8_TDR_Short_All |
|  INDEXNYSEGIS:MID |    ma_Traders_Asset_Mgr_Long_Short_Diff_100 |
|  INDEXNYSEGIS:MID |         ma_Change_in_Dealer_Short_Ratio_100 |
|  INDEXNYSEGIS:MID |     ma_Change_in_Other_Rept_Short_Ratio_100 |
|  INDEXNYSEGIS:MID |        ma_Traders_Dealer_Short_Ratio_20/100 |
|  INDEXNYSEGIS:MID |                  mo_Pct_of_OI_Dealer_Net_20 |
|  INDEXNYSEGIS:MID |             Change_in_Lev_Money_Short_Ratio |
|      NYSEARCA:DJP |                               ma_Low_20/100 |
|      NYSEARCA:DJP |                              ma_High_20/100 |
|      NYSEARCA:DJP |                              ma_Open_20/100 |
|      NYSEARCA:DJP |                             ma_Close_20/100 |
|      NYSEARCA:DJP |                                        High |
|      NYSEARCA:DJP |                                  ma_Open_20 |
|      NYSEARCA:DJP |                                        Open |
|      NYSEARCA:DJP |                                 ma_Close_20 |
|      NYSEARCA:DJP |                                         Low |
|      NYSEARCA:DJP |                                   ma_Low_20 |
|      NYSEARCA:EFA |                             ma_Close_20/100 |
|      NYSEARCA:EFA |                              ma_Open_20/100 |
|      NYSEARCA:EFA |                              ma_High_20/100 |
|      NYSEARCA:EFA |                               ma_Low_20/100 |

#### Feature Key

| Code | Meaning |
|---|:---:|
| ma | Moving Average |
| mo | Trailing Period Change |
| momo | Trailing Period Change in Change |
| 20 | 20 Trading Day Period |
| 20/100 | 20 Trading Day over 100 Trading Day |
| Long_Short_Diff | Long - Short |
| Short_Ratio | Short / Gross Total |
| Net | Net Position |

### Code Commentary

#### Configuration
The system contains a `config.json` file that controls the data inputs, feature building, and back testing parameter search. Each main python script starts by initializing and importing the configuration.

#### Data Gathering
The first section of code is devoted to gathering data. The only way to consume price data for the set of 8 tickers was to build a customer Google finance scraper, `get_prices()`. Google doesn't have downloadable history for most tickers so the custom scraper was necessary. The Yahoo Finance API is broken, the Quandl data doesn't go back far enough in time, and Quantopian doesn't give users the ability to export data from their system.

The CFTC data was manually downloaded, unzipped, and made available for loading into a data frame. A more robust system would pull the file directly in the script, unzip to a temporary location for loading. This was attempted, but there was an issue with the various urlib modules that kept raising errors.

#### Data Cleaning
Data cleaning is pretty straight forward, using two functions, `clean_columns` and `clean_outliers`. `clean_columns` checks each data column to ensure majority of the column contains numeric values and rejects bad columns. `clean_outliers` searches the data for outlier values and replaces them with a local median.

#### Feature Building
Feature building is broken into 3 main pieces, CFTC feature manipulation, momentum, and moving average permutation. The CFTC feature manipulation builds intra investor type features such as short ratio and net exposure. The momentum section builds two feature types, vanilla momentum, a trailing price change metric, and derivative momentum, a trailing change in price change metric. The moving average permutation iterates through the defined configuration, building short term versus long term moving average features.

#### Factor Building
That last piece of building code creates the trailing feature z scores and bins and stores the mean returns associated with each asset, feature, and bin combination. The last step stores the historical results data and the price data for backtesting.

#### Feature Selection and Backtesting
The final step runs a gridsearch on feature selection parameters, backtesting each permutaion, and storing the results for analysis.

### Execution
This takes over an hour:
```
python build_factors.py
```
* Scrapes data from Google Finance
* Loads CFTC data
* Cleans data
* Builds features
* Calculates rolling bin and zscore factors for each feature
* Records quantile returns and test date for backtesting
* Records test data for backtesting

```
python backtest_factors.py
```
* Performs factor selection parameter gridsearch and outputs backtest returns
Results in `results/parameter_returns.csv`.
