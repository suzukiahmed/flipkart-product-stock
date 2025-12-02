from playwright.async_api import async_playwright
import asyncio
import math
import httpx
import re
from urllib.parse import urlparse, parse_qs


async def getProductDetails(productLink, pincode):
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True, args=['--no-sandbox'])
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36 OPR/68.0.3618.125'
    )
    page = await context.new_page()

    async def route_handler(route):
        resource_type = route.request.resource_type
        if resource_type in ('stylesheet', 'image', 'font'):
            await route.abort()
        else:
            await route.continue_()

    await page.route('**/*', route_handler)
    try:
        try:
            await page.goto(productLink, timeout=10000)
        except:
            None
        try:
            await page.locator('xpath=//div[contains(text(), "currently out of stock")]').wait_for(timeout=1000)
            outOfStock = True
        except:
            outOfStock = False
        try:
            await page.locator('xpath=//div[contains(text(), "Coming Soon")]').wait_for(timeout=800)
            comingSoon = True
        except:
            comingSoon = False
        if (comingSoon or outOfStock):
            inStock = False
        else:
            inStock = True
        if (inStock):
            try:
                pincodeField = page.locator('xpath=//input[@id="pincodeInputId"]')
                await pincodeField.click(click_count=3)
                await pincodeField.type(str(pincode))
            except:
                try:
                    await page.wait_for_selector('input[class="cfnctZ"]', timeout=1200)
                except:
                    pincodeDropDownMenu = page.locator('img[src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI5IiBoZWlnaHQ9IjUiPjxwYXRoIGZpbGw9IiMyMTIxMjEiIGZpbGwtcnVsZT0iZXZlbm9kZCIgZD0iTS4yMjcuNzAzQy0uMTY4LjMxNS0uMDMyIDAgLjUxNCAwaDcuOTY1Yy41NTYgMCAuNjg1LjMxNy4yOTguNjk4TDcuNjQgMS44MThsLTIuNDI3IDIuMzlhMS4wMiAxLjAyIDAgMCAxLTEuNDI3LS4wMDNMLjIyNy43MDN6Ii8+PC9zdmc+"]')
                    await pincodeDropDownMenu.click()
                    await page.wait_for_selector('input[class="cfnctZ"]', timeout=1100)
                pincodeField = page.locator('input[class="cfnctZ"]').first
                await pincodeField.click(click_count=3)
                await pincodeField.type(str(pincode))
            checkButton = page.locator('xpath=//span[contains(text(), "Check")]')
            await checkButton.first.click()
            try:
                await page.locator('xpath=//div[contains(text(), "Currently out of stock in this area.")]').wait_for(timeout=2100)
                pincodeStock = False
            except:
                try:
                    await page.locator('xpath=//div[contains(text(), "Not a valid pincode")]').wait_for(timeout=1100)
                    pincodeStock = False
                except:
                    try:
                        await page.locator('xpath=//div[contains(text(), "No seller")]').wait_for(timeout=1100)
                        pincodeStock = False
                    except:
                        pincodeStock = True
        else:
            pincodeStock = False
        webPage = await page.content()

        # Verification mechanism for TRUE pincode stock
        if pincodeStock:
            if webPage.__contains__('No seller') or webPage.__contains__('Not a valid pincode') or webPage.__contains__('out of stock'):
                pincodeStock = False

        webPage = webPage.replace('&amp;', '&')

        try:
            await page.wait_for_selector('h1', timeout=1500)
            productName = await page.evaluate('() => document.querySelector("h1").textContent')
        except:
            productName = webPage.split('class="B_NuCI')[1].split(
                '</span>')[0].split('>')[1].replace('<!-- -->', '').replace('&nbsp;', '')
        try:
            await page.wait_for_selector('div[class="dyC4hf"]', timeout=1000)
            prices = (await page.evaluate('() => document.querySelector("div[class=\\"dyC4hf\\"]").textContent')).replace(',', '')
            currentPrice = int(prices.split('₹')[1].replace(',', ''))
            try:
                discountSelector = page.locator('xpath=//span[contains(text(), "% off")]')
                discountPercentIndicator = await discountSelector.first.text_content()
                originalPrice = int(prices.split('₹')[2].replace(
                    ',', '').split(discountPercentIndicator)[0])
            except:
                originalPrice = currentPrice
                discountPercentIndicator = '0% off'
        except:
            currentPrice = int(webPage.split('<h1')[1].split(">₹")[
                1].split("</div>")[0].replace(',', ''))
            originalPriceFinder = webPage.split('<h1')[1].split(
                ">₹")[2].split("</div>")[0].split('<!-- -->')
            if len(originalPriceFinder) > 1:
                try:
                    originalPriceField = originalPriceFinder[1].replace(
                        ',', '')
                    originalPrice = int(originalPriceField)
                except:
                    originalPrice = currentPrice
            else:
                try:
                    originalPrice = int(webPage.split('_3I9_wc _2p6lqe')[1].split(
                        '</div>')[0].split('>')[1].replace('₹', '').replace(',', ''))
                except:
                    originalPrice = currentPrice
            discount = originalPrice-currentPrice
            discountPercent = math.floor(discount/originalPrice * 100)
            discountPercentIndicator = str(discountPercent) + '% off'
        try:
            await page.wait_for_selector('img[class="jMnjzX"]', timeout=1000)
            fassured = True
        except:
            fassured = False

        stockMessage = {'general_stock': inStock,
                        'pincode': pincode, 'pincode_stock': pincodeStock}
        result = {'name': productName, 'current_price': currentPrice, 'original_price': originalPrice,
                  'discount': discountPercentIndicator, 'share_url': productLink, 'fassured': fassured, 'stock_details': stockMessage}
    except:
        result = {'error': 'Some error occured while fetching product details'}
    finally:
        try:
            await context.close()
            await browser.close()
            await playwright.stop()
        except:
            None
        return result


def extractProductId(productLink):
    """
    Extract product ID from Flipkart/Shopsy URL.
    The actual product ID for the API is the 'pid' query parameter, not the 'itm...' in the path.
    For Flipkart/Shopsy URLs: https://www.flipkart.com/.../p/itm...?pid=ACTUAL_PRODUCT_ID&...
    """
    try:
        # First, try to extract 'pid' from query parameters (this is the actual product ID)
        parsed_url = urlparse(productLink)
        query_params = parse_qs(parsed_url.query)
        
        if 'pid' in query_params:
            pid = query_params['pid'][0]
            if pid:
                return pid
        
        # Fallback: Extract from path if pid is not in query string
        # Pattern 1: /p/itmXXXXXXXXXXXX
        match = re.search(r'/p/(itm[a-zA-Z0-9]+)', parsed_url.path)
        if match:
            return match.group(1)
        
        # Pattern 2: itmXXXXXXXXXXXX anywhere in path
        match = re.search(r'(itm[a-zA-Z0-9]+)', parsed_url.path)
        if match:
            return match.group(1)
        
        # Pattern 3: Check path segments
        parts = parsed_url.path.split('/')
        for part in parts:
            if part.startswith('itm') and len(part) > 3:
                return part
        
        return None
    except Exception as e:
        return None


async def getProductDetailsFromAPI(productLink):
    """
    Fetch product details from Flipkart Affiliate API using product ID.
    Returns product details from the API or None if product ID cannot be extracted or API call fails.
    """
    productId = extractProductId(productLink)
    
    if not productId:
        return {'error': 'Could not extract product ID from URL'}
    
    # API credentials from Postman collection
    affiliateId = "aneesrahm"
    affiliateToken = "7ab4e8f576264fc58287c2f06ce06766"
    apiUrl = f"https://affiliate-api.flipkart.net/affiliate/1.0/product.json?id={productId}"
    
    headers = {
        "Fk-Affiliate-Id": affiliateId,
        "Fk-Affiliate-Token": affiliateToken,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(apiUrl, headers=headers)
            
            if response.status_code == 200:
                apiData = response.json()
                
                # Parse the API response structure
                # The API response structure may vary, so we'll extract what we can
                result = {
                    'source': 'Flipkart Affiliate API',
                    'product_id': productId,
                    'raw_response': apiData
                }
                
                # Try to extract common fields from API response
                if 'productBaseInfo' in apiData:
                    productInfo = apiData['productBaseInfo']
                    if 'productIdentifier' in productInfo:
                        result['product_identifier'] = productInfo['productIdentifier']
                    if 'title' in productInfo:
                        result['name'] = productInfo['title']
                    if 'productDescription' in productInfo:
                        result['description'] = productInfo['productDescription']
                
                if 'productShippingInfo' in apiData:
                    shippingInfo = apiData['productShippingInfo']
                    if 'shippingCharges' in shippingInfo:
                        result['shipping_charges'] = shippingInfo['shippingCharges']
                
                if 'productBaseInfo' in apiData and 'flipkartSpecialPrice' in apiData['productBaseInfo']:
                    result['current_price'] = apiData['productBaseInfo']['flipkartSpecialPrice']['amount']
                
                if 'productBaseInfo' in apiData and 'maximumRetailPrice' in apiData['productBaseInfo']:
                    result['original_price'] = apiData['productBaseInfo']['maximumRetailPrice']['amount']
                
                if 'productBaseInfo' in apiData and 'inStock' in apiData['productBaseInfo']:
                    result['in_stock'] = apiData['productBaseInfo']['inStock']
                
                if 'productBaseInfo' in apiData and 'imageUrls' in apiData['productBaseInfo']:
                    result['image_urls'] = apiData['productBaseInfo']['imageUrls']
                
                if 'productBaseInfo' in apiData and 'productUrl' in apiData['productBaseInfo']:
                    result['product_url'] = apiData['productBaseInfo']['productUrl']
                
                return result
            else:
                return {
                    'error': f'API request failed with status code {response.status_code}',
                    'product_id': productId
                }
    except httpx.TimeoutException:
        return {'error': 'API request timed out', 'product_id': productId}
    except httpx.RequestError as e:
        return {'error': f'API request error: {str(e)}', 'product_id': productId}
    except Exception as e:
        return {'error': f'Error fetching from API: {str(e)}', 'product_id': productId}
