USE [lportal]
GO

/****** Object:  Table [dbo].[_TesoraliaInstrumentsConfig]    Script Date: 30/11/2020 14:59:18 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[_TesoraliaInstrumentsConfig](
	[AccountId] [int] NOT NULL,
	[Id] [int] IDENTITY(1,1) NOT NULL,
	[ScrapeTransfers] [bit] NOT NULL,
	[LastScrapedTransfersTimeStamp] [datetime] NULL,
	[OffsetDays] [smallint] NOT NULL
) ON [PRIMARY]
GO

ALTER TABLE [dbo].[_TesoraliaInstrumentsConfig] ADD  CONSTRAINT [DF__TesoraliaInstrumentsConfig_ScrapeTransfers]  DEFAULT ((0)) FOR [ScrapeTransfers]
GO

ALTER TABLE [dbo].[_TesoraliaInstrumentsConfig] ADD  CONSTRAINT [DF__TesoraliaInstrumentsConfig_OffsetDays]  DEFAULT ((0)) FOR [OffsetDays]
GO


