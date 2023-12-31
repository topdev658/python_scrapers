USE [tesoralia]
GO
/****** Object:  StoredProcedure [ONLINE].[GetActiveTransfersAccounts]    Script Date: 30/11/2020 14:56:59 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		BRG
-- Create date: 25/11/2020
-- Description:	Obtiene las cuentas activas que están marcadas para obtener la información de Transferencias
-- =============================================
CREATE PROCEDURE [ONLINE].[GetActiveTransfersAccounts] @CustomerFinancialEntityAccessId int
	
AS
BEGIN

	SET NOCOUNT ON;

    SELECT INST.AccountId, ACC.FinancialEntityAccountId , ACC.CustomerFinancialEntityAccessId, INST.LastScrapedTransfersTimeStamp - INST.OffsetDays as LastScrapedTransfersTimeStamp
	FROM 
		   [lportal].[dbo].[_TesoraliaInstrumentsConfig] AS INST INNER JOIN [lportal].[dbo]._TesoraliaAccounts AS ACC
		   ON INST.AccountId = ACC.Id
	WHERE
		   INST.ScrapeTransfers = 1
		   AND
		   ACC.Active = 1
		   AND
		   @CustomerFinancialEntityAccessId = ACC.CustomerFinancialEntityAccessId
END
