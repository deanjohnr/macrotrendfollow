### build_factors.py ###
import pandas as pd
import numpy as np
import time
import datetime
from lxml import html
import requests
import json

# Scrapes Google Finance for price data
def get_prices(tickers, startdate, enddate):
    
    #TODO: Add startdate and enddate validation
    
    df = pd.DataFrame()   #Initialize final data frame
    for ticker in tickers:
        
        df_ticker = pd.DataFrame()  #Initialize ticker data frame
        checkdate = enddate
        lastcheckdate = ''
        print('Retrieving data for ' + ticker + '...')
        while (checkdate != startdate) and (checkdate != lastcheckdate):
            # Build URL
            firstspace = startdate.index(' ')
            secondspace = startdate.index(' ',firstspace+1,-1)
            startdateurl = startdate[0:firstspace]+'+'+startdate[firstspace+1:secondspace]+'%2C+'+startdate[secondspace+1:]
            firstspace = checkdate.index(' ')
            secondspace = checkdate.index(' ',firstspace+1,-1)
            enddateurl = checkdate[0:firstspace]+'+'+checkdate[firstspace+1:secondspace]+'%2C+'+checkdate[secondspace+1:]
            url = """https://www.google.com/finance/historical?q="""+ticker+"""&startdate="""+startdateurl+"""&enddate="""+enddateurl+"""&num=200"""

            # Parse Page
            page = requests.get(url)
            tree = html.fromstring(page.content)
            prices = [td.text_content()[1:len(td.text_content())-1].replace(',','').split('\n') for td in tree.xpath('//div[@id="prices"]/table[@class="gf-table historical_price"]/tr')]

            try:
                tmpdf = pd.DataFrame(prices[1:], columns=prices[0])
            except:
                print(prices)
                raise
            
            lastcheckdate = checkdate
            checkdate = tmpdf.tail(1)['Date'].values[0]
            
            if checkdate != lastcheckdate:
                df_ticker = df_ticker.append(tmpdf).drop_duplicates()
        
        df_ticker['asset'] = ticker
        df_ticker['date'] = pd.to_datetime(df_ticker['Date'])
        df_ticker = df_ticker.drop('Date').set_index(keys=['date','asset'])
        
        df = df.append(df_ticker)
    print('Done retrieving data')
    return df

# Function to clean columns based on percentage of NaN values
def clean_columns(df, pctnan=0.2):
    df = df.select_dtypes(exclude=['object'])
    df = df.dropna(thresh=len(df)*pctnan, axis=1)
    return df

# Function to clean outliers
def clean_outliers(df, window=3, threshold=3):
    df_fill = df.rolling(window=3, center=False).median().fillna(method='bfill').fillna(method='ffill')
    df_diff = (df-df_fill).abs()
    mask = df_diff/df_diff.std() > threshold
    df[mask] = df_fill
    return df

### INITIALIZE CONFIGURATION ###
feature_columns = None
price_columns = None
momentum_columns = None
moving_average_columns = None
cftc_ignore = []
date_column = None
ticker_column = None

# Test Data Structure Default Variables
forward_periods = [10,20] # array of ints
quantiles = 5 # >= 2
train_end = pd.to_datetime('01/01/2016') # Set train and test split date

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

# CFTC Data
try:
    cftc_ticker = str(config['data']['cftc']['ticker'])
except:
    print('Error configuring CFTC ticker column')
    raise
    
try:
    cftc_date = str(config['data']['cftc']['date'])
except:
    print('Error configuring CFTC date columns')
    raise
    
try:
    res = config['data']['cftc']['ignore']
    if res is not None:
        cftc_ignore = res
except:
    cftc_ignore = []

# Tickers and CFTC mapping
try:
    tickers = config['data']['tickers']
except:
    print('Error configuring tickers')
    raise

# Feature Configuration

# Momentum
try:
    momentum_columns = config['features']['momentum']['columns']
except:
    pass

try:
    momentum_period = config['features']['momentum']['period']
except:
    pass

# Moving Average
try:
    moving_average_columns = config['features']['moving_average']['columns']
except:
    pass

try:
    moving_average_periods = config['features']['moving_average']['periods']
except:
    pass

# Google finance
try:
    price_columns = config['data']['google']['columns']
except:
    price_columns = [target]

# Measurement Period
try:
    start_date = config['measurement']['start_date']
except:
    print('Warning: using default start date Dec 1 2005')
    start_date = 'Dec 1 2005'

try:
    end_date = config['measurement']['end_date']
except:
    print('Warning: using default end date Jan 1 2017')
    end_date = 'Jan 1 2017'

# Forward periods for prediction
try:
    forward_periods = config['measurement']['forward_periods']
except:
    pass

# Factor quantiles
try:
    quantiles = config['measurement']['quantiles']
except:
    pass

# Train test split date
try:
    train_end = pd.to_datetime(config['measurement']['train_end'])
except:
    print('Warning: using default train test split data Jan 1 2016')
    pass
    
# Utility Rolling Binning Function
binrank = lambda x: pd.cut(x,bins=quantiles,labels=(np.array(range(quantiles))+1))[-1]

### LOAD AND PROCESS CFTC DATA ###
# Read in CFTC Data
#TODO: UPGRADE TO WEB SCRAPE
df_cftc = pd.read_csv('data/C_TFF_2006_2016.txt')

# Filter to relevent tickers
df_cftc = df_cftc[df_cftc[cftc_ticker].isin(tickers.values())].drop(cftc_ignore, axis=1)

# Standardize Index Columns
df_cftc['date'] = pd.to_datetime(df_cftc[cftc_date])
df_cftc['asset'] = df_cftc[cftc_ticker].replace(dict((v,k) for k,v in tickers.iteritems())) #flip keys and values for mapping
df_cftc = df_cftc.drop([cftc_ticker,cftc_date], axis=1)

### SCRAPE AND PROCESS GOOGLE PRICES ###
# Scrape
try:
    df = get_prices(tickers.keys(), start_date, end_date)
except:
    print('Warning: Failed to get google prices, falling back to last stored googletickerdata.csv')
    df = pd.read_csv('data/googlepricedata.csv')
    df = df.set_index(keys=['date', 'asset'])
else:
    df.to_csv('data/googlepricedata.csv')

# Standardize Index
df = df.reset_index()
df['date'] = pd.to_datetime(df['date'])

### EXECUTE BY ASSET ###
# Initialize data frames
df_test = pd.DataFrame()
df_factor = pd.DataFrame()

for ticker in tickers.keys():
    
    print('Processing '+ticker+'...')
    
    ## Clean outliers ##
    
    # google finance data cleaning
    df_prices = df.loc[df['asset'] == ticker]
    df_prices = df_prices.set_index(keys=['date', 'asset']).sort_index()
    df_prices = df_prices.apply(lambda x: pd.to_numeric(x, errors='coerce'), axis=0)
    df_prices = clean_columns(df_prices, pctnan=0.2)
    df_prices = clean_outliers(df_prices, window=3, threshold=3)
    
    # cftc data cleaning
    df_pos = df_cftc.loc[df_cftc['asset'] == ticker]
    df_pos = df_pos.set_index(keys=['date', 'asset']).sort_index()
    df_pos = df_pos.apply(lambda x: pd.to_numeric(x, errors='coerce'), axis=0)
    df_pos = clean_columns(df_pos, pctnan=0.2)
    df_pos = clean_outliers(df_pos, window=3, threshold=3)
    
    # Merge Google and CFTC
    df_data = df_prices.merge(right=df_pos, how='left', left_index=True, right_index=True)
    
    # Forward Fill
    df_data = df_data.fillna(method='ffill')
    
    data_columns = np.array(df_data.columns.values)
    
    if feature_columns is None:
        feature_columns_tmp = data_columns
    else:
        feature_columns_tmp = feature_columns
    
    if price_columns is None:
        price_columns_tmp = df_prices.columns.values
    else:
        price_columns_tmp = data_columns[np.in1d(data_columns,momentum_columns)]
    
    if momentum_columns is None:
        momentum_columns_tmp = data_columns
    else:
        momentum_columns_tmp = data_columns[np.in1d(data_columns,momentum_columns)]
    
    if moving_average_columns is None:
        moving_average_columns_tmp = data_columns
    else:
        moving_average_columns_tmp = data_columns[np.in1d(data_columns,moving_average_columns)]
        
    # Create Long/Short Net Exposure
    long_array = np.array([])
    short_array = np.array([])
    spread_array = np.array([])
    net_array = np.array([])
    long_short_diff_array = np.array([])
    short_ratio_array = np.array([])
    for j in [i for i, s in enumerate(data_columns) if '_Long_All' in s]:
        long_name = data_columns[j]
        name_component = long_name[:long_name.index('_Long_All')]
        short_name = name_component+'_Short_All'
        long_short_diff_name = name_component+'_Long_Short_Diff'
        short_ratio_name = name_component+'_Short_Ratio'
        net_name = name_component+'_Net'
        spread_name = name_component+'_Spread_All'
        if (short_name in data_columns) and (spread_name in data_columns):
            long_array = np.append(long_array,long_name)
            short_array = np.append(short_array,short_name)
            long_short_diff_array = np.append(long_short_diff_array,long_short_diff_name)
            spread_array = np.append(spread_array,spread_name)
            net_array = np.append(net_array,net_name)
            short_ratio_array = np.append(short_ratio_array,short_ratio_name)
        
    # Create Net Features
    df_data[net_array] = df_data[long_array] - df_data[short_array].values + df_data[spread_array].values
    df_data[long_short_diff_array] = df_data[long_array] - df_data[short_array].values
    df_data[short_ratio_array] = df_data[short_array]/(df_data[short_array].values + df_data[long_array].values + df_data[spread_array].values)
    
    # Add Net Features to Moving Average and Momentum Lists
    momentum_columns_tmp = np.append(momentum_columns_tmp, [net_array, long_short_diff_array, short_ratio_array])
    moving_average_columns_tmp = np.append(moving_average_columns_tmp, [net_array, long_short_diff_array, short_ratio_array])
    
    df_data = df_data.reset_index()
    
    # Momentum
    mocolnames = ['mo_'+col+'_'+str(momentum_period) for col in momentum_columns_tmp]
    df_data[mocolnames] = df_data[momentum_columns_tmp].diff(momentum_period)/df_data[momentum_columns_tmp].shift(momentum_period)
    
    # Momentum 2nd Degree
    momocolnames = ['momo_'+col+'_'+str(momentum_period) for col in momentum_columns_tmp]
    df_data[momocolnames] = df_data[mocolnames].diff(momentum_period)
    
    # Build Moving Average Features
    for col in moving_average_columns_tmp:
        for moving_average_period in moving_average_periods:
            df_data['ma_'+col+'_'+str(moving_average_period)] = df_data[col].rolling(window=moving_average_period, center=False).mean()
            if col in price_columns_tmp:
                df_data['ma_'+col+'_target/'+str(moving_average_period)] = df_data['ma_'+col+'_'+str(moving_average_period)]/df_data[target]
        for moving_average_period_num in moving_average_periods:
            for moving_average_period_denom in moving_average_periods:
                if moving_average_period_num < moving_average_period_denom:
                    df_data['ma_'+col+'_'+str(moving_average_period_num)+'/'+str(moving_average_period_denom)] = df_data['ma_'+col+'_'+str(moving_average_period_num)]/df_data['ma_'+col+'_'+str(moving_average_period_denom)]

    #TODO: Add Feature Groups and Positioning Percentages
    
    ### Measure Feature Quantile Returns ###
    
    for feature in df_data.drop(['date','asset',target], axis=1):
        
        print('Analyzing '+ticker+'_'+feature)
        
        # Clean Feature
        df_feature = df_data[['date','asset',target,feature]].fillna(method='ffill').dropna().set_index(keys=['date','asset'])
        
        # Ensure Feature has enough data to support binning (may not need this anymore)
        feature_mean = df_feature[feature].mean()
        feature_stdev = df_feature[feature].std()
        if (feature_stdev>0) and (~np.isnan(feature_mean)) and (~np.isinf(feature_mean)) and (~np.isnan(feature_stdev)) and (~np.isinf(feature_stdev)):
            
            # Build Factor and Factor Bins
            #factor_data = df_feature[[feature,target]]
            
            # Create Forward Returns
            for period in forward_periods:
                df_feature[period] = df_feature[target].pct_change(period).shift(-period)
            
            # Compute Factor Z-Score
            df_feature.rename(columns={feature: 'factor'}, inplace=True)
            df_feature['factor_zscore'] = (df_feature['factor']-df_feature['factor'].rolling(window=400, min_periods=100).mean())/df_feature['factor'].rolling(window=400, min_periods=100).std()
            
            # Bin Factor Z-Score (may not need this try, exception)
            try:
                df_feature['factor_bucket'] = df_feature['factor'].rolling(window=400, min_periods=100).apply(binrank)
            except:
                print('Exception!')
                continue
            else:
                #df_feature['factor_bucket'] = df_feature['factor'].rolling(window=400, min_periods=100).apply(binrank)

                df_feature = df_feature.dropna().reset_index()

                train_data = df_feature[df_feature['date'] < train_end].set_index(keys=['date','asset'])
                test_data = df_feature[df_feature['date'] >= train_end]

                # Compute Mean, Std Error, and Sample Sizes
                mean_return = train_data.groupby('factor_bucket')[forward_periods].mean()
                std_err = train_data.groupby('factor_bucket')[forward_periods].std()
                count_sample = train_data.groupby('factor_bucket')[forward_periods].count()

                # Join results
                df_factor_tmp = (mean_return/std_err).merge(right=mean_return, left_index=True, right_index=True, suffixes=['_zscore','_mean'])
                df_factor_tmp = df_factor_tmp.merge(right=std_err, left_index=True, right_index=True, suffixes=['','_std_err'])
                df_factor_tmp = df_factor_tmp.merge(right=count_sample, left_index=True, right_index=True, suffixes=['','_count'])

                # Format results for storage
                df_factor_tmp['feature'] = feature
                df_factor_tmp['asset'] = ticker
                df_factor_tmp = df_factor_tmp.reset_index().set_index(keys=['asset','feature','factor_bucket'])
                df_factor = df_factor.append(df_factor_tmp)

                # Format Test Data
                #test_data = factor_data[factor_data['date'] >= train_end]
                test_data['feature'] = feature
                test_data = test_data.set_index(keys=['date','asset','feature'])
                df_test = df_test.append(test_data)
    
    # Save results periodically to avoid a full rerun on error
    df_factor.to_csv('results/'+ticker+'_factors.csv')
    # Save test data
    df_test.to_csv('results/test_data.csv')

