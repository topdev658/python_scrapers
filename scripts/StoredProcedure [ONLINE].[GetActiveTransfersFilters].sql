USE [tesoralia]
GO
/****** Object:  StoredProcedure [ONLINE].[GetActiveTransfersFilters]    Script Date: 13/12/2020 20:07:42 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		JFM
-- Create date: 30/11/2020
-- Description:	Obtiene los filtros activos para aplicar a la información de transferencias extraída de la banca 
-- =============================================
CREATE PROCEDURE [ONLINE].[GetActiveTransfersFilters] @AccountId int, @NavigationType nvarchar(50) 
	
AS
BEGIN

	SET NOCOUNT ON;

    SELECT AccountId, BankCode, NavigationType, OriginField, LogicOverField, DestinyField, Active
	FROM 
		   [lportal].[dbo].[_TesoraliaTransfersFilters]
	WHERE
		Active = 1
		AND
		AccountId = @AccountId
		AND
		NavigationType = @NavigationType
END
