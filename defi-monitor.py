import time
import logging
import requests
import threading
import json
import os
from flask import Flask, render_template_string, Response

ETHERSCAN_API_KEY = 'YOUR_API_KEY_HERE'
ETHERSCAN_API_URL = 'https://api.etherscan.io/api'
THRESHOLD_ETHER = 100
FLAGGED_ADDRESSES = {
    '0x0000000000000000000000000000000000000001',
}
HIGH_GAS_GWEI = 200
POLL_INTERVAL = 2
DATA_FILE = 'suspicious_transactions.json'

suspicious_txs = []
lock = threading.Lock()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Défi Monitor</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/dataTables.bootstrap5.min.css">
    <style>
        body { padding: 2rem; background-color: #121212; color: #eee; }
        table { font-size: 0.9rem; }
        .flagged { background-color: #511; }
        .high-value { background-color: #221155; }
        .high-gas { background-color: #553311; }
        .stat { margin-right: 2rem; }
    </style>
</head>
<body>
    <h1>🔍 Défi Monitor - Transactions Suspectes</h1>
    <div class="d-flex mb-3">
        <div class="stat">💸 Total ETH: <span id="total-eth">0</span></div>
        <div class="stat">⚠️ Total suspectes: <span id="total-count">0</span></div>
        <button class="btn btn-warning btn-sm me-2" onclick="pauseStream()">⏸️ Pause</button>
        <button class="btn btn-success btn-sm" onclick="resumeStream()">▶️ Reprendre</button>
    </div>
    <table id="tx-table" class="table table-dark table-striped">
        <thead>
            <tr>
                <th>Hash</th>
                <th>Bloc</th>
                <th>From</th>
                <th>To</th>
                <th>Valeur (ETH)</th>
                <th>Gas (gwei)</th>
                <th>Raison</th>
            </tr>
        </thead>
        <tbody></tbody>
    </table>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/dataTables.bootstrap5.min.js"></script>
    <script>
        let evtSource;
        let totalETH = 0;
        let paused = false;
        $(document).ready(function() {
            $('#tx-table').DataTable();
            resumeStream();
        });
        function updateStats(val) {
            totalETH += parseFloat(val);
            $('#total-eth').text(totalETH.toFixed(2));
            let count = parseInt($('#total-count').text());
            $('#total-count').text(count + 1);
        }
        function pauseStream() {
            if (evtSource) evtSource.close();
            paused = true;
        }
        function resumeStream() {
            if (paused) $('#tx-table').DataTable().clear().draw();
            paused = false;
            evtSource = new EventSource('/stream');
            evtSource.onmessage = function(e) {
                const data = JSON.parse(e.data);
                const table = $('#tx-table').DataTable();
                const rowClass = data.reason.includes("adresse") ? "flagged" : data.reason.includes("gas") ? "high-gas" : "high-value";
                table.row.add([
                    `<a href='https://etherscan.io/tx/${data.hash}' target='_blank'>${data.hash.slice(0, 10)}...</a>`,
                    data.blockNumber,
                    `<a href='https://etherscan.io/address/${data.from}' target='_blank'>${data.from.slice(0, 8)}...</a>`,
                    `<a href='https://etherscan.io/address/${data.to}' target='_blank'>${data.to.slice(0, 8)}...</a>`,
                    parseFloat(data.value).toFixed(4),
                    data.gasPrice,
                    data.reason
                ]).node().className = rowClass;
                table.draw(false);
                updateStats(data.value);
            }
        }
    </script>
</body>
</html>
'''

def safe_hex_to_int(hex_str, default=0):
    try:
        return int(hex_str, 16)
    except (ValueError, TypeError):
        return default

def fetch_latest_block():
    try:
        r = requests.get(ETHERSCAN_API_URL, params={
            'module': 'proxy', 'action': 'eth_blockNumber', 'apikey': ETHERSCAN_API_KEY
        })
        result = r.json().get('result')
        return safe_hex_to_int(result)
    except Exception as e:
        logging.error(f"Erreur récupération du dernier bloc : {e}")
        return 0

def fetch_block_transactions(block_num):
    try:
        r = requests.get(ETHERSCAN_API_URL, params={
            'module': 'proxy', 'action': 'eth_getBlockByNumber',
            'tag': hex(block_num), 'boolean': 'true', 'apikey': ETHERSCAN_API_KEY
        })
        response_data = r.json()
        result = response_data.get('result')
        
        if 'error' in response_data:
            logging.error(f"API Error for block {block_num}: {response_data['error']}")
            return []
        
        if isinstance(result, str) and "rate limit" in result.lower():
            logging.warning(f"Rate limit hit for block {block_num}, waiting...")
            time.sleep(1)
            return []
        
        if isinstance(result, dict) and 'transactions' in result:
            return result.get('transactions', [])
        else:
            logging.warning(f"Bloc {block_num}: résultat inattendu - {type(result).__name__}: {str(result)[:100]}")
            return []
    except Exception as e:
        logging.error(f"Erreur bloc {block_num} : {e}")
        return []

def load_data():
    """Charge les données depuis le fichier JSON"""
    global suspicious_txs
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                suspicious_txs = json.load(f)
            logging.info(f"Chargé {len(suspicious_txs)} transactions depuis {DATA_FILE}")
        else:
            suspicious_txs = []
            logging.info(f"Fichier {DATA_FILE} non trouvé, démarrage avec liste vide")
    except Exception as e:
        logging.error(f"Erreur lors du chargement : {e}")
        suspicious_txs = []

def save_data():
    """Sauvegarde les données dans le fichier JSON"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(suspicious_txs, f, ensure_ascii=False, indent=2)
        logging.info(f"Sauvegardé {len(suspicious_txs)} transactions dans {DATA_FILE}")
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde : {e}")

def monitor():
    last_block = fetch_latest_block()
    if last_block == 0:
        logging.error("Impossible d'initialiser le dernier bloc.")
        return
    
    logging.info(f"Monitoring started from block {last_block}")
    
    while True:
        try:
            new_block = fetch_latest_block()
            if new_block > last_block:
                blocks_to_process = min(new_block - last_block, 1)
                for block_num in range(last_block + 1, last_block + blocks_to_process + 1):
                    txs = fetch_block_transactions(block_num)
                    logging.info(f"Processing block {block_num} with {len(txs)} transactions")
                    for tx in txs:
                        detect_and_store(tx)
                    time.sleep(1.2) 
                last_block = last_block + blocks_to_process
            time.sleep(POLL_INTERVAL)
        except Exception as e:
            logging.error(f"Erreur dans monitor : {e}")
            time.sleep(5)

def detect_and_store(tx):
    try:
        reasons = []
        value_eth = safe_hex_to_int(tx.get('value')) / 1e18
        gas_gwei = safe_hex_to_int(tx.get('gasPrice')) / 1e9
        to_address = tx.get('to', '').lower() if tx.get('to') else None
        if value_eth >= THRESHOLD_ETHER:
            reasons.append("valeur élevée")
        if to_address and to_address in FLAGGED_ADDRESSES:
            reasons.append("adresse suspecte")
        if gas_gwei >= HIGH_GAS_GWEI:
            reasons.append("gas élevé")
        if reasons:
            data = {
                'hash': tx.get('hash'),
                'blockNumber': safe_hex_to_int(tx.get('blockNumber')),
                'from': tx.get('from'),
                'to': to_address,
                'value': value_eth,
                'gasPrice': round(gas_gwei, 2),
                'reason': ", ".join(reasons),
                'timestamp': time.time()
            }
            with lock:
                if not any(existing_tx.get('hash') == data['hash'] for existing_tx in suspicious_txs):
                    suspicious_txs.append(data)
                    if len(suspicious_txs) % 10 == 0:
                        save_data()
    except Exception as e:
        logging.error(f"Erreur analyse tx : {e}")

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/stream')
def stream():
    def event_stream():
        last_index = 0
        while True:
            with lock:
                new = suspicious_txs[last_index:]
                last_index = len(suspicious_txs)
            for tx in new:
                yield f"data: {json.dumps(tx)}\n\n"
            time.sleep(1)
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/clear')
def clear_data():
    """Efface toutes les données"""
    global suspicious_txs
    with lock:
        suspicious_txs = []
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
    return "Données effacées"

@app.route('/stats')
def stats():
    """Affiche les statistiques"""
    with lock:
        total_txs = len(suspicious_txs)
        total_eth = sum(tx.get('value', 0) for tx in suspicious_txs)
        return {
            'total_transactions': total_txs,
            'total_eth': round(total_eth, 4),
            'file_exists': os.path.exists(DATA_FILE)
        }

if __name__ == '__main__':
    load_data()
    
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Thread(target=monitor, daemon=True).start()
        def periodic_save():
            while True:
                time.sleep(300)
                with lock:
                    save_data()
        threading.Thread(target=periodic_save, daemon=True).start()
    
    try:
        app.run(debug=True, port=5001, host='0.0.0.0')
    except KeyboardInterrupt:
        logging.info("Arrêt du programme...")
        save_data()

