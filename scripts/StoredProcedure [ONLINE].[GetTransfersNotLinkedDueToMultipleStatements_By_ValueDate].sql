USE [tesoralia]
GO
/****** Object:  StoredProcedure [ONLINE].[GetTransfersNotLinkedDueToMultipleStatements]    Script Date: 16/02/2021 16:13:49 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		JFM
-- Create date: 18/02/2021
-- Description:	Obtener las transferencias marcadas como 'Multiple vinculacion' que no han sido vinculadas
-- =============================================
CREATE PROCEDURE [ONLINE].[GetTransfersNotLinkedDueToMultipleStatements_By_ValueDate]
AS
BEGIN
	SET NOCOUNT ON;

	SELECT 
		COUNT(*) AS FILAS, AccountId, CONVERT(VARCHAR, ValueDate, 103) AS ValueDate, Amount
	FROM 
		[lportal].[dbo].[_TesoraliaTransferStatement]  
	WHERE 
		IdStatement = 'Multiple vinculacion'
	GROUP BY 
		AccountId, ValueDate, Amount
	HAVING COUNT(*)  > 1  
END


