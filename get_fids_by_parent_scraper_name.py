import argparse
import main_launcher

def parse_cmdline_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--scraper-name',
        '-s',
        help='Scraper parent name to get fids from  specific customer: user Id. '
             'If not passed: the all_customers_scraping will start if allowed in settings',
        type=str
    )

    args = parser.parse_args()
    return parser, args

def main():
    """
    Get all ruralvia financial entity ids retrieving based on scraper inheritance.
    Extract information from currently configured link financial_entity_id to scraper at main_launcher.py
    Example:
    --------
        'python3 get_fids_by_parent_scraper_name.py -s ruralvia'

    Command line parameters:
    ------------------------
        --scraper-name, -s
        Name of the parent scraper
    """
    parser, args = parse_cmdline_args()
    scraper_name = args.scraper_name
    scraper_name = 'RuralviaScraper'
    all_fids = main_launcher.FIN_ENTITY_ID_TO_SCRAPER
    for fid in all_fids:
        args.scraper_name
        scraper = all_fids.get(fid)
        scraper_base = str(scraper.__bases__)
        if 'RURALVIA'.lower() in scraper_base.lower():
            print('{}, -- {}'.format(fid, str(scraper).split('.')[-1].strip('\'>')))
        #print('Clase: {} {}'.format(str(scraper).split('.')[-1], scraper.__bases__))
if __name__ == '__main__':
    main()