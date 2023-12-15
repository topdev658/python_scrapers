USE [tesoralia]
GO
/****** Object:  StoredProcedure [ONLINE].[SetTransferIdStatement]    Script Date: 20/01/2021 10:01:42 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		JFM
-- Create date: 19/01/2021
-- Description:	Actualiza la vinculación a movimiento de la transferencia cuyo id se recibe por parámetro
-- =============================================
ALTER PROCEDURE [ONLINE].[SetTransferIdStatement]  
	@TransferId bigint, 
	@IdStatement varchar(50),
	@NotLinkedReason varchar(200) = NULL
AS
BEGIN

	SET NOCOUNT ON;

	UPDATE [lportal].[dbo].[_TesoraliaTransferStatement]
	SET IdStatement = @IdStatement, 
		NotLinkedReason = @NotLinkedReason,
		UpdateIdStatementDate=GETDATE()
	WHERE Id = @TransferId

END
