# src/database/queries.py
from typing import Optional, List

class BorderoQueries:
    @staticmethod
    def get_titulos_query(borderos: Optional[List[str]] = None, carteira_id: Optional[int] = None) -> str:
        return """
        WITH Titulos AS (
            SELECT 
                '1' AS Tipo_Registro,
                'INCL' AS Inclusao,
                tit.[ctrl_id] AS Id,
                tit.Carteira_ID,
                cart.Nome AS Carteira,
                'DIRETA CAPITAL FIDC' AS Razao_Titular,
                '51030944000142' AS CNPJ_Titular,
                '' AS Conta_do_Titular,
                '' AS Meu_Numero,
                '' AS Manutencao,
                '2' AS Tipo_Regime,
                ced.CGC AS CNPJ_Credor,
                UPPER(ced.NOME) AS Razao_Credor,
                ced.ESTADO AS UF,
                UPPER(ced.CIDADE) AS CIDADE,
                sac.CGC AS CNPJ_Devedor,
                UPPER(sac.NOME) AS Razao_Devedor,
                'Boleto' AS Pagamento,
                'DC' AS Tipo_IF,
                'INCL' AS Acao,
                '' AS Codigo_IF,
                '' AS Vencimento_Atualizada,
                '58561405' AS Conta_Escriturador,
                '' AS Data_Valor_Atualizado,
                CASE tit.tipodcto
                    WHEN 'DM' THEN '02'
                    WHEN 'DS' THEN '05'
                    ELSE 'XX'
                END AS Especie_Titulo,
                tit.[BORDERO] AS Numero_Bordero,
                        
                tit.[ModoDeCobranca_ID] AS Cobranca_Id,

                CASE WHEN tit.[ModoDeCobranca_ID] = 35 THEN 1
                ELSE 0 END AS Is_Monkey,

				CASE WHEN gs.idgrupo = 24 THEN 1
				ELSE 0 END AS Is_CasasBahia,

                tit.[DCTO] AS Numero_Titulo,

                TRIM(tit.controleparticipante) AS Controle_Interno,

                CASE
					-- tratamento títulos casa bahia, extrapolam os 10 dígitos do número de documento
					WHEN gs.idgrupo = 24 THEN
						CASE
							WHEN LEN(TRIM(tit.[DCTO])) > 10 THEN TRIM(tit.NOTAFISCAL)
							ELSE tit.[DCTO]
						END
                    -- há / ou -  → pega tudo antes do primeiro deles
                    WHEN CHARINDEX('/', tit.controleparticipante) > 0 OR CHARINDEX('-', tit.controleparticipante) > 0
                    THEN SUBSTRING(
                            TRIM(tit.controleparticipante),
                            1,
                            CASE
                                WHEN CHARINDEX('/', TRIM(tit.controleparticipante)) = 0 THEN CHARINDEX('-', TRIM(tit.controleparticipante)) - 1
                                WHEN CHARINDEX('-', TRIM(tit.controleparticipante)) = 0 THEN CHARINDEX('/', TRIM(tit.controleparticipante)) - 1
                                WHEN CHARINDEX('/', TRIM(tit.controleparticipante)) < CHARINDEX('-', TRIM(tit.controleparticipante))
                                    THEN CHARINDEX('/', TRIM(tit.controleparticipante)) - 1
                                ELSE CHARINDEX('-', TRIM(tit.controleparticipante)) - 1
                            END
                            )

                    -- só dígitos → pega os últimos até 10, preservando zeros à esquerda
                    WHEN TRIM(tit.controleparticipante) NOT LIKE '%[^0-9]%'
                    THEN RIGHT(TRIM(tit.controleparticipante), CASE WHEN LEN(TRIM(tit.controleparticipante)) > 10 THEN 10 ELSE LEN(TRIM(tit.controleparticipante)) END)
					
                    ELSE NULL -- opcional: casos que não se encaixam
                END AS Documento_Encontrato,

                tit.[NOTAFISCAL] AS Nota_Fiscal,
                CONVERT(VARCHAR(8), tit.[DTBORDERO], 112) AS Data_Operacao,
                CONVERT(VARCHAR(8), tit.[DATA], 112) AS Data_Vencimento,
                CAST(tit.[VALOR] AS DECIMAL(18,2)) AS Valor_Face,
                CAST(tit.[VALOR] AS DECIMAL(18,2)) AS Valor_Atualizado,
                td.descricao AS Tipo_Documento,
                CAST(tit.ValorNota AS DECIMAL(18,2)) AS Valor_nota_fiscal,
                tit.BORDERO AS Bordero,
                COALESCE(sflu.BANCO, sfidc.BANCO) AS Banco,
                CASE 
                    WHEN COALESCE(sflu.BANCO, sfidc.BANCO) IS NULL OR 
                        LTRIM(RTRIM(COALESCE(sflu.BANCO, sfidc.BANCO))) = '' 
                    THEN 'EM ABERTO' 
                    ELSE 'PAGO' 
                END AS Situacao
            FROM 
                [wba].[dbo].[SIGFLS] tit
            JOIN 
                [wba].[dbo].[SIGBORS] bor ON tit.BORDERO = bor.BORDERO
            JOIN 
                [wba].[dbo].[tipodcto] td ON tit.tipodcto = td.tipodcto
            LEFT JOIN 
                [wba].[dbo].[SIGCAD] ced ON tit.CLIFOR = ced.CODIGO
            LEFT JOIN 
                [wba].[dbo].[SIGCAD] sac ON tit.SACADO = sac.CODIGO
			LEFT JOIN
				[wba].[dbo].[GrupoEmpresa] gs ON sac.codigo = gs.clifor
            JOIN 
                [wba].[dbo].[Carteira] cart ON cart.NumeroCarteira = tit.Carteira_ID
            LEFT JOIN 
                [wba].[dbo].[SIGFLU] sflu ON tit.ctrl_id = sflu.sigfls
            LEFT JOIN 
                [wba].[dbo].[SIGFIDC] sfidc ON tit.ctrl_id = sfidc.sigfls
            WHERE 
                1=1
                -- Apenas Títulos em ABERTO podem ser registrados.
                AND (COALESCE(sflu.BANCO, sfidc.BANCO) IS NULL OR COALESCE(sflu.BANCO, sfidc.BANCO) = '  ' OR COALESCE(sflu.BANCO, sfidc.BANCO) = '')
                AND (tit.rejeitado NOT IN ('X', 'S') OR tit.rejeitado IS NULL)
                AND bor.dtliberacao IS NOT NULL
                AND td.tipodcto IN ('DM', 'DS')
                --AND tit.[ModoDeCobranca_ID] IN (35) -- Monkey
                --AND tit.Carteira_ID = 0
        ),
        Titulos_Nfe AS (
            SELECT
                a.numero,
                a.serie,
                CONVERT(VARCHAR(8), a.Data_Emissao, 112) AS Data_Emissao,
                CAST(a.valor AS DECIMAL(18,2)) AS valor,
                a.chave,
                a.Ctrl_ID
            FROM
                [wba].[dbo].[nfeimportada] a
            INNER JOIN 
                [wba].[dbo].[nfeimportadaxsigfls] b ON b.nfeimportada_id = a.ctrl_id
                
            UNION ALL
                
            SELECT
                a.numero,
                a.serie,
                CONVERT(VARCHAR(8), a.Data_Emissao, 112) AS Data_Emissao,
                CAST(a.valor AS DECIMAL(18,2)) AS valor,
                a.chave,
                a.Ctrl_ID
            FROM
                [wba].[dbo].[nfeimportada] a
            INNER JOIN 
                [wba].[dbo].[NFeImportadaXSigflsMultiplasNFes] b ON b.NFeImportada_ID = a.Ctrl_ID
        )
                
        SELECT 
            Id,
            Carteira_ID,
            Tipo_IF,
            Tipo_Registro,
            Acao,
            Codigo_IF,
            Conta_Escriturador,
            Conta_do_Titular,
            CNPJ_Titular,
            Razao_Titular,
            Meu_Numero,
            Manutencao,
            Tipo_Regime,
            CNPJ_Credor,
            Razao_Credor,
            CNPJ_Devedor,
            Razao_Devedor,
            Valor_Face,
            Valor_Atualizado,
            Data_Valor_Atualizado,
            ISNULL(Data_Emissao, Data_Operacao) AS Data_Emissao,
            Data_Vencimento,
            Vencimento_Atualizada,
            UF,
            CIDADE,
            Especie_Titulo,
            Valor_nota_fiscal,
            Data_Operacao,
            Numero_Bordero,
            Pagamento,
            Controle_Interno,
            Documento_Encontrato,

            CASE
                WHEN 
					(TRY_CAST(Numero_Titulo AS INT) IS NULL AND Is_Monkey > 0) OR 
					(LEN(TRIM(Numero_Titulo)) > 10 AND Is_CasasBahia > 0)
                THEN Documento_Encontrato
                ELSE ISNULL(Numero_Titulo, '')
            END Numero_Titulo,
                    
            CASE
                WHEN TRY_CAST(Nota_Fiscal AS INT) IS NULL  AND Is_Monkey > 0
                THEN Documento_Encontrato
                ELSE ISNULL(Nota_Fiscal, '')
            END Nota_Fiscal,

            ISNULL(Chave, '') Chave,
            Bordero,
            ISNULL(Numero, '') Numero,
            ISNULL(Serie, '') Serie,
            Tipo_Documento,
            Carteira,
            ISNULL(Banco, '') Banco,
            Situacao
        FROM 
            Titulos
        LEFT JOIN 
            Titulos_Nfe
        ON Ctrl_ID = Id

        WHERE 1=1
        {carteira_filtro}
        """.format(
                carteira_filtro=BorderoQueries.add_where_clause_carteira(carteira_id)
            ) + """
        {borderos_filtro}
        """.format(
                borderos_filtro=BorderoQueries.add_where_clause_borderos(borderos)
            )
        
    @staticmethod
    def add_where_clause_carteira(carteira_id: int) -> str:
        return f"AND Carteira_ID = {carteira_id}" if carteira_id else ""

    @staticmethod
    def add_where_clause_borderos(borderos: List[str]) -> str:
        return f"AND Bordero IN ({','.join(borderos)})"

