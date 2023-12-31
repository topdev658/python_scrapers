USE [tesoralia]
GO
/****** Object:  StoredProcedure [ONLINE].[GetTransfersNotLinkedDueToMultipleStatements]    Script Date: 18/01/2021 19:04:35 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		BRG
-- Create date: 18/01/2021
-- Description:	Obtener las transferencias marcadas como 'Multiple vinculacion' que no han sido vinculadas
-- =============================================
CREATE PROCEDURE [ONLINE].[GetTransfersNotLinkedDueToMultipleStatements]
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


