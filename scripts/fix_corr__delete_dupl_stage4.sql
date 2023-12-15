--- ///////////////////
--- ///////////////////
--- ///////////////////

-- STAGE 4
-- QUERY TO DELETE DUPL FOR OLD RECEIPTS OF BANKINTER and OTHERS
-- LOGIC:
-- FIND RECEIPTS (* with AccountId IS NULL AND StatementId is NULL *) and delete others
-- found by ProductId LIKE product_id[-9:]
DECLARE @id BIGINT;
DECLARE @product_id VARCHAR(50);
DECLARE @document_date DATETIME;
DECLARE @checksum CHAR(256) = '';
DECLARE @customer_id BIGINT;
DECLARE @fin_ent_id BIGINT;
DECLARE @org_id BIGINT;
DECLARE @ids_to_delete_str VARCHAR(MAX);
DECLARE @iter_ix INT = 0;
DECLARE @processed_checksums TABLE (Checksum CHAR(256));


SELECT Checksum, ProductId INTO #duplicates
FROM [lportal].[dbo].[_TesoraliaDocuments]
-- WHERE FinancialEntityId IN (202) -- (302 Bankia, 202 Bankinter, 1104 Liberbank, 1 BBVA, 102 Sabadell, 201 Santander, 103 Caixa)
-- 1402 LABORAL_KUTXA, 1101 CAJA_RURAL,
GROUP BY CustomerId, Checksum, ProductId, FinancialEntityId, DocumentDate
HAVING COUNT(*) > 1;

WHILE (@iter_ix < 1000 AND @checksum <> '-')
    BEGIN
        SET @id = -1;
        SET @checksum = '-';
        -- Peek top checksum
        SELECT TOP 1 @checksum=Checksum, @product_id=ProductId
        FROM #duplicates
        WHERE Checksum NOT IN (SELECT Checksum FROM @processed_checksums);
        IF (@checksum = '-')
            PRINT ('== ALL DUPLICATES WERE PROCESSED ==')
        ELSE
            BEGIN
                -- Update @processed_checksums
                INSERT INTO @processed_checksums (Checksum) VALUES (@checksum);

                -- Peek 1st doc for this Checksum, look only for doc with StatementId
                SELECT TOP 1 @id=Id, @document_date=DocumentDate,
                             @customer_id=CustomerId, @fin_ent_id=FinancialEntityId, @org_id=OrganizationId
                FROM _TesoraliaDocuments
                WHERE Checksum=@checksum
                  AND ProductId LIKE '%' + RIGHT(@product_id, 9)
                  AND AccountId IS NULL -- NO ACCOUNT ID
                  AND StatementId IS NULL -- NO STATEMENT ID
                ORDER BY Id;
                IF (@id=-1)
                    PRINT ('NOT DUPL WITHOUT AccountId and StatementId FOR ' + @product_id + ' with ' + LEFT(@checksum, 10) + '...')
                ELSE
                    BEGIN
                        SET @iter_ix += 1; -- count iters when found AccountId
                        -- DETECT DUPLICATES:
                        -- All should be the same except StatementId
                        -- (correspondence sometimes can't detect StatementId while receipt can)
                        -- also ProductId is matching by LIKE
                        SELECT Id INTO #ids_to_delete
                        FROM _TesoraliaDocuments
                        WHERE Checksum=@checksum
                          AND DocumentDate=@document_date
                          AND ProductId LIKE '%' + RIGHT(@product_id, 9)
                          AND CustomerId=@customer_id
                          AND FinancialEntityId=@fin_ent_id
                          AND OrganizationId=@org_id
                          AND Id <> @id;
                        -- DELETE DUPLICATES
                        SET @ids_to_delete_str = '';
                        SELECT
                                @ids_to_delete_str = COALESCE(@ids_to_delete_str + ' ', '') + CAST(Id AS NVARCHAR(10))
                        FROM #ids_to_delete;
                        IF (@ids_to_delete_str <> ' ')
                            BEGIN
                                PRINT ('DELETE ' + @ids_to_delete_str + '   KEEP ' + CAST(@id AS NVARCHAR(10)) + ' (' + LEFT(@checksum, 10) + '...)');
                                DELETE FROM _TesoraliaDocuments WHERE Id IN (SELECT Id FROM #ids_to_delete);
                            END
                        ELSE
                            PRINT ('NO DUPL FOR ' + CAST(@id AS NVARCHAR(10)) + ' (' + LEFT(@checksum, 10) + '...)');
                        DROP TABLE #ids_to_delete;
                    END
            END
    END;
DROP TABLE #duplicates;

--- ///////////////////
--- ///////////////////
--- ///////////////////
