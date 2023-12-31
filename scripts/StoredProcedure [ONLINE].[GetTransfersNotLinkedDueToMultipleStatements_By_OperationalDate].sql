USE [tesoralia]
GO
/****** Object:  StoredProcedure [ONLINE].[GetTransfersNotLinkedDueToMultipleStatements]    Script Date: 22/02/2021 9:51:46 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		JFM
-- Create date: 22/02/2021
-- Description:	Obtener las transferencias marcadas como 'Multiple vinculacion' que no han sido vinculadas
-- =============================================
CREATE PROCEDURE [ONLINE].[GetTransfersNotLinkedDueToMultipleStatements_By_OperationalDate]
AS
BEGIN
    SELECT
        COUNT(*) AS FILAS, 
        TS.AccountId, 
        TA.FinancialEntityAccountId, 
        CONVERT(VARCHAR, TS.OperationalDate, 103) AS OperationalDate, 
        TS.Amount
    FROM
        [lportal].[dbo].[_TesoraliaTransferStatement] TS
    INNER JOIN [lportal].[dbo].[_TesoraliaAccounts] TA on TS.AccountId = TA.Id
    WHERE
            TS.IdStatement = 'Multiple vinculacion'
    GROUP BY
        TS.AccountId, TA.FinancialEntityAccountId, TS.OperationalDate, TS.Amount
    HAVING COUNT(*) > 1  
END


