# This makes a plot where all years are stacked up on top of each other, with a color ramp to generally
# tell them apart
import pandas as pd
import numpy as np
import sys
import matplotlib as mpl
import matplotlib.pyplot as plt
from cycler import cycler


#def monthly_graphs(data_frame):

# Update these as needed
workspace = '/home/arthur/Dropbox/projects/greenland/transect_points/appears/'
csv_name = 'russel-transect-3km-spacing-1-MCD43A3-006-results.csv'
aoi_name = 'Russel Glacier Transect 1'
dt_indx = pd.date_range('2000-01-01', '2020-12-31')
csv_path = workspace + csv_name

# Define the fields of interest so we can ignore the rest
fields = ['ID', 'Date', 'MCD43A3_006_Albedo_WSA_shortwave', 'MCD43A3_006_BRDF_Albedo_Band_Mandatory_Quality_shortwave']

# Import raw APPEARS output
ts_df = pd.read_csv(csv_path, usecols=fields, parse_dates=[0])
ts_df['Date'] = pd.to_datetime(ts_df['Date'])
ts_df.set_index('Date', inplace=True)

# Mask out fill values (and could optionally also mask out mag inversions by adding another condition == 1
ts_df['MCD43A3_006_Albedo_WSA_shortwave'].mask(ts_df['MCD43A3_006_BRDF_Albedo_Band_Mandatory_Quality_shortwave'] == 255,
                                               np.NaN, inplace=True)
ts_df['SW_WSA'] = ts_df['MCD43A3_006_Albedo_WSA_shortwave']
del ts_df['MCD43A3_006_BRDF_Albedo_Band_Mandatory_Quality_shortwave']
del ts_df['MCD43A3_006_Albedo_WSA_shortwave']

# Probably delete the below -- works but not what I need
# ts_df.reset_index(inplace=True)
# ts_df['year'] = ts_df['Date'].dt.year
# ts_df['month'] = ts_df['Date'].dt.month
#
# # Group data first by year, then by month
# g = ts_df.groupby(['year', 'month'])
#
# # For each group, calculate the average of only the snow_depth column
# monthly_averages = g.aggregate({"SW_WSA": np.mean})
# monthly_averages.to_csv(workspace + 'grouped_date.csv')
# sys.exit()

# Here's where the subsetting by year then month happens
monthly_mean_df = pd.DataFrame(ts_df.groupby(['ID', pd.Grouper(freq='M')])['SW_WSA'].mean())
#monthly_mean_df.to_csv(workspace + 'initial_df.csv')
monthly_mean_df.reset_index(inplace=True)

#TODO Can I use this to input multiple concatenated appears requests??
#print(monthly_mean_df.groupby(['ID', 'Date']).mean())

# Pull off the dates and ID numbers (corresponding to distance from coast for transects),
# and make a new DF with unique values only
dates = monthly_mean_df.index.get_level_values('Date').tolist()
ids = monthly_mean_df.index.get_level_values('ID').tolist()
ids_df = pd.DataFrame({'ID': ids})
ids_df.drop_duplicates('ID', keep='first', inplace=True)
ids_df['ID'] = ids_df['ID'].astype(int)
ids_df.set_index('ID', inplace=True)
ids_df.sort_index(inplace=True)

# Use a temporary DF to organize the SW WSA values each time period into columns, then add them
# to the previously created ids_df, so we have a df where the index is the IDs, then cols are each
# month's average SW WSA
for dt in dates:
    build_df = monthly_mean_df.iloc[monthly_mean_df.index.get_level_values('Date') == dt].copy()
    build_df['ID_int'] = build_df.index.get_level_values('ID').astype(int)
    build_df = build_df.sort_values('ID_int')
    build_df.set_index('ID_int', inplace=True)
    build_df.sort_index(inplace=True)
    ids_df[str(dt)] = build_df['SW_WSA']

    # To check that the indices are aligned right, uncomment the below and check output
    # ids_df['test_index'] = build_df.index

    # ids_df = ids_df.join(build_df, lsuffix='_left', rsuffix='_right')

ids_df_climo = ids_df.copy()

# Remove all columns between column index 1 to 3
ids_df_climo.drop(ids_df_climo.iloc[:, :], inplace=True, axis=1)
ids_df_climo_temp = ids_df_climo.copy()

for mnth in ['-01-', '-02-', '-03-', '-04-', '-05-', '-06-', '-07-', '-08-', '-09-', '-10-', '-11-', '-12-']:
    for col in ids_df.columns:
        if mnth in str(col):
            ids_df_climo_temp[str(col)] = ids_df[col]
    ids_df_climo[mnth[1:-1]] = ids_df_climo_temp.mean(axis=1, skipna=True)
    ids_df_climo_temp.drop(ids_df_climo_temp.iloc[:, :], inplace=True, axis=1)


# Set up the color cycler for the plot
n = 12 #len(ids_df_climo_temp.columns)
color = plt.cm.twilight(np.linspace(0, 1, n))
mpl.rcParams['axes.prop_cycle'] = cycler('color', color)

# Create a plot where all the years are combined in a single graph
fig_comb = plt.figure(figsize=(7, 5))
ax_comb = fig_comb.add_subplot(111)
#ids_df_climo.to_csv(workspace + 'test_final_climo.csv')
# Add each year to same plot
for ycol in ids_df_climo.columns:
    print(ycol)
    ax_comb.plot(ids_df_climo.index * 3, ids_df_climo[ycol], label=str(ycol),
                 linewidth=0.5)  # * 3 is bc each sample is 3km further inland

ax_comb.set_ylabel('Shortwave White Sky Albedo')
ax_comb.set_ylim(0.0, 1.0)
ax_comb.set_xlabel('Km from Coastline')
fig_comb.suptitle(aoi_name + ' 2000-2020 Mean')
plt.legend(ncol=3, loc='lower right', fontsize=7, title='Monthly Mean')
fig_comb.savefig(csv_path[:-4] + aoi_name.replace(' ', '_') + '_2000-2020_mean_' + '_Monthly_Averages2.png',
                 dpi=600)

plt.show()
years = [i for i in range(2000, 2021, 1)]

# This part is the monthly averages
#TODO make these into functions
for year in years:
    ts_df_yr = ts_df[str(year)]
    
    # Here's where the subsetting by year then month happens
    monthly_mean_sr = ts_df_yr.groupby(['ID', pd.Grouper(freq='M')])['SW_WSA'].mean()
    monthly_mean_df = pd.DataFrame(monthly_mean_sr)

    # Pull off the dates and ID numbers (corresponding to distance from coast for transects),
    # and make a new DF with unique values only
    dates = monthly_mean_df.index.get_level_values('Date').tolist()
    ids = monthly_mean_df.index.get_level_values('ID').tolist()
    ids_df = pd.DataFrame({'ID': ids})
    ids_df.drop_duplicates('ID', keep='first', inplace=True)
    ids_df['ID'] = ids_df['ID'].astype(int)
    ids_df.set_index('ID', inplace=True)
    ids_df.sort_index(inplace=True)

    # Use a temporary DF to organize the SW WSA values each time period into columns, then add them
    # to the previously created ids_df, so we have a df where the index is the IDs, then cols are each
    # month's average SW WSA
    for dt in dates:
        build_df = monthly_mean_df.iloc[monthly_mean_df.index.get_level_values('Date') == dt].copy()
        build_df['ID_int'] = build_df.index.get_level_values('ID').astype(int)
        build_df = build_df.sort_values('ID_int')
        build_df.set_index('ID_int', inplace=True)
        build_df.sort_index(inplace=True)
        ids_df[str(dt)] = build_df['SW_WSA']

        # To check that the indices are aligned right, uncomment the below and check output
        #ids_df['test_index'] = build_df.index

        #ids_df = ids_df.join(build_df, lsuffix='_left', rsuffix='_right')

    # Make an overall average of SW WSA to use as a basline for a simpler set of plots
    #overall_ids_df[str(year) + '_mean'] = ids_df.mean(axis=1)
    #overall_ids_df = overall_ids_df.merge(ids_df, left_on='ID', right_on='ID')

    # Set up the color cycler for the plot
    n = len(ids_df.columns)
    color = plt.cm.twilight(np.linspace(0, 1, n))
    mpl.rcParams['axes.prop_cycle'] = cycler('color', color)

    # Create a plot where all the years are combined in a single graph
    fig_comb = plt.figure(figsize=(7, 5))
    ax_comb = fig_comb.add_subplot(111)

    # Add each year to same plot -- for some reason a 'undefined' values comes back first, so
    # check for year part first and only use cols with a valid part of the date in them, i.e. '20*'
    for ycol in ids_df.columns:
        if '20' in str(ycol):
            ax_comb.plot(ids_df.index * 3, ids_df[ycol], label=str(ycol[5:7]), linewidth=0.5)
            # *3 is bc each sample is 3km further inland

    ax_comb.set_ylabel('Shortwave White Sky Albedo')
    ax_comb.set_ylim(0.0, 1.0)
    ax_comb.set_xlabel('Km from Coastline')
    fig_comb.suptitle(aoi_name + ', year ' + str(year) + ' Monthly Averages')
    plt.legend(ncol=3, loc='lower right', fontsize=7, title='Months')
    fig_comb.savefig(csv_path[:-4] + aoi_name.replace(' ', '_') + '_year_' + str(year) + '_Monthly_Averages2.png',
                     dpi=600)

    plt.show()

# These are the ten day averages.
#TODO make these into functions...

for year in years:
    ts_df_yr = ts_df[str(year)]
    # print(ts_df_yr.head())
    # Here's where the subsetting by year then month happens
    tenday_mean_sr = ts_df_yr.groupby(['ID', pd.Grouper(freq='10D')])['SW_WSA'].mean()
    tenday_mean_df = pd.DataFrame(tenday_mean_sr)
    #tenday_mean_df.sort_index(inplace=True)
    #tenday_mean_df.to_csv(workspace + str(year) + "tenday_mean.csv")

    dates = tenday_mean_df.index.get_level_values('Date').tolist()
    ids = tenday_mean_df.index.get_level_values('ID').tolist()
    ids_df = pd.DataFrame({'ID': ids})
    ids_df.drop_duplicates('ID', keep='first', inplace=True)
    ids_df['ID'] = ids_df['ID'].astype(int)
    ids_df.set_index('ID', inplace=True)
    ids_df.sort_index(inplace=True)

    #ids_df.to_csv(workspace + 'ids_df_empty.csv')
    for dt in dates:
        build_df = tenday_mean_df.iloc[tenday_mean_df.index.get_level_values('Date') == dt].copy()
        build_df['ID_int'] = build_df.index.get_level_values('ID').astype(int)
        build_df = build_df.sort_values('ID_int')
        build_df.set_index('ID_int', inplace=True)
        build_df.sort_index(inplace=True)
        ids_df[str(dt)] = build_df['SW_WSA']

        # To check that the indices are aligned right, uncomment the below and check output
        #ids_df['test_index'] = build_df.index
        #ids_df.to_csv(workspace + 'test_index_alignment.csv')
        #ids_df = ids_df.join(build_df, lsuffix='_left', rsuffix='_right')


    n = len(ids_df.columns)
    color = plt.cm.twilight(np.linspace(0, 1, n))
    mpl.rcParams['axes.prop_cycle'] = cycler('color', color)

    ### Create a plot where all the years are combined in a single graph
    fig_comb = plt.figure(figsize=(8, 5))
    ax_comb = fig_comb.add_subplot(111)

    # Add each year to same plot -- for some reason a 'undefined' values comes back first, so
    # check for year part first
    for ycol in ids_df.columns:
        if '20' in str(ycol):
            ax_comb.plot(ids_df.index * 3, ids_df[ycol], label=str(ycol)[5:10], linewidth=0.5)

    ax_comb.set_ylabel('Shortwave White Sky Albedo')
    ax_comb.set_ylim(0.0, 1.0)
    ax_comb.set_xlabel('Km from Coastline')
    fig_comb.suptitle(aoi_name + ', year ' + str(year) + ' Ten Day Averages')
    plt.legend(ncol=3, loc='lower right', fontsize=7, title='10 Day Averages')
    fig_comb.savefig(csv_path[:-4] + aoi_name.replace(' ', '_') + '_year_' + str(year) + '_Ten_Day_Averages2.png',
                     dpi=600)

    plt.show()

