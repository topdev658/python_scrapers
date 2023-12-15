"""Independent module to be able to include
into SantanderOrgWFilialesNuevoLoginChecksScraper and
into SantanderOrgWFilialesChecksScraper
without changes.
"""

import traceback
from typing import List, Tuple

from custom_libs import extract
from project.custom_types import (
    CheckParsed, CheckCollectionScraped,
    AccountScraped, MovementScraped
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers


def download_checks(
        scraper: BasicScraper,
        account_scraped: AccountScraped,
        movements_scraped: List[MovementScraped]) -> Tuple[bool, List[CheckParsed]]:
    if not scraper.basic_should_download_checks():
        return False, []

    checks_parsed = get_check_parsed_from_scraped_data(scraper, account_scraped, movements_scraped)

    for check_parsed in checks_parsed:
        try:

            check_collection_scraped = CheckCollectionScraped(
                OfficeDC=check_parsed['office_dc'],
                CheckType=check_parsed['doc_code'],
                CollectionReference=check_parsed['check_number'],
                Amount=check_parsed['amount'],
                CollectionDate=check_parsed['expiration_date'],
                State=check_parsed['state'],
                CheckQuantity=1,
                KeyValue=check_parsed['keyvalue'],
                CustomerId=scraper.db_customer_id,
                FinancialEntityId=scraper.db_financial_entity_id,
                AccountId=None,
                AccountNo=None,
                StatementId=None,
            )

            statement_data = scraper.db_connector.get_movement_data_from_keyvalue(
                check_parsed['keyvalue'],
                account_scraped.FinancialEntityAccountId,
                account_scraped.CustomerId,
            )
            if statement_data:
                check_collection_scraped = check_collection_scraped._replace(
                    AccountId=statement_data['AccountId'],
                    AccountNo=statement_data['AccountNo'],
                    StatementId=statement_data['InitialId'],
                    CollectionReference=check_parsed['check_number']
                )

            # DAF: for Transactional Check Collection Insertion.
            # relation 1 check collection to 1 check. But for insert we pass
            # a list with the check_parsed instead check_parsed
            scraper.basic_save_check_collection(check_collection_scraped, [check_parsed])

        except:

            scraper.logger.error("{}: {}: can't save check: EXCEPTION\n{}".format(
                check_parsed['check_number'],
                check_parsed['keyvalue'],
                traceback.format_exc()
            ))

    scraper.basic_log_time_spent('GET CHECKS for account {}'.format(account_scraped.FinancialEntityAccountId))
    return True, checks_parsed


def get_check_parsed_from_scraped_data(
        scraper: BasicScraper,
        account_scraped: AccountScraped,
        movements_scraped: List[MovementScraped]) -> List[CheckParsed]:
    if not movements_scraped:
        return []

    scraper.logger.info('{}: process Check Collections: from_date={} to_date={}'.format(
        account_scraped.FinancialEntityAccountId,
        movements_scraped[0].OperationalDate,
        movements_scraped[-1].OperationalDate
    ))

    checks_parsed = []
    for movement in movements_scraped:
        check_concept = extract.re_first_or_blank(
            '(?si)ENTREGA DE DOCUMENTOS PARA SU COMPENSACION',
            movement.StatementDescription
        )
        if not check_concept:
            continue

        extended_description_data = parse_helpers.get_check_data_from_extended_description(
            movement.StatementExtendedDescription)

        state = "ABONADO"
        if movement.Amount < 0:
            state = "DEVUELTO"

        checks_parsed.append({
            'details_link': None,
            'capture_date': movement.OperationalDate,
            'check_number': extended_description_data['checkNumber'],  # Numero de Documento
            'charge_account': '',
            'amount': movement.Amount,
            'expiration_date': movement.OperationalDate,
            'doc_code': extended_description_data['operationCode'],  # Tipo de Operacion, Codigo de operacion
            'stamped': False,
            'state': state,
            'has_details': True,
            'keyvalue': movement.KeyValue,
            'charge_cif': '',
            'office_dc': extended_description_data['originOffice'],
            'image_link': None,
            'image_content': None,
        })

    # TODO use type-safe approach
    # we use basic_get_check_collections_to_process: here we have check_collections of only one check
    # in this case they are interchangeable. the function is only keyvalue based
    return scraper.basic_get_check_collections_to_process(checks_parsed)
