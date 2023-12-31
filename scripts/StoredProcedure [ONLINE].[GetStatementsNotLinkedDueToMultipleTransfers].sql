USE [tesoralia]
GO
/****** Object:  StoredProcedure [ONLINE].[GetStatementsNotLinkedDueToMultipleTransfers]    Script Date: 18/01/2021 16:58:44 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		JFM
-- Create date: 18/02/2021
-- Description:	Obtener los movimientos que deben ser vinculados a 
-- Transferencias marcadas como 'Multiple vinculacion' usando 
-- OperationalDate o ValueDate en función de los parámetros de entrada
--
-- =============================================
CREATE PROCEDURE [ONLINE].[GetStatementsNotLinkedDueToMultipleTransfers]
@AccountId bigint, 
@OperationalDate AS datetime = NULL, 
@ValueDate AS datetime = NULL, 
@Amount float 
	
AS
BEGIN

	SET NOCOUNT ON;

	IF (@OperationalDate IS NULL)
	BEGIN

		SELECT InitialId
		FROM [lportal].[dbo]._TesoraliaStatements
		WHERE 
			ValueDate = @ValueDate
			AND AccountId = @AccountId
			AND Amount = @Amount		
			AND CONVERT(varchar,InitialId) NOT IN 
				(SELECT IdStatement FROM lportal.dbo._TesoraliaTransferStatement
					WHERE
						AccountId = @AccountId
						AND	ValueDate = @ValueDate
						AND Amount = @Amount
						AND IdStatement IS NOT NULL
						AND ISNUMERIC(IdStatement) = 1
				)	 
	END;

	IF (NOT @OperationalDate IS NULL)
		BEGIN

			SELECT InitialId
			FROM [lportal].[dbo]._TesoraliaStatements
			WHERE 
				OperationalDate = @OperationalDate
				AND AccountId = @AccountId
				AND Amount = @Amount
				AND CONVERT(varchar,InitialId) NOT IN 
					(SELECT IdStatement FROM lportal.dbo._TesoraliaTransferStatement
						WHERE
							AccountId = @AccountId
							AND	OperationalDate = @OperationalDate
							AND Amount = @Amount
							AND IdStatement IS NOT NULL
							AND ISNUMERIC(IdStatement) = 1
					)

	END;
END

