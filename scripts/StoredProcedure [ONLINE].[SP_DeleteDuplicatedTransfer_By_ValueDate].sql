USE [tesoralia]
GO

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO


-- =============================================
-- Author:		BRG
-- Create date: 19/01/2021
-- Description:	Elimina todos los duplicados de la tabla basándose en el ValueDate
-- =============================================
CREATE PROCEDURE [ONLINE].[SP_DeleteDuplicatedTransfer_By_ValueDate] @ParamCustomerId int, @ParamEntity nvarchar(50)
	
AS
BEGIN
	
	SET NOCOUNT ON;
	
	DECLARE @NumMovimientos AS INT
	DECLARE @NumTransferencias AS INT
	DECLARE @Filas AS INT
	DECLARE @AccountId AS VARCHAR (20)
	DECLARE @ValueDate AS VARCHAR (20)
	DECLARE @Amount AS VARCHAR (200)
	DECLARE @NameOrder AS VARCHAR (200)
	DECLARE @Concept AS VARCHAR (200)
	DECLARE @Reference AS VARCHAR (200)
	DECLARE @Description AS VARCHAR (200)
	DECLARE @Obrservation AS VARCHAR (200)
	DECLARE @CustomerId AS INT
	DECLARE @Entity AS VARCHAR (200)

	DECLARE cs CURSOR FOR 
		-- Obtener Transferencias duplicadas (Sin tener en cuenta si han sido vinculadas)
		SELECT COUNT(*) AS FILAS, AccountId, CONVERT(varchar, ValueDate, 103), Amount, NameOrder, Concept, Reference, [Description], Obrservation, CustomerId, Entity
		FROM [lportal].[dbo].[_TesoraliaTransferStatement]
		WHERE CustomerId = @ParamCustomerId
			AND Entity = @ParamEntity
		GROUP BY AccountId, CONVERT(varchar, ValueDate, 103), Amount, NameOrder, Concept, Reference, [Description], Obrservation, CustomerId, Entity  
		HAVING COUNT(*) > 1  
		ORDER BY COUNT(*) DESC 
	
		OPEN cs
		FETCH NEXT FROM cs INTO @Filas, @AccountId, @ValueDate, @Amount, @NameOrder, @Concept, @Reference, @Description, @Obrservation, @CustomerId, @Entity  
		WHILE @@fetch_status = 0
		BEGIN
	
			--PRINT '@AccountId -> ' + @AccountId
			--PRINT '@ValueDate -> ' + @ValueDate
			--PRINT '@Amount -> ' + @Amount
			--PRINT '@NameOrder -> ' + @NameOrder
			--PRINT '@Concept -> ' + @Concept
			--PRINT '@Reference -> ' + @Reference
			--PRINT '@Description -> ' + @Description
			--PRINT '@Obrservation -> ' + @Obrservation
			--PRINT '@CustomerId -> ' + @CustomerId
			--PRINT '@Entity -> ' + @Entity

			SET @NumMovimientos = (
				SELECT COUNT(*)
				FROM [lportal].[dbo].[_TesoraliaStatements] 
				WHERE 
					AccountId = @AccountId
					AND ValueDate = @ValueDate
					AND Amount = @Amount
				)

			IF (@NumMovimientos <> @Filas)
			BEGIN
				SET @NumTransferencias = @Filas - 1 

				--Borrar la Transferencia duplicada que no ha sido vinculada		
				DELETE FROM [lportal].[dbo].[_TesoraliaTransferStatement] 
				WHERE Id IN (
					SELECT TOP (@NumTransferencias) Id FROM [lportal].[dbo].[_TesoraliaTransferStatement] 
					WHERE AccountId = @AccountId
						AND ValueDate = @ValueDate 
						AND Amount = @Amount
						AND NameOrder = @NameOrder
						AND Concept = @Concept
						AND Reference = @Reference
						AND [Description] = @Description
						AND Obrservation = @Obrservation
						AND (IdStatement IS NULL OR ISNUMERIC(IdStatement) <> 1)
						ORDER BY IdStatement
					)
			END

		
			FETCH NEXT FROM cs INTO @Filas, @AccountId, @ValueDate, @Amount, @NameOrder, @Concept, @Reference, @Description, @Obrservation, @CustomerId, @Entity
		END
		CLOSE cs
		DEALLOCATE cs	
END