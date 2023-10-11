import login
import get_plan_info
import pandas as pd


access_token = access_token = login.get_access_token()

# Import data usage
data_file = 'usage_data.csv'

df = pd.read_csv(data_file, index_col='datetime')

# Get a list of all the unique suffixes
suffixes = df['suffix'].unique()

# Create a dictionary to store the smaller dataframes
df_dict = {}

# Iterate over the suffixes and create a smaller dataframe for each suffix
for suffix in suffixes:
    df_dict[suffix] = df[df['suffix'] == suffix]

# Access the smaller dataframes using the dictionary
df_e1 = df_dict['E1']   # => E1 data

df_e2 = None
if 'E2' in df['suffix'].unique():
    df_e2 = df_dict['E2']   # => E2 data

df_b1 = None
if 'B1' in df['suffix'].unique():
    df_b1 = df_dict['B1']   # => B1 data


def fetch_rates():
    rates = []

    plans_data = login.fetch_and_save_plan_info(access_token)
    plans = get_plan_info.get_plans(plans_data)
    plan_detail = get_plan_info.get_plan_detail(plans)
    e_contract = get_plan_info.get_e_contract(plan_detail)
    # Pricing
    solar = get_plan_info.parse_solar(e_contract)
    rate = get_plan_info.get_tariff_period(e_contract)
    controledload = get_plan_info.get_controlled_load(e_contract)
    rates.append({'tariff': rate, 'controlled_load': controledload, 'solar': solar})
    return rates

def get_single_rate_detail():
    rates_json = fetch_rates()
    e2_rate = 0
    e2_daily_charge = 0
    solar_feed_in_rate = 0
    solar_meter_charge = 0
    # Extract rates
    for ratess in rates_json:
        e1_vol = 0
        e1_rate_over_vol = 0
        e2_vol = 0
        e2_rate_over_vol = 0
        if ratess['tariff'] != []:
            e1_daily_charge = ratess['tariff'][0]['daily_supply_charge']
            rates = ratess['tariff'][1]['rates']
            # Main
            e1_rate = rates[0]['unit_price']
            e1_vol = rates[0]['volume']
            if rates[0]['volume'] != 0:
                e1_rate_over_vol = rates[1]['unit_price']

            # Controlled_load
        if ratess['controlled_load'] != []:
            controlled_load = ratess['controlled_load']
            e2_daily_charge = controlled_load[0]['daily_supply_charge']
            ctrl_rates = controlled_load[1]['rates']
            e2_rate = ctrl_rates[0]['unit_price']
            e2_vol = ctrl_rates[0]['volume']
            if ctrl_rates[0]['volume'] != 0:
                e2_rate_over_vol = ctrl_rates[1]['unit_price']

            # Solar
        if ratess['solar'] != []:
            solar_rates = {rat['name']: rat['amount'] for rat in ratess['solar']}
            solar_rates = list(solar_rates.items())
            for n in range(0,len(solar_rates)):
                key, value = solar_rates[n]
                if key in ['Solar feed-in credit','Feed-in tariff']:
                    solar_feed_in_rate = value
                if key == 'Solar Meter Charge':
                    solar_meter_charge = value

        rates = {'e1_daily_charge': e1_daily_charge,
                'e1_rate': e1_rate,
                'e1_vol': e1_vol,
                'e1_rate_over_vol': e1_rate_over_vol,
                'e2_daily_charge': e2_daily_charge,
                'e2_rate': e2_rate,
                'e2_vol': e2_vol,
                'e2_rate_over_vol': e2_rate_over_vol,
                'b1_rate': solar_feed_in_rate,
                'b1_meter_charge': solar_meter_charge
                }
    return rates


def to_daily_frame(df: pd.DataFrame):

    df.index = pd.to_datetime(df.index)
        # Sum by day
    daily_u_summary = df['interval_read'].resample('D').sum()
        # Set range
    daily_u_day_range = pd.date_range(start=df.index[0].date(),end=df.index[-1].date(), freq='D')
        # Create data frame by daily
    daily_u_df = pd.DataFrame(daily_u_summary,index=daily_u_day_range)
    return daily_u_df


e1_u_day = to_daily_frame(df=df_e1)
e1_u_day = e1_u_day.rename(columns={'interval_read': 'e1'})

if df_e2 is not None :
    e2_u_day = to_daily_frame(df=df_e2)
    e2_u_day = e2_u_day.rename(columns={'interval_read': 'e2'})

if df_b1 is not None:
    b1_u_day = to_daily_frame(df=df_b1)
    b1_u_day = b1_u_day.rename(columns={'interval_read': 'b1'})

rates = get_single_rate_detail()


def pricing_col(df, rate, col_name, to_col_name):
    # df_pricing = df.copy(deep=True)
    df[to_col_name] = df[col_name] * rate
    return df


    """ usage charge """
def usage_charge(usage_df: pd.DataFrame,
                 rate_name: str,
                 col_value_name: str,
                 to_col_name: str):

    rate = float(get_single_rate_detail()[rate_name])
    usage_df = pricing_col(usage_df, rate, col_value_name, to_col_name)
    return usage_df

    """ usage charge for tariff include volume"""
def usage_charge_with_vol(usage_df: pd.DataFrame,
                          rate_name_1: str,
                          vol_1: str,
                          rate_name_2: str,
                          col_value_name: str,
                          to_col_name: str):

    rate_1 = float(get_single_rate_detail()[rate_name_1])
    rate_2 = float(get_single_rate_detail()[rate_name_2])
    vol_1 = float(get_single_rate_detail()[vol_1])
    usage_df[to_col_name] = usage_df[col_value_name].apply(lambda x: (x * rate_1) if x < vol_1 else (vol_1*rate_1 + (x - vol_1)*rate_2))
    return usage_df


    """ daily charge"""
def daily_charge(usage_df: pd.DataFrame,
                 rate_name: str,
                 to_col_name: str):

    usage_df[to_col_name]= float(get_single_rate_detail()[rate_name])
    return usage_df


""" Cost calculation """
# Main
rates = get_single_rate_detail()

e1_vol = rates['e1_vol']
if e1_vol == 0:
    e1_cost_daily = usage_charge(e1_u_day,
                                 rate_name='e1_rate',
                                 col_value_name='e1',
                                 to_col_name='e1_cost_daily')
else:
    e1_cost_daily = usage_charge_with_vol(e1_u_day,
                                          rate_name_1='e1_rate',
                                          vol_1='e1_vol',
                                          rate_name_2='e1_rate_over_vol',
                                          col_value_name='e1',
                                          to_col_name='e1_cost_daily')

# Controlled_load
e2_cost_daily = None
e2_vol = rates['e2_vol']
if df_e2 is not None:
    if e2_vol == 0:
        e2_cost_daily = usage_charge(e2_u_day,
                                     rate_name='e2_rate',
                                     col_value_name='e2',
                                     to_col_name='e2_cost_daily')
    else:
        e2_cost_daily = usage_charge_with_vol(e2_u_day,
                                              rate_name_1='e2_rate',
                                              vol_1='e2_vol',
                                              rate_name_2='e2_rate_over_vol',
                                              col_value_name='e2',
                                              to_col_name='e2_cost_daily')

# Solar
b1_cost_daily = None
if df_b1 is not None:
    b1_cost_daily = usage_charge(b1_u_day, rate_name='b1_rate', col_value_name='b1', to_col_name='b1_cost_daily')



if e2_cost_daily is None and b1_cost_daily is None:
    cost_daily_df = pd.concat([e1_cost_daily['e1_cost_daily']], axis=1)

elif e2_cost_daily is not None and b1_cost_daily is None:
    cost_daily_df = pd.concat([e1_cost_daily['e1_cost_daily'], e2_cost_daily['e2_cost_daily']], axis=1)

elif e2_cost_daily is None and b1_cost_daily is not None:
    cost_daily_df = pd.concat([e1_cost_daily['e1_cost_daily'], b1_cost_daily['b1_cost_daily']], axis=1)

else:
    cost_daily_df = pd.concat([e1_cost_daily['e1_cost_daily'], e2_cost_daily['e2_cost_daily'], b1_cost_daily['b1_cost_daily']], axis=1)


cost_daily_df = daily_charge(cost_daily_df, rate_name='e1_daily_charge', to_col_name='e1_daily_charge')
if e2_cost_daily is not None:
    cost_daily_df = daily_charge(cost_daily_df, rate_name='e2_daily_charge', to_col_name='e2_daily_charge')

# print(cost_daily_df)
# print(e1_u_day)

# print(fetch_rates())
# print(get_single_rate_detail())
