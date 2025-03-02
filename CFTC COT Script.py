# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 11:52:36 2025

@author: Jun Hui
"""

########################################## Data Extraction ##########################################
import pandas as pd
import matplotlib.pyplot as plt
plt.style.use('seaborn')
from sodapy import Socrata  #https://pythonhosted.org/sodapy/
from datetime import datetime
from dateutil.relativedelta import relativedelta #adding years to a date

current_dateTime = datetime.now()
current_dateTime_str = current_dateTime.strftime('%Y-%m-%d') #convert to string

start_dateTime_1Y = current_dateTime - relativedelta(years=1) #1 year worth of data
start_dateTime_1Y_str = start_dateTime_1Y.strftime('%Y-%m-%d') #convert 1Y to string

# Set client to the CFTC website
client = Socrata("publicreporting.cftc.gov", None)
    
# Report Dataset Identifier:
Legacy_Futures_Only_Report = "6dca-aqww"
Legacy_Combined_Report = "jun7-fc8e"
Disaggregated_Futures_Only_Report = "72hh-3qpy"
Disaggregated_Combined_Report = "kh3c-gbw2"
TFF_Futures_Only_Report = "gpe5-46if"
TFF_Combined_Report = "yw9f-hn96"
Supplemental_Report = "4zgm-a668"

#Sample Data 
sample = client.get(Disaggregated_Combined_Report, limit=2000)
sample_df = pd.DataFrame.from_records(sample)
sample_col_names = sample_df.columns
sample_market_and_exchange_names = sample_df[["market_and_exchange_names", "cftc_contract_market_code"]].drop_duplicates()
#get unique contract names and code, remove duplicates and return as list of tuples

#return results from selected dataset as JSON from API
results = client.get(Disaggregated_Combined_Report,
                     where=f"cftc_contract_market_code in ('023391','023651','023A84','67411','67651','06765A','06765C','06765Z','84691','88691','111659','06765L') AND (report_date_as_yyyy_mm_dd >= '{start_dateTime_1Y_str}' AND report_date_as_yyyy_mm_dd <= '{current_dateTime_str}')",
                     order="report_date_as_yyyy_mm_dd")

#convert from JSON to DF
final_df = pd.DataFrame.from_records(results)

# Converting data type of selected columns to numeric
col_names = pd.DataFrame(final_df.columns)
convert_begin = col_names[col_names[0] == 'open_interest_all'].index[0] #returns the position at the first occurrence of the specified value
convert_end = col_names[col_names[0] == 'contract_units'].index[0]
convert_list = final_df.columns[convert_begin:convert_end]

for col in convert_list:
    final_df[col] = pd.to_numeric(final_df[col])
    
   ########################################### Charts and data manipulation #################################
latest_date_datetime = datetime.strptime(max(final_df['report_date_as_yyyy_mm_dd']), '%Y-%m-%dT%H:%M:%S.%f')
week_before_datetime = latest_date_datetime - relativedelta(days=7)
month_before_datetime = latest_date_datetime - relativedelta(months=1)

latest_date = max(final_df['report_date_as_yyyy_mm_dd'])
week_before_str = week_before_datetime.strftime('%Y-%m-%d')
month_before_str = month_before_datetime.strftime('%Y-%m-%d')


#line chart, time series, nat gas ICE LD1 and NYME, open interest
#prod merc/swaps/mm /other other - shorts net position vs weekly change

ICE_nat_gas = final_df[final_df['contract_market_name'] == "NAT GAS ICE LD1"]
ICE_nat_gas['report_date_as_yyyy_mm_dd'] = pd.to_datetime(ICE_nat_gas['report_date_as_yyyy_mm_dd'])
ICE_nat_gas = ICE_nat_gas.set_index('report_date_as_yyyy_mm_dd')

NYME_nat_gas  = final_df[final_df['contract_market_name'] == "NAT GAS NYME"]
NYME_nat_gas['report_date_as_yyyy_mm_dd'] = pd.to_datetime(NYME_nat_gas['report_date_as_yyyy_mm_dd'])
NYME_nat_gas = NYME_nat_gas.set_index('report_date_as_yyyy_mm_dd')

WTI = final_df[final_df['contract_market_name'] == "CRUDE OIL, LIGHT SWEET-WTI"]
WTI['report_date_as_yyyy_mm_dd'] = pd.to_datetime(WTI['report_date_as_yyyy_mm_dd'])
WTI = WTI.set_index('report_date_as_yyyy_mm_dd')

Gold = final_df[final_df['contract_market_name'] == "GOLD"]
Gold['report_date_as_yyyy_mm_dd'] = pd.to_datetime(Gold['report_date_as_yyyy_mm_dd'])
Gold = Gold.set_index('report_date_as_yyyy_mm_dd')

RBOB = final_df[final_df['contract_market_name'] == "GASOLINE RBOB"]
RBOB['report_date_as_yyyy_mm_dd'] = pd.to_datetime(RBOB['report_date_as_yyyy_mm_dd'])
RBOB = RBOB.set_index('report_date_as_yyyy_mm_dd')

#Chart illustrating open interest over the weeks for ICE Nat Gas
plt.figure(figsize=(12,6))
plt.plot(ICE_nat_gas.index, ICE_nat_gas['open_interest_all'], label = 'ICE NG open interest all')
plt.plot(NYME_nat_gas.index, NYME_nat_gas['open_interest_old']+100, label = 'NYME NG open interest')

plt.title("Open interest for Nat Gas Futures")
plt.xlabel("Week No.")
plt.ylabel("open interest")
plt.legend()

plt.xticks(rotation=45) #rotate x-axis label for better readability
plt.tight_layout()
plt.show()

# nyme NG MM long short positions
long_positions = NYME_nat_gas['m_money_positions_long_all']
short_positions = NYME_nat_gas['m_money_positions_short_all']
net_position = long_positions - short_positions
open_interest = NYME_nat_gas['open_interest_all']

fig, ax1 = plt.subplots(figsize=(12,6))
ax1.fill_between(NYME_nat_gas.index, open_interest, color='skyblue', alpha=0.3, label = 'Open Interest')
ax1.set_ylabel('Open Interest')
ax1.tick_params(axis = 'y')

ax2 = ax1.twinx() #Create a second y-axis (ax2) that shares the same x-axis

ax2.plot(NYME_nat_gas.index, long_positions, color='navy', label='long')
ax2.plot(NYME_nat_gas.index, short_positions, color='maroon', label='short')
ax2.plot(NYME_nat_gas.index, net_position, color='forestgreen', label='net position')
ax2.set_ylabel('MM Positions')
ax2.tick_params(axis='y')

#Customize the plot
plt.title("NAT GAS MM (Futures & Options)")
ax1.set_xlabel("Date")
# Combine legends from both axes
lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax2.legend(lines + lines2, labels + labels2, loc='upper right')

plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

### Bar chart for w-o-w change in positions

#report_date = latest_date
#weekbefore = week_before_str

print(latest_date_datetime)

#pulls long, short data for commercial, swap, mm, others
current_NYMEX = NYME_nat_gas.loc[[NYME_nat_gas.index.max()]] #use double [] to prevent cols turning into rows
prod_merc_long = current_NYMEX['change_in_prod_merc_long']
prod_merc_short = current_NYMEX['change_in_prod_merc_short']
prod_merc_net = prod_merc_long - prod_merc_short
swap_long = current_NYMEX['change_in_swap_long_all']
swap_short = current_NYMEX['change_in_swap_short_all']
swap_net= swap_long-swap_short
mm_long = current_NYMEX['change_in_m_money_long_all']
mm_short = current_NYMEX['change_in_m_money_short_all']
mm_net = mm_long-mm_short
other_long = current_NYMEX['change_in_other_rept_long']
other_short = current_NYMEX['change_in_other_rept_short']
other_net = other_long - other_short

#Prepare data for the bar chart
categories = ['Prod Merc', 'Swap', 'MM', 'Other']
positions = ['Long', 'Short', 'Net']

data = {
    'Long': [prod_merc_long.values[0], swap_long.values[0], mm_long.values[0], other_long.values[0]],
    'Short': [prod_merc_short.values[0], swap_short.values[0], mm_short.values[0], other_short.values[0]],
    'Net': [prod_merc_net.values[0], swap_net.values[0], mm_net.values[0], other_net.values[0]]
}

# --- Plotting ---
fig, ax = plt.subplots(figsize=(12, 6))  # Adjust figure size as needed

# Bar width
bar_width = 0.2

# X positions for each group
x = range(len(positions))
# [0, 1, 2] (Long, Short, Net)
colors = ['forestgreen', 'maroon', 'blue']

# Plotting bars
for i, position in enumerate(positions):
    ax.bar([cat + i * bar_width for cat in range(len(categories))], data[position], width=bar_width, label=position, color=colors[i])

# --- Customization ---
ax.set_xlabel('Category')
ax.set_ylabel('Change')
ax.set_title('NAT GAS WoW Change')  # Set chart title as needed
ax.set_xticks([cat + bar_width for cat in range(len(categories))])
ax.set_xticklabels(categories)
ax.legend(loc='upper right')  # Move legend to avoid overlap

plt.tight_layout()
plt.show()