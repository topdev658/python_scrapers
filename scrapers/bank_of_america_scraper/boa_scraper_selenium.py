from selenium import webdriver


if __name__ == '__main__':
    chromedriver = 'bin/chromedriver'
    options = webdriver.ChromeOptions()
    # options.add_argument('headless')
    options.add_argument('window-size=800x600')
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(executable_path=chromedriver, chrome_options=options)

    # document.cookie="olb_signin_prefill_multi_secure=juan*****:D9AD3EFA2722DC394260CB9A05C618B94CD98242DC4F1C0E:02/21/2019||elen*****:03AA74BB14B5579DEFDE0739FA1A6C553E95E584CFB70B03:02/21/2019; path=/; domain=.bankofamerica.com";