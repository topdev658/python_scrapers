USE [tesoralia]
GO
/****** Object:  StoredProcedure [ONLINE].[GetTransfersIdsNotLinkedDueToMultipleStatements]    Script Date: 18/01/2021 19:04:35 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		JFM
-- Create date: 18/02/2021
-- Description:	Obtenerlas los identificadores transferencias marcadas como 'Vinculación múltiple' que no han sido vinculadas para una cuenta,  importe y fecha concretos
-- =============================================
ALTER PROCEDURE [ONLINE].[GetTransfersIdsNotLinkedDueToMultipleStatements] 
@AccountId bigint, 
@OperationalDate AS datetime = NULL, 
@ValueDate AS datetime = NULL, 
@Amount float 

AS
BEGIN
	SET NOCOUNT ON;


	IF (@OperationalDate IS NULL)
	BEGIN

		SELECT 
			Id
		FROM 
			[lportal].[dbo].[_TesoraliaTransferStatement]  
		WHERE 
			IdStatement = 'Multiple vinculacion' 
			AND ValueDate = @ValueDate
			AND AccountId = @AccountId
			AND Amount = @Amount		 
	END;

	IF (NOT @OperationalDate IS NULL)
	BEGIN

		SELECT 
			Id
		FROM 
			[lportal].[dbo].[_TesoraliaTransferStatement]  
		WHERE 
			IdStatement = 'Multiple vinculacion' 
			AND OperationalDate = @OperationalDate
			AND AccountId = @AccountId
			AND Amount = @Amount	

	END;
END


