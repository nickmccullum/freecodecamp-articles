import pandas as pd
import xlsxwriter
import boto3

IEX_API_Key = ''

#Specify the stock tickers that will be included in our spreadsheet
tickers = [
            'MSFT',
            'AAPL',
            'AMZN',
            'GOOG',
            'FB',
            'BRK.B',
            'JNJ',
            'WMT',
            'V',
            'PG'
            ]


#Create an empty string called `ticker_string` that we'll add tickers and commas to
ticker_string = ','.join(tickers)

#Create the endpoint strings
endpoints = 'price,stats'

#Interpolate the endpoint strings into the HTTP_request string
HTTP_request = f'https://cloud.iexapis.com/stable/stock/market/batch?symbols={ticker_string}&types={endpoints}&range=1y&token={IEX_API_Key}'

# Send the request and use pandas to directly read the json answer
raw_data = pd.read_json(HTTP_request)

#Create an empty pandas DataFrame to append our parsed values into during our for loop
output_data = pd.DataFrame(pd.np.empty((0,4)))

for ticker in raw_data.columns:
	
    #Parse the company's name
    company_name = raw_data[ticker]['stats']['companyName']
    
    #Parse the company's stock price
    stock_price = raw_data[ticker]['price']
    
    #Parse the company's dividend yield
    dividend_yield = raw_data[ticker]['stats']['dividendYield']
    
    
    new_column = pd.Series([ticker, company_name, stock_price, dividend_yield])
    output_data = output_data.append(new_column, ignore_index = True)

#Change the column names of output_data
output_data.columns = ['Ticker', 'Company Name', 'Stock Price', 'Dividend Yield']

#Change the index of output_data
output_data.set_index('Ticker', inplace=True)

#Replace the missing values of the 'Dividend Yield' column with 0
output_data['Dividend Yield'].fillna(0,inplace=True)

writer = pd.ExcelWriter('stock_market_data.xlsx', engine='xlsxwriter')

output_data.to_excel(writer, sheet_name='Stock Market Data')

header_template = writer.book.add_format(
        {
            'font_color': '#ffffff',
            'bg_color': '#135485',
            'border': 1
        }
    )

string_template = writer.book.add_format(
        {
            'bg_color': '#DADADA',
            'border': 1
        }
    )

dollar_template = writer.book.add_format(
        {
            'num_format':'$0.00',
            'bg_color': '#DADADA',
            'border': 1
        }
    )

percent_template = writer.book.add_format(
        {
            'num_format':'0.0%',
            'bg_color': '#DADADA',
            'border': 1
        }
    )


#Format the header of the spreadsheet
writer.sheets['Stock Market Data'].conditional_format('A1:D1', 
                             {
                                'type':     'cell',
                                'criteria': '<>',
                                'value':    '"None"',
                                'format':   header_template
                                }
                            )

#Format the 'Ticker' and 'Company Name' columns
writer.sheets['Stock Market Data'].conditional_format('A2:B11', 
                             {
                                'type':     'cell',
                                'criteria': '<>',
                                'value':    '"None"',
                                'format':   string_template
                                }
                            )

#Format the 'Stock Price' column
writer.sheets['Stock Market Data'].conditional_format('C2:C11', 
                             {
                                'type':     'cell',
                                'criteria': '<>',
                                'value':    '"None"',
                                'format':   dollar_template
                                }
                            )

#Format the 'Dividend Yield' column
writer.sheets['Stock Market Data'].conditional_format('D2:D11', 
                             {
                                'type':     'cell',
                                'criteria': '<>',
                                'value':    '"None"',
                                'format':   percent_template
                                }
                            )

#Specify all column widths
writer.sheets['Stock Market Data'].set_column('B:B', 32)
writer.sheets['Stock Market Data'].set_column('C:C', 18)
writer.sheets['Stock Market Data'].set_column('D:D', 20)

writer.save()

s3 = boto3.resource('s3')
s3.meta.client.upload_file('stock_market_data.xlsx', 'my-S3-bucket', 'stock_market_data.xlsx', ExtraArgs={'ACL':'public-read'})
