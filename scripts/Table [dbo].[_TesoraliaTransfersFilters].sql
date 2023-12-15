USE [lportal]
GO

/****** Object:  Table [dbo].[_TesoraliaTransfersFilters]    Script Date: 03/12/2020 8:31:55 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[_TesoraliaTransfersFilters](
	[Id] [int] IDENTITY(1,1) NOT NULL,
	[AccountId] [int] NOT NULL,
	[BankCode] [nvarchar](50) NULL,
	[NavigationType] [nvarchar](50) NULL,
	[OriginField] [nvarchar](50) NOT NULL,
	[LogicOverField] [nvarchar](50) NULL,
	[DestinyField] [nvarchar](50) NOT NULL,
	[Active] [bit] NOT NULL
) ON [PRIMARY]
GO

ALTER TABLE [dbo].[_TesoraliaTransfersFilters] ADD  CONSTRAINT [DF__TesoraliaTransfersFilters_Active]  DEFAULT ((1)) FOR [Active]
GO


