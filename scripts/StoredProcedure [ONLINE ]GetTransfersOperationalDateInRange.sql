USE [tesoralia]
GO
/****** Object:  StoredProcedure [ONLINE].[GetTransfersOperationalDateInRange]    Script Date: 16/03/2021 12:03:55 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		JFM
-- Create date: 15/03/2021
-- Description:	Obtener todas las transferencias insertadas para una cuenta en un rango de fechas
-- =============================================
ALTER PROCEDURE [ONLINE].[GetTransfersOperationalDateInRange]
@AccountId bigint,
@FromOperationalDate AS datetime,
@ToOperationalDate AS datetime

AS
BEGIN

	SET NOCOUNT ON;

	SELECT *
	FROM [lportal].[dbo]._TesoraliaTransferStatement
	WHERE
		AccountId = @AccountId
		AND OperationalDate BETWEEN @FromOperationalDate AND @ToOperationalDate
END
