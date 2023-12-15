# ISO 4217
# https://en.wikipedia.org/wiki/ISO_4217

CODES_TO_ALPHA = {
    784: 'AED', 971: 'AFN', 8: 'ALL', 51: 'AMD', 532: 'ANG', 973: 'AOA', 32: 'ARS', 36: 'AUD', 533: 'AWG',
    944: 'AZN', 977: 'BAM', 52: 'BBD', 50: 'BDT', 975: 'BGN', 48: 'BHD', 108: 'BIF', 60: 'BMD', 96: 'BND',
    68: 'BOB', 986: 'BRL', 44: 'BSD', 64: 'BTN', 72: 'BWP', 933: 'BYN', 84: 'BZD', 124: 'CAD', 976: 'CDF',
    756: 'CHF', 152: 'CLP', 156: 'CNY', 170: 'COP', 188: 'CRC', 931: 'CUC', 192: 'CUP', 132: 'CVE',
    203: 'CZK', 262: 'DJF', 208: 'DKK', 214: 'DOP', 12: 'DZD', 818: 'EGP', 232: 'ERN', 230: 'ETB', 978: 'EUR',
    242: 'FJD', 238: 'FKP', 826: 'GBP', 981: 'GEL', 936: 'GHS', 292: 'GIP', 270: 'GMD', 324: 'GNF',
    320: 'GTQ', 328: 'GYD', 344: 'HKD', 340: 'HNL', 191: 'HRK', 332: 'HTG', 348: 'HUF', 360: 'IDR',
    376: 'ILS', 356: 'INR', 368: 'IQD', 364: 'IRR', 352: 'ISK', 388: 'JMD', 400: 'JOD', 392: 'JPY',
    404: 'KES', 417: 'KGS', 116: 'KHR', 174: 'KMF', 408: 'KPW', 410: 'KRW', 414: 'KWD', 136: 'KYD',
    398: 'KZT', 418: 'LAK', 422: 'LBP', 144: 'LKR', 430: 'LRD', 426: 'LSL', 434: 'LYD', 504: 'MAD',
    498: 'MDL', 969: 'MGA', 807: 'MKD', 104: 'MMK', 496: 'MNT', 446: 'MOP', 478: 'MRO', 480: 'MUR',
    462: 'MVR', 454: 'MWK', 484: 'MXN', 458: 'MYR', 943: 'MZN', 516: 'NAD', 566: 'NGN', 558: 'NIO',
    578: 'NOK', 524: 'NPR', 554: 'NZD', 512: 'OMR', 590: 'PAB', 604: 'PEN', 598: 'PGK', 608: 'PHP',
    586: 'PKR', 985: 'PLN', 600: 'PYG', 634: 'QAR', 946: 'RON', 941: 'RSD', 643: 'RUB', 646: 'RWF',
    682: 'SAR', 90: 'SBD', 690: 'SCR', 938: 'SDG', 752: 'SEK', 702: 'SGD', 654: 'SHP', 694: 'SLL', 706: 'SOS',
    968: 'SRD', 728: 'SSP', 678: 'STD', 222: 'SVC', 760: 'SYP', 748: 'SZL', 764: 'THB', 972: 'TJS',
    934: 'TMT', 788: 'TND', 776: 'TOP', 949: 'TRY', 780: 'TTD', 901: 'TWD', 834: 'TZS', 980: 'UAH',
    800: 'UGX', 840: 'USD', 858: 'UYU', 860: 'UZS', 937: 'VEF', 704: 'VND', 548: 'VUV', 882: 'WST',
    950: 'XAF', 961: 'XAG', 959: 'XAU', 955: 'XBA', 956: 'XBB', 957: 'XBC', 958: 'XBD', 951: 'XCD',
    960: 'XDR', 952: 'XOF', 964: 'XPD', 953: 'XPF', 962: 'XPT', 994: 'XSU', 963: 'XTS', 965: 'XUA',
    999: 'XXX', 886: 'YER', 710: 'ZAR', 967: 'ZMW', 932: 'ZWL'
}

FULL_LIST = [
    {
        "alpha_3": "AED",
        "name": "UAE Dirham",
        "numeric": "784"
    },
    {
        "alpha_3": "AFN",
        "name": "Afghani",
        "numeric": "971"
    },
    {
        "alpha_3": "ALL",
        "name": "Lek",
        "numeric": "008"
    },
    {
        "alpha_3": "AMD",
        "name": "Armenian Dram",
        "numeric": "051"
    },
    {
        "alpha_3": "ANG",
        "name": "Netherlands Antillean Guilder",
        "numeric": "532"
    },
    {
        "alpha_3": "AOA",
        "name": "Kwanza",
        "numeric": "973"
    },
    {
        "alpha_3": "ARS",
        "name": "Argentine Peso",
        "numeric": "032"
    },
    {
        "alpha_3": "AUD",
        "name": "Australian Dollar",
        "numeric": "036"
    },
    {
        "alpha_3": "AWG",
        "name": "Aruban Florin",
        "numeric": "533"
    },
    {
        "alpha_3": "AZN",
        "name": "Azerbaijanian Manat",
        "numeric": "944"
    },
    {
        "alpha_3": "BAM",
        "name": "Convertible Mark",
        "numeric": "977"
    },
    {
        "alpha_3": "BBD",
        "name": "Barbados Dollar",
        "numeric": "052"
    },
    {
        "alpha_3": "BDT",
        "name": "Taka",
        "numeric": "050"
    },
    {
        "alpha_3": "BGN",
        "name": "Bulgarian Lev",
        "numeric": "975"
    },
    {
        "alpha_3": "BHD",
        "name": "Bahraini Dinar",
        "numeric": "048"
    },
    {
        "alpha_3": "BIF",
        "name": "Burundi Franc",
        "numeric": "108"
    },
    {
        "alpha_3": "BMD",
        "name": "Bermudian Dollar",
        "numeric": "060"
    },
    {
        "alpha_3": "BND",
        "name": "Brunei Dollar",
        "numeric": "096"
    },
    {
        "alpha_3": "BOB",
        "name": "Boliviano",
        "numeric": "068"
    },
    {
        "alpha_3": "BRL",
        "name": "Brazilian Real",
        "numeric": "986"
    },
    {
        "alpha_3": "BSD",
        "name": "Bahamian Dollar",
        "numeric": "044"
    },
    {
        "alpha_3": "BTN",
        "name": "Ngultrum",
        "numeric": "064"
    },
    {
        "alpha_3": "BWP",
        "name": "Pula",
        "numeric": "072"
    },
    {
        "alpha_3": "BYN",
        "name": "Belarusian Ruble",
        "numeric": "933"
    },
    {
        "alpha_3": "BZD",
        "name": "Belize Dollar",
        "numeric": "084"
    },
    {
        "alpha_3": "CAD",
        "name": "Canadian Dollar",
        "numeric": "124"
    },
    {
        "alpha_3": "CDF",
        "name": "Congolese Franc",
        "numeric": "976"
    },
    {
        "alpha_3": "CHF",
        "name": "Swiss Franc",
        "numeric": "756"
    },
    {
        "alpha_3": "CLP",
        "name": "Chilean Peso",
        "numeric": "152"
    },
    {
        "alpha_3": "CNY",
        "name": "Yuan Renminbi",
        "numeric": "156"
    },
    {
        "alpha_3": "COP",
        "name": "Colombian Peso",
        "numeric": "170"
    },
    {
        "alpha_3": "CRC",
        "name": "Costa Rican Colon",
        "numeric": "188"
    },
    {
        "alpha_3": "CUC",
        "name": "Peso Convertible",
        "numeric": "931"
    },
    {
        "alpha_3": "CUP",
        "name": "Cuban Peso",
        "numeric": "192"
    },
    {
        "alpha_3": "CVE",
        "name": "Cabo Verde Escudo",
        "numeric": "132"
    },
    {
        "alpha_3": "CZK",
        "name": "Czech Koruna",
        "numeric": "203"
    },
    {
        "alpha_3": "DJF",
        "name": "Djibouti Franc",
        "numeric": "262"
    },
    {
        "alpha_3": "DKK",
        "name": "Danish Krone",
        "numeric": "208"
    },
    {
        "alpha_3": "DOP",
        "name": "Dominican Peso",
        "numeric": "214"
    },
    {
        "alpha_3": "DZD",
        "name": "Algerian Dinar",
        "numeric": "012"
    },
    {
        "alpha_3": "EGP",
        "name": "Egyptian Pound",
        "numeric": "818"
    },
    {
        "alpha_3": "ERN",
        "name": "Nakfa",
        "numeric": "232"
    },
    {
        "alpha_3": "ETB",
        "name": "Ethiopian Birr",
        "numeric": "230"
    },
    {
        "alpha_3": "EUR",
        "name": "Euro",
        "numeric": "978"
    },
    {
        "alpha_3": "FJD",
        "name": "Fiji Dollar",
        "numeric": "242"
    },
    {
        "alpha_3": "FKP",
        "name": "Falkland Islands Pound",
        "numeric": "238"
    },
    {
        "alpha_3": "GBP",
        "name": "Pound Sterling",
        "numeric": "826"
    },
    {
        "alpha_3": "GEL",
        "name": "Lari",
        "numeric": "981"
    },
    {
        "alpha_3": "GHS",
        "name": "Ghana Cedi",
        "numeric": "936"
    },
    {
        "alpha_3": "GIP",
        "name": "Gibraltar Pound",
        "numeric": "292"
    },
    {
        "alpha_3": "GMD",
        "name": "Dalasi",
        "numeric": "270"
    },
    {
        "alpha_3": "GNF",
        "name": "Guinea Franc",
        "numeric": "324"
    },
    {
        "alpha_3": "GTQ",
        "name": "Quetzal",
        "numeric": "320"
    },
    {
        "alpha_3": "GYD",
        "name": "Guyana Dollar",
        "numeric": "328"
    },
    {
        "alpha_3": "HKD",
        "name": "Hong Kong Dollar",
        "numeric": "344"
    },
    {
        "alpha_3": "HNL",
        "name": "Lempira",
        "numeric": "340"
    },
    {
        "alpha_3": "HRK",
        "name": "Kuna",
        "numeric": "191"
    },
    {
        "alpha_3": "HTG",
        "name": "Gourde",
        "numeric": "332"
    },
    {
        "alpha_3": "HUF",
        "name": "Forint",
        "numeric": "348"
    },
    {
        "alpha_3": "IDR",
        "name": "Rupiah",
        "numeric": "360"
    },
    {
        "alpha_3": "ILS",
        "name": "New Israeli Sheqel",
        "numeric": "376"
    },
    {
        "alpha_3": "INR",
        "name": "Indian Rupee",
        "numeric": "356"
    },
    {
        "alpha_3": "IQD",
        "name": "Iraqi Dinar",
        "numeric": "368"
    },
    {
        "alpha_3": "IRR",
        "name": "Iranian Rial",
        "numeric": "364"
    },
    {
        "alpha_3": "ISK",
        "name": "Iceland Krona",
        "numeric": "352"
    },
    {
        "alpha_3": "JMD",
        "name": "Jamaican Dollar",
        "numeric": "388"
    },
    {
        "alpha_3": "JOD",
        "name": "Jordanian Dinar",
        "numeric": "400"
    },
    {
        "alpha_3": "JPY",
        "name": "Yen",
        "numeric": "392"
    },
    {
        "alpha_3": "KES",
        "name": "Kenyan Shilling",
        "numeric": "404"
    },
    {
        "alpha_3": "KGS",
        "name": "Som",
        "numeric": "417"
    },
    {
        "alpha_3": "KHR",
        "name": "Riel",
        "numeric": "116"
    },
    {
        "alpha_3": "KMF",
        "name": "Comoro Franc",
        "numeric": "174"
    },
    {
        "alpha_3": "KPW",
        "name": "North Korean Won",
        "numeric": "408"
    },
    {
        "alpha_3": "KRW",
        "name": "Won",
        "numeric": "410"
    },
    {
        "alpha_3": "KWD",
        "name": "Kuwaiti Dinar",
        "numeric": "414"
    },
    {
        "alpha_3": "KYD",
        "name": "Cayman Islands Dollar",
        "numeric": "136"
    },
    {
        "alpha_3": "KZT",
        "name": "Tenge",
        "numeric": "398"
    },
    {
        "alpha_3": "LAK",
        "name": "Kip",
        "numeric": "418"
    },
    {
        "alpha_3": "LBP",
        "name": "Lebanese Pound",
        "numeric": "422"
    },
    {
        "alpha_3": "LKR",
        "name": "Sri Lanka Rupee",
        "numeric": "144"
    },
    {
        "alpha_3": "LRD",
        "name": "Liberian Dollar",
        "numeric": "430"
    },
    {
        "alpha_3": "LSL",
        "name": "Loti",
        "numeric": "426"
    },
    {
        "alpha_3": "LYD",
        "name": "Libyan Dinar",
        "numeric": "434"
    },
    {
        "alpha_3": "MAD",
        "name": "Moroccan Dirham",
        "numeric": "504"
    },
    {
        "alpha_3": "MDL",
        "name": "Moldovan Leu",
        "numeric": "498"
    },
    {
        "alpha_3": "MGA",
        "name": "Malagasy Ariary",
        "numeric": "969"
    },
    {
        "alpha_3": "MKD",
        "name": "Denar",
        "numeric": "807"
    },
    {
        "alpha_3": "MMK",
        "name": "Kyat",
        "numeric": "104"
    },
    {
        "alpha_3": "MNT",
        "name": "Tugrik",
        "numeric": "496"
    },
    {
        "alpha_3": "MOP",
        "name": "Pataca",
        "numeric": "446"
    },
    {
        "alpha_3": "MRO",
        "name": "Ouguiya",
        "numeric": "478"
    },
    {
        "alpha_3": "MUR",
        "name": "Mauritius Rupee",
        "numeric": "480"
    },
    {
        "alpha_3": "MVR",
        "name": "Rufiyaa",
        "numeric": "462"
    },
    {
        "alpha_3": "MWK",
        "name": "Malawi Kwacha",
        "numeric": "454"
    },
    {
        "alpha_3": "MXN",
        "name": "Mexican Peso",
        "numeric": "484"
    },
    {
        "alpha_3": "MYR",
        "name": "Malaysian Ringgit",
        "numeric": "458"
    },
    {
        "alpha_3": "MZN",
        "name": "Mozambique Metical",
        "numeric": "943"
    },
    {
        "alpha_3": "NAD",
        "name": "Namibia Dollar",
        "numeric": "516"
    },
    {
        "alpha_3": "NGN",
        "name": "Naira",
        "numeric": "566"
    },
    {
        "alpha_3": "NIO",
        "name": "Cordoba Oro",
        "numeric": "558"
    },
    {
        "alpha_3": "NOK",
        "name": "Norwegian Krone",
        "numeric": "578"
    },
    {
        "alpha_3": "NPR",
        "name": "Nepalese Rupee",
        "numeric": "524"
    },
    {
        "alpha_3": "NZD",
        "name": "New Zealand Dollar",
        "numeric": "554"
    },
    {
        "alpha_3": "OMR",
        "name": "Rial Omani",
        "numeric": "512"
    },
    {
        "alpha_3": "PAB",
        "name": "Balboa",
        "numeric": "590"
    },
    {
        "alpha_3": "PEN",
        "name": "Sol",
        "numeric": "604"
    },
    {
        "alpha_3": "PGK",
        "name": "Kina",
        "numeric": "598"
    },
    {
        "alpha_3": "PHP",
        "name": "Philippine Peso",
        "numeric": "608"
    },
    {
        "alpha_3": "PKR",
        "name": "Pakistan Rupee",
        "numeric": "586"
    },
    {
        "alpha_3": "PLN",
        "name": "Zloty",
        "numeric": "985"
    },
    {
        "alpha_3": "PYG",
        "name": "Guarani",
        "numeric": "600"
    },
    {
        "alpha_3": "QAR",
        "name": "Qatari Rial",
        "numeric": "634"
    },
    {
        "alpha_3": "RON",
        "name": "Romanian Leu",
        "numeric": "946"
    },
    {
        "alpha_3": "RSD",
        "name": "Serbian Dinar",
        "numeric": "941"
    },
    {
        "alpha_3": "RUB",
        "name": "Russian Ruble",
        "numeric": "643"
    },
    {
        "alpha_3": "RWF",
        "name": "Rwanda Franc",
        "numeric": "646"
    },
    {
        "alpha_3": "SAR",
        "name": "Saudi Riyal",
        "numeric": "682"
    },
    {
        "alpha_3": "SBD",
        "name": "Solomon Islands Dollar",
        "numeric": "090"
    },
    {
        "alpha_3": "SCR",
        "name": "Seychelles Rupee",
        "numeric": "690"
    },
    {
        "alpha_3": "SDG",
        "name": "Sudanese Pound",
        "numeric": "938"
    },
    {
        "alpha_3": "SEK",
        "name": "Swedish Krona",
        "numeric": "752"
    },
    {
        "alpha_3": "SGD",
        "name": "Singapore Dollar",
        "numeric": "702"
    },
    {
        "alpha_3": "SHP",
        "name": "Saint Helena Pound",
        "numeric": "654"
    },
    {
        "alpha_3": "SLL",
        "name": "Leone",
        "numeric": "694"
    },
    {
        "alpha_3": "SOS",
        "name": "Somali Shilling",
        "numeric": "706"
    },
    {
        "alpha_3": "SRD",
        "name": "Surinam Dollar",
        "numeric": "968"
    },
    {
        "alpha_3": "SSP",
        "name": "South Sudanese Pound",
        "numeric": "728"
    },
    {
        "alpha_3": "STD",
        "name": "Dobra",
        "numeric": "678"
    },
    {
        "alpha_3": "SVC",
        "name": "El Salvador Colon",
        "numeric": "222"
    },
    {
        "alpha_3": "SYP",
        "name": "Syrian Pound",
        "numeric": "760"
    },
    {
        "alpha_3": "SZL",
        "name": "Lilangeni",
        "numeric": "748"
    },
    {
        "alpha_3": "THB",
        "name": "Baht",
        "numeric": "764"
    },
    {
        "alpha_3": "TJS",
        "name": "Somoni",
        "numeric": "972"
    },
    {
        "alpha_3": "TMT",
        "name": "Turkmenistan New Manat",
        "numeric": "934"
    },
    {
        "alpha_3": "TND",
        "name": "Tunisian Dinar",
        "numeric": "788"
    },
    {
        "alpha_3": "TOP",
        "name": "Pa’anga",
        "numeric": "776"
    },
    {
        "alpha_3": "TRY",
        "name": "Turkish Lira",
        "numeric": "949"
    },
    {
        "alpha_3": "TTD",
        "name": "Trinidad and Tobago Dollar",
        "numeric": "780"
    },
    {
        "alpha_3": "TWD",
        "name": "New Taiwan Dollar",
        "numeric": "901"
    },
    {
        "alpha_3": "TZS",
        "name": "Tanzanian Shilling",
        "numeric": "834"
    },
    {
        "alpha_3": "UAH",
        "name": "Hryvnia",
        "numeric": "980"
    },
    {
        "alpha_3": "UGX",
        "name": "Uganda Shilling",
        "numeric": "800"
    },
    {
        "alpha_3": "USD",
        "name": "US Dollar",
        "numeric": "840"
    },
    {
        "alpha_3": "UYU",
        "name": "Peso Uruguayo",
        "numeric": "858"
    },
    {
        "alpha_3": "UZS",
        "name": "Uzbekistan Sum",
        "numeric": "860"
    },
    {
        "alpha_3": "VEF",
        "name": "Bolívar",
        "numeric": "937"
    },
    {
        "alpha_3": "VND",
        "name": "Dong",
        "numeric": "704"
    },
    {
        "alpha_3": "VUV",
        "name": "Vatu",
        "numeric": "548"
    },
    {
        "alpha_3": "WST",
        "name": "Tala",
        "numeric": "882"
    },
    {
        "alpha_3": "XAF",
        "name": "CFA Franc BEAC",
        "numeric": "950"
    },
    {
        "alpha_3": "XAG",
        "name": "Silver",
        "numeric": "961"
    },
    {
        "alpha_3": "XAU",
        "name": "Gold",
        "numeric": "959"
    },
    {
        "alpha_3": "XBA",
        "name": "Bond Markets Unit European Composite Unit (EURCO)",
        "numeric": "955"
    },
    {
        "alpha_3": "XBB",
        "name": "Bond Markets Unit European Monetary Unit (E.M.U.-6)",
        "numeric": "956"
    },
    {
        "alpha_3": "XBC",
        "name": "Bond Markets Unit European Unit of Account 9 (E.U.A.-9)",
        "numeric": "957"
    },
    {
        "alpha_3": "XBD",
        "name": "Bond Markets Unit European Unit of Account 17 (E.U.A.-17)",
        "numeric": "958"
    },
    {
        "alpha_3": "XCD",
        "name": "East Caribbean Dollar",
        "numeric": "951"
    },
    {
        "alpha_3": "XDR",
        "name": "SDR (Special Drawing Right)",
        "numeric": "960"
    },
    {
        "alpha_3": "XOF",
        "name": "CFA Franc BCEAO",
        "numeric": "952"
    },
    {
        "alpha_3": "XPD",
        "name": "Palladium",
        "numeric": "964"
    },
    {
        "alpha_3": "XPF",
        "name": "CFP Franc",
        "numeric": "953"
    },
    {
        "alpha_3": "XPT",
        "name": "Platinum",
        "numeric": "962"
    },
    {
        "alpha_3": "XSU",
        "name": "Sucre",
        "numeric": "994"
    },
    {
        "alpha_3": "XTS",
        "name": "Codes specifically reserved for testing purposes",
        "numeric": "963"
    },
    {
        "alpha_3": "XUA",
        "name": "ADB Unit of Account",
        "numeric": "965"
    },
    {
        "alpha_3": "XXX",
        "name": "The codes assigned for transactions where no currency is involved",
        "numeric": "999"
    },
    {
        "alpha_3": "YER",
        "name": "Yemeni Rial",
        "numeric": "886"
    },
    {
        "alpha_3": "ZAR",
        "name": "Rand",
        "numeric": "710"
    },
    {
        "alpha_3": "ZMW",
        "name": "Zambian Kwacha",
        "numeric": "967"
    },
    {
        "alpha_3": "ZWL",
        "name": "Zimbabwe Dollar",
        "numeric": "932"
    }
]


def get_by_code(currency_code: int) -> str:
    return CODES_TO_ALPHA[currency_code]
