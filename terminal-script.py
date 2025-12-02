import API.flipkart as flipkart
import asyncio
import json


async def main(link, pincode):
    # Fetch from web scraping (existing method)
    print('Fetching product details from web scraping...')
    result = await flipkart.getProductDetails(link, pincode)
    
    print('\n=== WEB SCRAPING RESULTS ===')
    try:
        print('Product Name : '+result["name"])
        print('Current Price : '+str(result["current_price"]))
        print('Original Price : '+str(result["original_price"]))
        print('Discount : '+result["discount"])
        print('Share URL : '+result["share_url"])
        print('F-Assure Product : '+str(result["fassured"]))
        print('In Stock (general) : ' +
              str(result["stock_details"]["general_stock"]))
        print('In Stock (for pincode '+str(result["stock_details"]["pincode"])+') : ' +
              str(result["stock_details"]["pincode_stock"]))
    except:
        print('Error : Some error occurred while fetching product details from web scraping')
    
    # Fetch from Flipkart Affiliate API
    print('\n=== FLIPKART AFFILIATE API RESULTS ===')
    apiResult = await flipkart.getProductDetailsFromAPI(link)
    
    if 'error' in apiResult:
        print('Error : ' + apiResult['error'])
        if 'product_id' in apiResult:
            print('Product ID extracted: ' + apiResult['product_id'])
    else:
        print('Source : ' + apiResult.get('source', 'N/A'))
        if 'product_id' in apiResult:
            print('Product ID : ' + apiResult['product_id'])
        if 'name' in apiResult:
            print('Product Name : ' + apiResult['name'])
        if 'current_price' in apiResult:
            print('Current Price : ₹' + str(apiResult['current_price']))
        if 'original_price' in apiResult:
            print('Original Price : ₹' + str(apiResult['original_price']))
        if 'in_stock' in apiResult:
            print('In Stock : ' + str(apiResult['in_stock']))
        if 'product_url' in apiResult:
            print('Product URL : ' + apiResult['product_url'])
        if 'description' in apiResult:
            desc = str(apiResult['description'])
            print('Description : ' + (desc[:100] + '...' if len(desc) > 100 else desc))
        if 'raw_response' in apiResult:
            print('\n--- Full API Response (JSON) ---')
            try:
                # Pretty print the JSON response
                formatted_json = json.dumps(apiResult['raw_response'], indent=2, ensure_ascii=False)
                print(formatted_json)
            except:
                print('Raw Response: ' + str(apiResult['raw_response']))
    
    print(br)
    check = input('Check out other product? (Y/N)')
    if check == 'y' or check == 'Y':
        inputData = askInput()
        await main(inputData[0], inputData[1])
    else:
        exit()


br = '___________________________________________________________'

print('=> flipkart-product-stock <=')
print('=> Flipkart Product Stock Details in a specific pincode <=')


def askInput():
    print(br)
    link = input("Input link of product : ")
    pincode = input("Your pincode : ")
    print(br)
    print('Please wait while we check your product on Flipkart...')
    print(br)
    return [link, pincode]


inputData = askInput()
asyncio.run(main(inputData[0], inputData[1]))
