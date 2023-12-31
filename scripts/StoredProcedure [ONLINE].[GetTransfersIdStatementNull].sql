USE [tesoralia]
GO
/****** Object:  StoredProcedure [ONLINE].[GetTransfersIdStatementNull]    Script Date: 21/12/2020 10:33:57 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		JFM
-- Create date: 21/12/2020
-- Modified:    18/02/2021
-- Description:	Obtiene las transferencias para un cliente y una entidad que no tienen IdStatement asignado para una fecha determinada 
-- =============================================
ALTER PROCEDURE [ONLINE].[GetTransfersIdStatementNull] @CustomerId int, @Entity nvarchar(50), @DateFrom date = NULL
	
AS
BEGIN

	SET NOCOUNT ON;
	SELECT * 
	FROM lportal.dbo._TesoraliaTransferStatement
	WHERE 
		CustomerId = @CustomerId
		AND	Entity = @Entity
		AND (IdStatement IS NULL 
			 OR ISNUMERIC(IdStatement) != 1) 
		AND (@DateFrom IS NULL
			 OR CONVERT(DATE, OperationalDate) >= @DateFrom)
END
