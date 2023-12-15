--- ===================
--- ===================
--- ===================

-- STAGE 1
-- QUERY TO DELETE DUPL FOR OLD RECEIPTS OF SABADELL
-- LOGIC:
-- DELETE OLD DOC ONLY IF THE NEW DOC PROVIDES ALL DETAILS
DECLARE @last_id BIGINT = 0;
DECLARE @id BIGINT = 0;
DECLARE @product_id VARCHAR(50);
DECLARE @document_date DATETIME;
DECLARE @amount DECIMAL(18, 2);
DECLARE @checksum CHAR(256);
DECLARE @customer_id BIGINT;
DECLARE @fin_ent_id BIGINT;

DECLARE @id2 BIGINT;
DECLARE @statement_id2 BIGINT;
DECLARE @account_id2 BIGINT;

DECLARE @iter_ix INT = 0; -- limit number of iterations per run
-- WHILE WE HAVE MORE RECEIPTS AND STEPS
WHILE (@id<>-1  AND @iter_ix < 230)
    BEGIN
        SET @id=-1;
        SET @iter_ix += 1;
        -- LOOK FOR OLD RECEIPT
        SELECT TOP 1 @checksum=Checksum, @id=Id, @product_id=ProductId, @document_date=DocumentDate, @amount=Amount,
                     @customer_id=CustomerId, @fin_ent_id=FinancialEntityId
        FROM _TesoraliaDocuments
        WHERE DocumentType='<RECEIPT>'
          AND Id > @last_id
        ORDER BY Id;
        IF (@id=-1)
            PRINT 'NO MORE DOCUMENTS'
        ELSE
            SET @last_id = @id;
        -- LOOK FOR DUPLICATE AND PROCESS ORIG
        SELECT TOP 1 @id2=Id, @statement_id2=StatementId, @account_id2=AccountId
        FROM _TesoraliaDocuments
        WHERE DocumentType='RECEIPT'
          AND ProductId=@product_id
          AND Checksum=@checksum
          AND DocumentDate=@document_date
          AND Amount=@amount
          AND CustomerId=@customer_id
          AND FinancialEntityId=@fin_ent_id

        IF (@statement_id2 IS NOT NULL AND @account_id2 IS NOT NULL)
            BEGIN
                PRINT ('DELETE ' + CAST(@id AS NVARCHAR(10)) + '  KEEP ' + CAST(@id2 AS NVARCHAR(10)) + ' (' + LEFT(@checksum, 10) + '...)');
                DELETE FROM _TesoraliaDocuments WHERE Id=@id;
            END
    END;

--- ===================
--- ===================
--- ===================

