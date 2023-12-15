from http.cookies import SimpleCookie
from typing import Dict, Union, Optional, List

from custom_libs.myrequests import MySession
from project.custom_types import Cookie

__version__ = '1.2.0'
__changelog__ = """
1.2.0
update_mass_cookies_typed
1.1.2
upd type hints
1.1.1
upd type hints
1.1.0
update_mass_cookies_from_str
"""


def update_mass_cookies(
        session: MySession,
        cookies: Union[Dict[str, str], Dict[str, Optional[str]]],
        domain: str,
        path: str = '/') -> MySession:
    """
    :param session: (my)requests' session
    :param cookies: dictionary with shape {cookie_name: cookie_value};
                    None 'val' deletes 'name' from the keys
    :param domain: a str 'domain.com', '.domain.com' etc.
    :param path: cookies' path
    :returns session with upd cookies
    """

    for cook_name, val in cookies.items():
        session.cookies.set(cook_name, val, domain=domain, path=path)

    return session


def update_mass_cookies_typed(
        session: MySession,
        cookies: List[Cookie]) -> MySession:
    for cookie in cookies:
        session.cookies.set(cookie.name, cookie.value, domain=cookie.domain, path=cookie.path)
    return session


def update_mass_cookies_from_str(
        session: MySession,
        cookies_str: str,
        domain: str,
        path: str = '/') -> MySession:
    """
    :param session: (my)requests' session
    :param cookies_str: a str like '_abc=hdfgghd;_xyz=sfasdfasdf'
    :param domain: a str 'domain.com', '.domain.com' etc.
    :param path: cookies' path
    :returns session with upd cookies

    >>> from custom_libs import myrequests
    >>> s = myrequests.session()
    >>> s = update_mass_cookies_from_str(s, '_abc=a;_xyz=x', 'web.info')
    >>> s.cookies.get_dict('web.info', '/') == {'_abc': 'a', '_xyz': 'x'}
    True
    >>> s = myrequests.session()
    >>> s = update_mass_cookies_from_str(s, '', 'web.info')
    >>> s.cookies.get_dict('web.info', '/') == {}
    True
    """

    cookies = SimpleCookie()  # type: SimpleCookie
    cookies.load(cookies_str)
    for cook_name, val_morsel in cookies.items():
        # ('_xyz', <Morsel: _xyz=sfasdfasdf>)
        session.cookies.set(cook_name, val_morsel.value, domain=domain, path=path)
    return session
