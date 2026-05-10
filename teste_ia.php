<?php

// ==========================
// CONEXÃO COM O BANCO
// ==========================
$host = 'sql201.infinityfree.com';
$usuario = 'if0_39007414';
$senha = 'SibfxkGyuneA6';
$banco = 'if0_39007414_bdcontroleestoque';

$conn = new mysqli($host, $usuario, $senha, $banco);

if ($conn->connect_error) {
    die("Erro de conexão: " . $conn->connect_error);
}

// ==========================
// URL DA API NO RAILWAY
// ==========================
$url = "https://api-estoque-ia-production.up.railway.app/prever";

// ==========================
// ARRAY PARA EXPORTAÇÃO
// ==========================
$relatorio_repor = [];

// ==========================
// FUNÇÃO PARA GERAR DADOS
// ==========================
function gerarRelatorio($conn, &$relatorio_repor) {

    $sql_produtos = "SELECT id_produto, nome_produto, qtde_estoque FROM produtos";
    $result_produtos = $conn->query($sql_produtos);

    if (!$result_produtos) {
        die("Erro na query produtos: " . $conn->error);
    }

    $linhas = [];

    while ($produto = $result_produtos->fetch_assoc()) {

        $id_produto = $produto["id_produto"];
        $nome = $produto["nome_produto"];
        $estoque = $produto["qtde_estoque"];

        $sql_vendas = "
            SELECT 
            SUM(iv.quantidade) as total_vendido,
            DATE_SUB(CURDATE(), INTERVAL 12 MONTH) AS data_inicio,
			CURDATE() AS data_fim
    
            FROM itens_venda iv
            JOIN vendas v ON iv.id_venda = v.id_venda
            WHERE iv.id_produto = $id_produto
            AND v.data_venda >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
        ";

        $result_vendas = $conn->query($sql_vendas);

        if (!$result_vendas) {
            die("Erro na query vendas: " . $conn->error);
        }

        $row = $result_vendas->fetch_assoc();

        $total_vendido = $row["total_vendido"] ?? 0;
        $data_inicio = $row["data_inicio"] ?? "-";
        $data_fim = $row["data_fim"] ?? "-";

        // formatar datas
        if ($data_inicio != "-") {
            $data_inicio = date("d/m/Y", strtotime($data_inicio));
            $data_fim = date("d/m/Y", strtotime($data_fim));
        }

        // previsão simples (média mensal dos ultimos 12 meses)
        $previsao = round($total_vendido / 12);

        $repor = $previsao - $estoque;
        if ($repor < 0) {
            $repor = 0;
        }

        if ($repor > 0) {
            $relatorio_repor[] = [
                "produto" => $nome,
                "estoque" => $estoque,
                "previsao" => $previsao,
                "repor" => $repor
            ];
        }

        $linhas[] = [
            "nome" => $nome,
            "estoque" => $estoque,
            "vendido" => $total_vendido,
            "periodo" => $data_inicio . " até " . $data_fim,
            "previsao" => $previsao,
            "repor" => $repor
        ];
    }

    return $linhas;
}
// ==========================
// GERAR DADOS
// ==========================
$linhas = gerarRelatorio($conn, $relatorio_repor);

// ==========================
// DOWNLOAD CSV (ANTES DO HTML)
// ==========================
if (isset($_GET['baixar'])) {

    header('Content-Type: text/csv');
    header('Content-Disposition: attachment; filename="relatorio_reposicao.csv"');

    $output = fopen("php://output", "w");

    fputcsv($output, ["Produto", "Estoque Atual", "Previsão", "Repor"]);

    foreach ($relatorio_repor as $item) {
        fputcsv($output, [
            $item["produto"],
            $item["estoque"],
            $item["previsao"],
            $item["repor"]
        ]);
    }

    fclose($output);
    exit;
}
                // Codigo para buscar no banco por data inicial e final com vendas registradas(subtituir no código sql) 
				//MIN(v.data_venda) as data_inicio, 
                //MAX(v.data_venda) as data_fim
?>

<!DOCTYPE html>
<html>
<head>
    <title>Previsão de Estoque</title>
    <style>
        body { font-family: Arial; }
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th {
            background-color: #333;
            color: white;
        }
        td, th {
            padding: 10px;
            text-align: center;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        .btn {
            padding:10px 15px;
            color:white;
            text-decoration:none;
            border-radius:5px;
            margin-right:10px;
        }
        .voltar { background-color:#333; }
        .download { background-color:green; }
        .alerta { color:red; font-weight:bold; }
        .ok { color:green; }
    </style>
</head>
<body>

<!-- BOTÕES -->
<a href="index.php" class="btn voltar">⬅ Voltar ao Menu</a>
<a href="relatorio_impressao.php?data_inicio=2025-01-01&data_fim=2025-06-30" target="_blank">
    <button>Imprimir Relatório</button>
</a>

<h2>📊 Previsão Inteligente de Estoque</h2>

<table>
<tr>
    <th>Produto</th>
	<th>Estoque</th>
	<th>Vendido (12 meses)</th>
	<th>Período Considerado</th>
	<th>Previsão</th>
	<th>Repor</th>
</tr>

<?php foreach ($linhas as $linha): ?>
<tr>
    <td><?php echo $linha["nome"]; ?></td>
	<td><?php echo $linha["estoque"]; ?></td>
	<td><?php echo $linha["vendido"]; ?></td>
	<td><?php echo $linha["periodo"]; ?></td>
	<td><?php echo $linha["previsao"]; ?></td>

<?php if ($linha["repor"] > 0): ?>
  	  	<td class="alerta"><?php echo $linha["repor"]; ?></td>
<?php else: ?>
   		 <td class="ok">OK</td>
<?php endif; ?>
</tr>
<?php endforeach; ?>

</table>

</body>
</html>