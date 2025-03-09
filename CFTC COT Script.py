# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 11:52:36 2025

@author: Jun Hui
"""

"""
Definition: 
  1. Prod_Merc: Producer and merchants (Commercial) that use financial products to manage or hedge risks
  2. Swap: Swap dealer is an tntity that deals primarily in swaps for a commodity and uses the future markets to manage or hedge the risk associated with those
           swap transactions.
  3. Money Manager: These are traders engaged in managing and conducting organized futures trading on behalf of clients
  4. Others: Other reportable trader that is not placed into one of the other three categories 
"""
    

########################################## Data Extraction ##########################################

from matplotlib.backends.backend_pdf import PdfPages
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

    
####################################### Function for chart creation ######################################

def weekly_chart(data_index,long,short,net,heading):
    
    latest_index = data_index.max()
    previous_index = data_index[data_index<latest_index].max()
        
    weekly_data_change = {"Long": long.loc[latest_index] - long.loc[previous_index],
                          "Short": short.loc[latest_index] - short.loc[previous_index],
                          "Net": (long.loc[latest_index] - long.loc[previous_index]) - (short.loc[latest_index] - short.loc[previous_index])}
    
    fig, ax1 = plt.subplots(figsize=(12,6))
        
    ax1.plot(data_index, long, color='navy', label='long')
    ax1.plot(data_index, short, color='maroon', label='short')
    ax1.plot(data_index, net, color='forestgreen', label='net position')
    ax1.set_title("NAT GAS " + heading + " (Futures & Options)")
    ax1.set_ylabel(heading + ' Positions')
    ax1.set_xlabel("Date")
    ax1.legend(loc='upper right')
    
    textbox = (
        f"WoW Change\n"
        f"Long: {weekly_data_change['Long']}\n"
        f"Short: {weekly_data_change['Short']}\n"
        f"Net: {weekly_data_change['Net']}\n")
    
    ax1.text(
        0.02, 0.95, textbox,
        transform=ax1.transAxes,
        fontsize=10,
        verticalalignment='top',
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.5, edgecolor="black"))
    
    plt.show()
    pdf.savefig(fig)
    plt.close(fig)

def weekly_chart_OI(data_index,long,short,net,OI,heading):
    fig, ax1 = plt.subplots(figsize=(12,6))
    ax1.fill_between(data_index, OI, color='skyblue', alpha=0.3, label = 'Open Interest')
    ax1.set_ylabel('Open Interest')
    ax1.tick_params(axis = 'y')
    
    ax2 = ax1.twinx() #Create a second y-axis (ax2) that shares the same x-axis
    ax2.plot(data_index, long, color='navy', label='long')
    ax2.plot(data_index, short, color='maroon', label='short')
    ax2.plot(data_index, net, color='forestgreen', label='net position')
    ax2.set_ylabel(heading + 'Positions')
    ax2.tick_params(axis='y')

    #Customize the plot
    ax1.set_title("NAT GAS " + heading + " (Futures & Options)")
    ax1.set_xlabel("Date")
    # Combine legends from both axes
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2 , labels + labels2 , loc='upper right')

    #Adding labels at the end of each line
    ax2.text(
       data_index[-1], net[-1], f'{net[-1]:,.0f}', 
       color='forestgreen', fontsize=10, fontweight='bold', va='center'
   )
    
    ax2.text(
        data_index[-1], long[-1], f'{long[-1]:,.0f}', 
        color='navy', fontsize=10, fontweight='bold', va='center'
    )
    ax2.text(
        data_index[-1], short[-1], f'{short[-1]:,.0f}', 
        color='maroon', fontsize=10, fontweight='bold', va='center'
    )
    
    ax1.grid(alpha=0.2)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    pdf.savefig(fig)
    plt.close(fig)
    
def net_position_concentration(data_index, MM, CM, Swap, Other, heading):
    fig, ax1 = plt.subplots(figsize=(12,6))
       
    ax1.plot(data_index, MM, color='navy', label='Money Managers')
    ax1.plot(data_index, CM, color='maroon', label='Commercial')
    ax1.plot(data_index, Swap, color='forestgreen', label='Swap Dealers')
    ax1.plot(data_index, Other, color='grey', label='Others')
    ax1.set_title(heading + "Net Position Concentration")
    ax1.set_ylabel("Percentage of Open Interest (%)")
    ax1.set_xlabel("Date")
    ax1.legend(loc='upper left')

    ax1.text(
       data_index[-1], MM[-1], f'{MM[-1]:+,.0f}', 
       color='navy', fontsize=14, fontweight='bold', va='center'
   )
    
    ax1.text(
        data_index[-1], CM[-1], f'{CM[-1]:+,.0f}', 
        color='maroon', fontsize=14, fontweight='bold', va='center'
    )
    ax1.text(
        data_index[-1], Swap[-1], f'{Swap[-1]:+,.0f}', 
        color='forestgreen', fontsize=14, fontweight='bold', va='center'
    )
    ax1.text(
        data_index[-1], Other[-1], f'{Other[-1]:+,.0f}', 
        color='grey', fontsize=14, fontweight='bold', va='center'
    )
    
    plt.show()
    pdf.savefig(fig)
    plt.close(fig)
    
########################################### Charts and data manipulation #################################

latest_date_datetime = datetime.strptime(max(final_df['report_date_as_yyyy_mm_dd']), '%Y-%m-%dT%H:%M:%S.%f')
week_before_datetime = latest_date_datetime - relativedelta(days=7)
month_before_datetime = latest_date_datetime - relativedelta(months=1)

latest_date = max(final_df['report_date_as_yyyy_mm_dd'])
week_before_str = week_before_datetime.strftime('%Y-%m-%d')
month_before_str = month_before_datetime.strftime('%Y-%m-%d')


#Dataset to use for charts

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

#### create a PDF object to save charts ####
with PdfPages('Nat Gas COT') as pdf:

######## Chart for NYME NG Total position #########
    longs = NYME_nat_gas['m_money_positions_long_all']+NYME_nat_gas['prod_merc_positions_long']+NYME_nat_gas['swap_positions_long_all']+NYME_nat_gas['other_rept_positions_long']
    shorts = NYME_nat_gas['m_money_positions_short_all'] + NYME_nat_gas['prod_merc_positions_short'] + NYME_nat_gas['swap__positions_short_all'] + NYME_nat_gas['other_rept_positions_short']
    nets = longs - shorts
    Open_Interest = NYME_nat_gas['open_interest_all']
    weekly_chart_OI(NYME_nat_gas.index,longs,shorts,nets,Open_Interest,"Total")

######## Charts for commercial, swap and others ########
    weekly_chart(NYME_nat_gas.index, NYME_nat_gas['m_money_positions_long_all'],NYME_nat_gas['m_money_positions_short_all'],NYME_nat_gas['m_money_positions_long_all']-NYME_nat_gas['m_money_positions_short_all'],"MM")
    weekly_chart(NYME_nat_gas.index, NYME_nat_gas['prod_merc_positions_long'],NYME_nat_gas['prod_merc_positions_short'],NYME_nat_gas['prod_merc_positions_long']-NYME_nat_gas['prod_merc_positions_short'],"Producer")
    weekly_chart(NYME_nat_gas.index, NYME_nat_gas['swap_positions_long_all'],NYME_nat_gas['swap__positions_short_all'],NYME_nat_gas['swap_positions_long_all']-NYME_nat_gas['swap__positions_short_all'],"Swaps")
    weekly_chart(NYME_nat_gas.index, NYME_nat_gas['other_rept_positions_long'],NYME_nat_gas['other_rept_positions_short'],NYME_nat_gas['other_rept_positions_long']-NYME_nat_gas['other_rept_positions_short'],"Others")
    
######## Bar chart for w-o-w change in positions ########
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
    
    
    categories = ['Prod Merc', 'Swap', 'MM', 'Other']
    positions = ['Long', 'Short', 'Net']
    
    data = {
        'Long': [prod_merc_long.values[0], swap_long.values[0], mm_long.values[0], other_long.values[0]],
        'Short': [prod_merc_short.values[0], swap_short.values[0], mm_short.values[0], other_short.values[0]],
        'Net': [prod_merc_net.values[0], swap_net.values[0], mm_net.values[0], other_net.values[0]]}
    
#PLotting the chart
    fig, ax = plt.subplots(figsize=(12, 6))  # Adjust figure size as needed
    bar_width = 0.2
    
# X positions for each group
    x = range(len(positions))
    # [0, 1, 2] (Long, Short, Net)
    colors = ['forestgreen', 'maroon', 'blue']
    
# Plotting bars
    for i, position in enumerate(positions):
        ax.bar([cat + i * bar_width for cat in range(len(categories))], data[position], width=bar_width, label=position, color=colors[i])
    
# Customization 
    ax.set_xlabel('Category')
    ax.set_ylabel('Change')
    ax.set_title('NAT GAS WoW Change')  # Set chart title as needed
    ax.set_xticks([cat + bar_width for cat in range(len(categories))])
    ax.set_xticklabels(categories)
    ax.legend(loc='upper right')  # Move legend to avoid overlap
    
    plt.tight_layout()
    plt.show()
    pdf.savefig(fig)
    plt.close(fig)

##### Net Contracts for commercial and MM #####
    fig, ax = plt.subplots(figsize=(12,6))
    ax.fill_between(NYME_nat_gas.index, NYME_nat_gas['prod_merc_positions_long']-NYME_nat_gas['prod_merc_positions_short'], 0, color='red',alpha=0.7,label='Net Commercial Positions' )
    ax.fill_between(NYME_nat_gas.index, NYME_nat_gas['m_money_positions_long_all']-NYME_nat_gas['m_money_positions_short_all'], 0, color='green',alpha=0.7,label='Net Trader Positions' )
    
    ax.set_title("NAT GAS Commercial vs Trader Net Positions", fontsize=14)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Net Contracts", fontsize=12)
    ax.grid(alpha=0.3)
    ax.legend(loc='upper left', fontsize=10)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    pdf.savefig(fig)
    plt.close(fig)
    
##### Nat Gas Net Position Concentration ####
    comm_net_oi = NYME_nat_gas.pct_of_oi_prod_merc_long - NYME_nat_gas.pct_of_oi_prod_merc_short
    swap_net_oi = NYME_nat_gas.pct_of_oi_swap_long_all - NYME_nat_gas.pct_of_oi_swap_short_all
    mm_net_oi =  NYME_nat_gas.pct_of_oi_m_money_long_all - NYME_nat_gas.pct_of_oi_m_money_short_all
    other_net_oi = NYME_nat_gas.pct_of_oi_other_rept_long - NYME_nat_gas.pct_of_oi_other_rept_short
    
    net_position_concentration(NYME_nat_gas.index, mm_net_oi, comm_net_oi, swap_net_oi, other_net_oi, 'Nat Gas ')

#### Long/Short Ratios ####

    comm_ratio = NYME_nat_gas.prod_merc_positions_long / NYME_nat_gas.prod_merc_positions_short
    MM_ratio = NYME_nat_gas.m_money_positions_long_all / NYME_nat_gas.m_money_positions_short_all
    swap_ratio = NYME_nat_gas.swap_positions_long_all / NYME_nat_gas.swap__positions_short_all
    other_ratio = NYME_nat_gas.other_rept_positions_long / NYME_nat_gas.other_rept_positions_short
    
    fig, ax1 = plt.subplots(figsize=(12,6))
    ax1.plot(NYME_nat_gas.index, MM_ratio, color = 'navy', label = 'Money Manager')
    ax1.plot(NYME_nat_gas.index, comm_ratio, color = 'maroon', label = 'Commercial')
    ax1.plot(NYME_nat_gas.index, swap_ratio, color = 'forestgreen', label = 'Swap Dealer')
    ax1.plot(NYME_nat_gas.index, other_ratio, color = 'grey', label = 'Others')
    ax1.set_title("Nat Gas Long/Short Ratio")
    ax1.set_ylabel("Long/Short Ratio")
    ax1.set_xlabel("Date")
    ax1.legend(loc='upper left')
    
    ax1.text(
        NYME_nat_gas.index[-1], MM_ratio[-1], f'{MM_ratio[-1]:+,.0f}', 
        color='navy', fontsize=14, fontweight='bold', va='center'
    )
     
    ax1.text(
        NYME_nat_gas.index[-1], comm_ratio[-1], f'{comm_ratio[-1]:+,.0f}', 
        color='maroon', fontsize=14, fontweight='bold', va='center'
    )
    ax1.text(
        NYME_nat_gas.index[-1], swap_ratio[-1], f'{swap_ratio[-1]:+,.0f}', 
        color='forestgreen', fontsize=14, fontweight='bold', va='center'
    )
    ax1.text(
        NYME_nat_gas.index[-1], other_ratio[-1], f'{other_ratio[-1]:+,.0f}', 
        color='grey', fontsize=14, fontweight='bold', va='center'
    )
    plt.show()
    pdf.savefig(fig)
    plt.close(fig)