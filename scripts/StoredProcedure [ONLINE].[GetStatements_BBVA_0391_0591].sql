USE [tesoralia]
GO
/****** Object:  StoredProcedure [ONLINE].[GetStatements_0391_0591]    Script Date: 22/12/2020 11:48:18 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		BRG
-- Create date: 22/12/2020
-- Description:	Obtener los Movimientos con código 0391 y 0591 de AVIA que deben convertirse en Transferencias
-- =============================================
CREATE PROCEDURE [ONLINE].[GetStatements_BBVA_0391_0591]	
AS
BEGIN
	SET NOCOUNT ON;

		SELECT CONVERT(varchar, OperationalDate, 112) AS OperationalDate, CONVERT(varchar, ValueDate, 112) AS ValueDate, Amount, AccountId, StatementExtendedDescription, InitialId
		FROM [lportal].[dbo].[_TesoraliaStatements]
		WHERE AccountId IN 
				(SELECT Id
				FROM [lportal].[dbo].[_TesoraliaAccounts]
				WHERE CustomerId = 239949
				AND Active = 1
				AND AccountNo LIKE 'ES__0182%') --> TODAS LAS CUENTAS BBVA
				AND (StatementExtendedDescription LIKE '%Código: 0391%' OR StatementExtendedDescription LIKE '%Código: 0591%')
				AND (CONVERT(VARCHAR,InitialId) NOT IN
						(
						SELECT IdStatement FROM [lportal].[dbo]._TesoraliaTransferStatement
						WHERE IdStatement IS NOT NULL
						) 
					) 
END


