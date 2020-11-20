from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from matplotlib import pyplot as plt
from scipy.optimize import curve_fit
import pandas as pd
import numpy as np
import datetime
import json

aa_url = 'https://api.glassnode.com/v1/metrics/addresses/active_count'
mc_url = 'https://api.glassnode.com/v1/metrics/market/marketcap_usd'
cs_url = 'https://api.glassnode.com/v1/metrics/supply/current'
pc_url = 'https://api.glassnode.com/v1/metrics/market/price_usd_close'

parameters = {
    'api_key' : '#your API key#', ### API Key required here.
    'a' : 'BTC',
    'i' : '24h',
    'c' : 'native',
}

def get_purifed_data(api_url, api_parameters):
    session = Session()
    try:
        response = session.get(api_url, params=api_parameters)
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
    df = pd.DataFrame(json.loads(response.text))
    df = df.set_index('t')
    df.index = pd.to_datetime(df.index, unit='s')
    df = df.loc[df.index > '2010-7-16'] # Day 1 of BTC API Data: 2010-7-17
    df = df.loc[df.index < '2020-11-4']
    df.reset_index(inplace=True)
    return df

def aa_growth_modeling_4prams(x, a, b, c, d):
    return (np.e**(a) * np.e**(-b * np.e**(-c * x**d)))

def fit_aa_curve_coe_4prams():
    aa_data = get_purifed_data(aa_url, parameters)
    aa_real_nums = np.array(aa_data['v'])
    aa_date_array = aa_data.index
    coe_guess = [1.72, 1.76, 0.79, 0.70]
    est_coe, est_cov = curve_fit(aa_growth_modeling_4prams, 
                                 aa_date_array, 
                                 aa_real_nums, 
                                 coe_guess, 
                                 maxfev = 1000000)
    return est_coe

def marketcap_to_activeaddress_modeling(x, a, b):
    return (np.e**(a) * x**(b))

def fit_marketcap_to_activeaddress_coe():
    aa_data = get_purifed_data(aa_url, parameters)
    mc_data = get_purifed_data(mc_url, parameters)
    aa_real_nums = np.array(aa_data['v'])
    mc_real_nums = np.array(mc_data['v'])
    coe_guess = [1.51, 1.69]
    est_coe, est_cov = curve_fit(marketcap_to_activeaddress_modeling, 
                                 aa_real_nums, 
                                 mc_real_nums, 
                                 coe_guess, 
                                 maxfev = 1000000)
    return est_coe

def coins_in_circulation_modeling(x, a, b, c, d):
    return (a + b * x + c * x**2 + d * x**3)

def fit_coins_in_circulation_coe():
    cs_data = get_purifed_data(cs_url, parameters)
    cs_real_nums = np.array(cs_data['v'])
    cs_date_array = cs_data.index
    coe_guess = [3000000, 300000, 100000, 100000]
    est_coe, est_cov = curve_fit(coins_in_circulation_modeling, 
                                 cs_date_array, 
                                 cs_real_nums, 
                                 coe_guess, 
                                 maxfev = 1000000)
    return est_coe

# Regarding the coefficients, please see to the papper:
# Combining a Generalized Metcalfe's Law and the LPPLS Model
# Prof. Didier Sornette and his team

def marketcap_to_activeaddress_log_linear(x):
# Generalized Metcalfe Regression / Generalized Metcalfe's Law
    return (np.exp(1.51) * pow(x, 1.69))
    
def aa_growth_distns_4prams(x):
    # Active Addresses Growth Curve / Equation
    a, b, c, d = fit_aa_curve_coe_4prams()
    return (np.exp(a) * np.exp(-b * np.exp(-c * x**d)))

def coins_in_circulation_distns(x):
    # Coins in Circulation curve / Equation
    a, b, c, d = fit_coins_in_circulation_coe()
    return (a + b * x + c * x**2 + d * x**3)

def plot_data():
    aa_data = get_purifed_data(aa_url, parameters)
    mc_data = get_purifed_data(mc_url, parameters)
    cs_data = get_purifed_data(cs_url, parameters)
    pc_data = get_purifed_data(pc_url, parameters)
    fig, main_ax = plt.subplots(2, 2, figsize=(20, 15))
    # up-left plot:
    main_ax[0, 0].title.set_text('Active Addresses')
    main_ax[0, 0].plot(aa_data['t'], aa_data['v'], 
                       linewidth=0.2)
    x1 = aa_data.index
    y1 = aa_growth_distns_4prams(x1)
    main_ax[0, 0].plot(aa_data['t'], y1, 
                       color=(0.7, 0.2, 0.1), 
                       linewidth=1, 
                       linestyle='--', 
                       zorder=1)
    main_ax[0, 0].set_yscale('log')
    main_ax[0, 0].set_ylim(pow(10, 3), 3*pow(10, 6))
    main_ax[0, 0].grid(True)
    # down-left plot:
    main_ax[1, 0].title.set_text('Market Cap')
    main_ax[1, 0].plot(mc_data['t'], mc_data['v'], 
                       linewidth=0.5)
    y2 = marketcap_to_activeaddress_log_linear(y1)
    main_ax[1, 0].plot(mc_data['t'], y2, 
                       color=(0.7, 0.2, 0.1), 
                       linewidth=1, 
                       linestyle='--', 
                       zorder=1)
    main_ax[1, 0].set_yscale('log') #basey = np.e
    main_ax[1, 0].set_ylim(pow(10, 4), pow(10, 13))
    main_ax[1, 0].grid(True)
    # up-right plot:
    main_ax[0, 1].title.set_text('Market Cap to Active Addresses')
    main_ax[0, 1].scatter(aa_data['v'], mc_data['v'], 
                          s=3, 
                          alpha=0.3)
    x3 = aa_data['v']
    y3 = marketcap_to_activeaddress_log_linear(x3)
    main_ax[0, 1].plot(x3, y3, 
                       color=(0.7, 0.2, 0.1), 
                       linewidth=0.5, 
                       linestyle='--', 
                       zorder=1)
    main_ax[0, 1].set_xscale('log')
    main_ax[0, 1].set_yscale('log')
    main_ax[0, 1].set_xlim(100, )
    main_ax[0, 1].set_ylim(pow(10, 5), )
    main_ax[0, 1].grid(True)
    # down-right plot:
    main_ax[1, 1].title.set_text('BTC Price vs Estimated Price')
    main_ax[1, 1].plot(pc_data['t'], pc_data['v'], 
                       linewidth=0.5, 
                       label='BTC Price')
    y4 = y2/coins_in_circulation_distns(cs_data.index)
    main_ax[1, 1].plot(pc_data['t'], y4, 
                       color=(0.7, 0.2, 0.1), 
                       linewidth=0.5, 
                       linestyle='--', 
                       zorder=1, 
                       label='Estimated Price based on GML')
    main_ax[1, 1].legend()
    main_ax[1, 1].set_yscale('log')
    main_ax[1, 1].set_ylim(1, 30000)
    main_ax[1, 1].grid(True)
    plt.show()
    
def x_days_prediction(x_days):
    # X_days++ price prediction based on the estimation curve
    aa_data = get_purifed_data(aa_url, parameters)
    x = pd.DataFrame(aa_data.index.tolist())
    x = np.append(x, (x[-x_days:] + x_days))
    puls_x_days_estimation = marketcap_to_activeaddress_log_linear(aa_growth_distns_4prams(x))/coins_in_circulation_distns(x)
    predicted_price = puls_x_days_estimation[-x_days:]
    return predicted_price

if __name__ == '__main__':
    plot_data()
    x_days_prediction(60)
