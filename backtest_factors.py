### backtest_factors.py ###
import pandas as pd
import numpy as np
import time
import datetime
import json

# Measures returns of feature selection parameters
def get_returns(df_result,
                df_test,
                forward_period,
                factor_type,
                factor_top_count,
                minimum_sample_size,
                factor_threshold,
                minimum_asset_pct):
    
    min_quantile = df_result['factor_bucket'].min()
    max_quantile = df_result['factor_bucket'].max()

    # Filter to minimum sample count
    df_result = df_result[df_result[str(forward_period)+'_count'] >= 30]
    
    # Set Factor Measure
    factor_measure = str(forward_period)+'_'+factor_type

    # Compute difference between max and min quantiles
    df_meandiff = (df_result[df_result['factor_bucket'] == max_quantile][[factor_measure]]
                    - df_result[df_result['factor_bucket'] == min_quantile][[factor_measure]])

    # Filter to top factors with minimum score
    df_top = df_meandiff.sort_values(factor_measure, ascending=False).reset_index().groupby('asset').head(factor_top_count).sort_values(['asset',factor_measure])
    df_top = df_top[df_top[factor_measure] >= factor_threshold]
    df_bot = df_meandiff.sort_values(factor_measure, ascending=False).reset_index().groupby('asset').tail(factor_top_count).sort_values(['asset',factor_measure])
    df_bot = df_bot[df_bot[factor_measure] <= -factor_threshold]

    # Output final set of features
    df_algofeatures = df_top.append(df_bot).sort_values('asset')
    
    asset_pct = float(len(df_algofeatures['asset'].drop_duplicates()))/float(len(df_test['asset'].drop_duplicates()))
    if asset_pct < minimum_asset_pct:
        return None
    
    # Join test data and chosen features
    df_backtest = df_test.reset_index().merge(df_algofeatures[['asset','feature',factor_measure]],
                                              how='inner', left_on=['asset','feature'], right_on=['asset','feature'])
    
    # Cap scores to limit position size skew and clean infinite numbers
    df_backtest.loc[df_backtest['factor_zscore'] > 3,'factor_zscore'] = 3
    df_backtest.loc[df_backtest['factor_zscore'] < -3,'factor_zscore'] = -3
    
    # Determine long/short direction of the factor
    df_backtest['direction'] = df_backtest['factor_zscore']/df_backtest['factor_zscore'].abs()

    # Use scores as portfolio asset weighting
    df_backtest['asset_weight'] = df_backtest['factor_zscore']*df_backtest['direction']
    df_backtest = df_backtest.dropna()
    df_backtest = df_backtest.groupby(['date','asset'])[['asset_weight',target]].mean()
    df_backtest['gross_weight'] = df_backtest['asset_weight'].abs()
    df_denom = df_backtest.groupby(['date'])[['gross_weight']].sum()
    df_count = df_backtest.groupby(['date'])[['asset_weight']].count()
    df_backtest = df_backtest.merge(df_denom, left_index=True, right_index=True, suffixes=['','_sum'])
    df_backtest = df_backtest.merge(df_count, left_index=True, right_index=True, suffixes=['','_count'])

    df_backtest['portfolio_weight'] = (df_backtest['asset_weight']/(df_backtest['gross_weight_sum']))

    # Add uniform index weights to compare returns
    df_backtest['index_weight'] = 1.0/df_backtest['asset_weight_count']
    
    df_backtest = df_backtest.reset_index()

    # Limits to Tuesdays for rebalancing
    df_backtest['dayofweek'] = df_backtest['date'].apply(lambda x: pd.to_datetime(x).dayofweek)
    df_backtest = df_backtest[df_backtest['dayofweek']==1].set_index(keys=['date','asset'])

    # Calculate weekly returns
    df_backtest['portfolio_return'] = df_backtest[target].unstack().pct_change(1).shift(-1).stack() * df_backtest['portfolio_weight']
    df_backtest['index_return'] = df_backtest[target].unstack().pct_change(1).shift(-1).stack() * df_backtest['index_weight']

    # Calculate cumulative returns
    df_return = df_backtest.groupby(['date'])[['portfolio_return','index_return']].sum()
    df_value = df_return.rolling(window=len(df_return), min_periods=1).apply(lambda x: np.prod(1 + x))-1
    df_return = df_return.merge(df_value, how='inner', left_index=True, right_index=True)

    # Calculate returns in excess of index
    df_return['excess_return'] = df_return['portfolio_return_y']-df_return['index_return_y']

    # Plot Returns
    df_result = df_return[['portfolio_return_y','index_return_y','excess_return']].dropna().tail(1)
    df_result['forward_period'] = forward_period
    df_result['factor_type'] = factor_type
    df_result['factor_top_count'] = factor_top_count
    df_result['minimum_sample_size'] = minimum_sample_size
    df_result['factor_threshold'] = factor_threshold
    df_result['minimum_asset_pct'] = minimum_asset_pct
    df_result['asset_pct'] = asset_pct
    return df_result


### INITIALIZE CONFIGURATION ###
factor_types = None
factor_top_counts = [5,10,20]
minimum_sample_sizes = [10,30,100,200]
factor_thresholds = [0.01,0.03,0.8,1.0,1.2]
minimum_asset_pct = 0.5

### LOAD CONFIGURATION ###
# Load Configuration File #
try:
    with open('config.json') as config_file:    
        config = json.load(config_file)
except:
    print('Error loading config.json file')
    raise

# Assign Configuration Variables #

# Target field, normally price
try:
    target = str(config['data']['google']['target'])
except:
    print('Error configuring algorithm target')
    raise

# Factor Measurement Types
try:
    factor_types = np.array(config['backtest']['factor']['factor_types'])
except:
    print('Error configuring factor measurement types')
    raise

# Factor Rank Top Selection Count
try:
    factor_top_counts = np.array(config['backtest']['factor']['factor_top_counts'])
except:
    pass
    
# Factor Rank Top Selection Count
try:
    factor_thresholds = np.array(config['backtest']['factor']['factor_thresholds'])
except:
    pass

# Factor Minimum Sample Size
try:
    minimum_sample_sizes = np.array(config['backtest']['factor']['minimum_sample_sizes'])
except:
    pass

# Factor Minimum Usable Asset Percentage
try:
    minimum_asset_pct = float(config['backtest']['factor']['minimum_asset_pct'])
except:
    pass

# Get Forward Looking Return Periods
try:
    forward_periods = np.array(config['measurement']['forward_periods'])
except:
    print('Error configuring forward periods')
    raise

# Load test data
df_test = pd.read_csv('results/test/test_data.csv')

# Load factor data
df_result = pd.DataFrame()
tickers = df_test['asset'].drop_duplicates().values
for ticker in tickers:
    df_result = df_result.append(pd.read_csv('results/factors/'+ticker+'_factors.csv'))
df_result = df_result.set_index(keys=['asset','feature'], drop=False)

denom = float(len(forward_periods)*len(factor_types)*len(factor_top_counts)*len(minimum_sample_sizes)*len(factor_thresholds))
print('Permutations: '+str(denom))

df_parameter = pd.DataFrame()
i = 0
for forward_period in forward_periods:
    for factor_type in factor_types:
        for factor_top_count in factor_top_counts:
            for minimum_sample_size in minimum_sample_sizes:
                for factor_threshold in factor_thresholds:
                    returns = get_returns(df_result,
                                          df_test,
                                          forward_period,
                                          factor_type,
                                          factor_top_count,
                                          minimum_sample_size,
                                          factor_threshold,
                                          minimum_asset_pct)
                    i += 1
                    if i%10 == 0:
                        print(str(round(i/denom,2)))
                    if returns is not None:
                        df_parameter = df_parameter.append(returns)

print('Storing Results')
df_parameter.to_csv('results/parameter_returns.csv')
print('Complete')