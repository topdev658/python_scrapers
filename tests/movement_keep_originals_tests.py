import unittest
from typing import List

from project.custom_types import MovementScraped, MovementSaved
from scrapers._basic_scraper import movement_helpers


__version__ = '2.0.0'
__changelog__ = """
2.0.0
InitialId support
"""


class MovKeepOriginalsTestCase(unittest.TestCase):
    """Test CreateTimeStamp, InitialId filled from movements_saved"""
    movs_scraped = []  # type: List[MovementScraped]
    movs_saved = []  # type: List[MovementSaved]

    @classmethod
    def setUpClass(cls) -> None:
        cls.movs_scraped = [
            MovementScraped(Amount=-18.9, TempBalance=23308.32, OperationalDate='20191216', ValueDate='20191215',
                            StatementDescription='INTERESES-COMISIONES-GASTOS',
                            StatementExtendedDescription='INTERESES-COMISIONES-GASTOS', OperationalDatePosition=1,
                            KeyValue='2133e660730269001cd41483833443558ce0c4d0511ab74da5f55201d608b226',
                            StatementReceiptDescription='', StatementReference1='', StatementReference2='',
                            Bankoffice='', Payer='', CreateTimeStamp=None, InitialId=None),
            MovementScraped(Amount=0.5, TempBalance=23308.82, OperationalDate='20191219', ValueDate='20190129',
                            StatementDescription='COM. EMI. Y MANT T. PREPAG 5525480001167740 DEVOLUCION',
                            StatementExtendedDescription='COM. EMI. Y MANT T. PREPAG 5525480001167740 DEVOLUCION',
                            OperationalDatePosition=1,
                            KeyValue='39ee642c8f5ffbcfb3726fb413c4d8f81f42cbd39fc75b25e4ffa35799ab24a9',
                            StatementReceiptDescription='', StatementReference1='', StatementReference2='',
                            Bankoffice='', Payer='', CreateTimeStamp=None, InitialId=None),
            MovementScraped(Amount=108564.52, TempBalance=131873.34, OperationalDate='20191219', ValueDate='20191220',
                            StatementDescription='ORDEN PA RECIBIDA EN EUROS LIQ. OP. Nº 000303644410001',
                            StatementExtendedDescription='ORDEN PA RECIBIDA EN EUROS LIQ. OP. Nº 000303644410001',
                            OperationalDatePosition=2,
                            KeyValue='4b85a60254a1cdccaa11283850256cbedfb996070f52a4c3809f5bf5d4dc74da',
                            StatementReceiptDescription='', StatementReference1='', StatementReference2='',
                            Bankoffice='', Payer='', CreateTimeStamp=None, InitialId=None),
            MovementScraped(Amount=-110000.0, TempBalance=21873.34, OperationalDate='20191219', ValueDate='20191219',
                            StatementDescription='TRASPASOS TRASPASO ENTRE CUENTAS',
                            StatementExtendedDescription='TRASPASOS TRASPASO ENTRE CUENTAS', OperationalDatePosition=3,
                            KeyValue='88df19188a5aab0bf30e20549b2e904930ba938350fb3d19a516277bc2244744',
                            StatementReceiptDescription='', StatementReference1='', StatementReference2='',
                            Bankoffice='', Payer='', CreateTimeStamp=None, InitialId=None)
        ]

        cls.movs_saved = [
            MovementSaved(Id=5563556, Amount=-18.9, TempBalance=23308.32, OperationalDate='20191216',
                          ValueDate='20191215', StatementDescription='INTERESES-COMISIONES-GASTOS',
                          OperationalDatePosition=1,
                          KeyValue='2133e660730269001cd41483833443558ce0c4d0511ab74da5f55201d608b226',
                          CreateTimeStamp='20191219 11:40:00.033', InitialId=1),
            MovementSaved(Id=5563557, Amount=0.6, TempBalance=23308.92, OperationalDate='20191219',
                          ValueDate='20190129',
                          StatementDescription='COM. EMI. Y MANT T. PREPAG 5525480001167740 DEVOLUCION',
                          OperationalDatePosition=1,
                          KeyValue='71a40f740a9188210a41177a9834542828126bab5e8d7f1b44e6027b55cbb684',
                          CreateTimeStamp='20191219 11:40:00.033', InitialId=2),
            MovementSaved(Id=5563558, Amount=108564.42, TempBalance=131873.34, OperationalDate='20191219',
                          ValueDate='20191220',
                          StatementDescription='ORDEN PA RECIBIDA EN EUROS LIQ. OP. Nº 000303644410001',
                          OperationalDatePosition=2,
                          KeyValue='cf647998b010b5525ec99fcf902c7a4ecb637a6ebfed7868830beb547ee15c79',
                          CreateTimeStamp='20191219 11:40:00.033', InitialId=3),
            MovementSaved(Id=5564182, Amount=-110000.0, TempBalance=21873.34, OperationalDate='20191219',
                          ValueDate='20191219', StatementDescription='TRASPASOS TRASPASO ENTRE CUENTAS',
                          OperationalDatePosition=3,
                          KeyValue='88df19188a5aab0bf30e20549b2e904930ba938350fb3d19a516277bc2244744',
                          CreateTimeStamp='20191219 13:00:37.193', InitialId=3),
        ]

    def test_fill_originals(self):
        movs_scraped_filled_ts, movs_saved_unmatched = \
            movement_helpers.fill_originals_from_movements_saved(
                self.movs_scraped,
                self.movs_saved
            )

        self.assertTrue(any(m.CreateTimeStamp for m in movs_scraped_filled_ts))
        self.assertTrue(any(m.InitialId for m in movs_scraped_filled_ts))
        # Avoid mutation of init list
        self.assertFalse(any(m.CreateTimeStamp for m in self.movs_scraped))
        self.assertEqual(len(movs_saved_unmatched), 2)
