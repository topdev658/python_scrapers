class Headers:
    def __init__(self, user_agent: str, languages: str, brands: str, platform: str):
        """
        Init Headers class, which is a helper class to construct headers to HTTP requests.
        Note that brands and platform must have double quotes in them.

        :param user_agent: User-Agent header
        :param languages: Accept-Language, e.g. 'en-US,en;q=0.9'
        :param brands: sec-ch-ua header, e.g. '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"'
        :param platform: sec-ch-ua platform, e.g. '"Linux"'
        """
        self.user_agent = user_agent
        self.languages = languages
        self.brands = brands
        self.platform = platform

    def document_get(self, referer):
        obj = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': self.brands,
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': self.platform,
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Dest': 'document',
        }

        if referer is not None:
            obj['Referer'] = referer

        obj.update({
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': self.languages,
        })

        return obj

    def script_get(self, referer: str):
        return {
            'Connection': 'keep-alive',
            'sec-ch-ua': self.brands,
            'sec-ch-ua-mobile': '?0',
            'User-Agent': self.user_agent,
            'sec-ch-ua-platform': self.platform,
            'Accept': '*/*',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Dest': 'script',
            'Referer': referer,
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': self.languages,
        }

    def image_get(self, referer: str):
        return {
            'Connection': 'keep-alive',
            'sec-ch-ua': self.brands,
            'sec-ch-ua-mobile': '?0',
            'User-Agent': self.user_agent,
            'sec-ch-ua-platform': self.platform,
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Dest': 'image',
            'Referer': referer,
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': self.languages,
        }

    def xhr_post(self, referer: str, accept: str, origin: str):
        # Unfortunately we do not set Content-Length
        # and Content-Type to simplify the API
        return {
            'Connection': 'keep-alive',
            # Content-Length
            'sec-ch-ua': self.brands,
            'Accept': accept,
            # Content-Type
            'sec-ch-ua-mobile': '?0',
            'User-Agent': self.user_agent,
            'sec-ch-ua-platform': self.platform,
            'Origin': origin,
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': referer,
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': self.languages,
        }