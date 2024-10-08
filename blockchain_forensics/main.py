import os
import json
import tkinter as tk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from bitcoin.rpc import RawProxy

# Setup the Bitcoin RPC client
rpc_client = RawProxy()

# Define file names for storage
TRANSACTION_FILE = 'transactions.log'
ADJACENCY_FILE = 'adjacency_list.csv'
ADDRESS_INDEX_FILE = 'address_index.idx'


# Initialize file storage for transactions, adjacency list, and index
def initialize_files():
    if not os.path.exists(TRANSACTION_FILE):
        with open(TRANSACTION_FILE, 'w') as tx_file:
            tx_file.write("block_hash,txid,block_height,timestamp,inputs,outputs\n")
    if not os.path.exists(ADJACENCY_FILE):
        with open(ADJACENCY_FILE, 'w') as adj_file:
            adj_file.write("input_address,output_address,txid,block_hash\n")
    if not os.path.exists(ADDRESS_INDEX_FILE):
        with open(ADDRESS_INDEX_FILE, 'w') as idx_file:
            pass  # Initialize an empty index file


# Append a single line to a file
def append_to_file(file_name, data_line):
    with open(file_name, 'a') as f:
        f.write(data_line + "\n")


# Create or update an index for an address
def index_address(address, file_name, line_number):
    with open(ADDRESS_INDEX_FILE, 'a') as index_file:
        index_file.write(f"{address},{file_name},{line_number}\n")


# Process a single block, extract transactions, and store in a file-based adjacency list
def process_block(block_hash):
    # Fetch the block by hash
    block = rpc_client.getblock(block_hash, 2)  # Verbosity 2 returns full transaction details
    block_height = block['height']
    block_timestamp = block['time']

    for tx in block['tx']:
        txid = tx['txid']
        # Extract inputs and outputs
        inputs = [vin.get('addr', 'coinbase') for vin in tx['vin']]
        outputs = [(vout['scriptPubKey'].get('addresses', ['unknown'])[0], vout['value']) for vout in tx['vout'] if vout['scriptPubKey'].get('addresses')]

        # Store transaction details in the transaction log
        tx_line = f"{block['hash']},{txid},{block_height},{block_timestamp},{str(inputs)},{str(outputs)}"
        append_to_file(TRANSACTION_FILE, tx_line)
        block_file_offset = sum(1 for _ in open(TRANSACTION_FILE, 'r')) - 1  # Calculate line number for indexing

        # Store the adjacency list details
        for input_addr in inputs:
            for output_addr, _ in outputs:
                adj_line = f"{input_addr},{output_addr},{txid},{block['hash']}"
                append_to_file(ADJACENCY_FILE, adj_line)

                # Index the input and output addresses
                index_address(input_addr, TRANSACTION_FILE, block_file_offset)
                index_address(output_addr, TRANSACTION_FILE, block_file_offset)


# Ingest blocks sequentially, starting from `start_block` up to `end_block`
def ingest_blocks(start_block=0, end_block=None):
    # Fetch the initial block hash to start
    start_block_hash = rpc_client.getblockhash(start_block)
    # If end_block is not specified, continue until the latest block
    latest_block = rpc_client.getblockcount() if end_block is None else end_block

    current_block_hash = start_block_hash
    current_block_height = start_block

    while current_block_height <= latest_block:
        print(f"Processing block {current_block_height}...")
        process_block(current_block_hash)
        # Fetch the next block hash
        current_block_hash = rpc_client.getblock(current_block_hash)['nextblockhash']
        current_block_height += 1
        print(f"Block {current_block_height} processed successfully.")


# Search for transactions associated with an address using the index file
def search_address(address):
    results = []
    with open(ADDRESS_INDEX_FILE, 'r') as index_file:
        for line in index_file:
            idx_address, file_name, line_number = line.strip().split(',')
            if idx_address == address:
                with open(file_name, 'r') as f:
                    for i, file_line in enumerate(f):
                        if i == int(line_number):
                            results.append(json.loads(file_line.strip()))
    return results


# Build a graph using networkx
def build_graph_from_address(address, depth=1):
    graph = nx.DiGraph()
    visited_addresses = set()
    queue = [(address, 0)]  # Start from the given address

    while queue:
        current_address, current_depth = queue.pop(0)
        if current_address in visited_addresses or current_depth > depth:
            continue

        # Mark the address as visited
        visited_addresses.add(current_address)
        transactions = search_address(current_address)

        for tx in transactions:
            inputs = eval(tx['inputs'])
            outputs = eval(tx['outputs'])
            for input_addr in inputs:
                for output_addr, _ in outputs:
                    graph.add_edge(input_addr, output_addr, txid=tx['txid'])
                    if current_depth < depth:
                        queue.append((output_addr, current_depth + 1))

    return graph


# Visualize the graph using matplotlib
def visualize_graph(graph):
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(graph)
    nx.draw(graph, pos, with_labels=True, node_size=700, node_color="lightblue", arrows=True, font_size=10, font_weight="bold")
    labels = nx.get_edge_attributes(graph, 'txid')
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=labels)
    plt.show()


# Create a basic tkinter interface for the tool
class ChainForensicsTool:
    def __init__(self, master):
        self.master = master
        master.title("Blockchain Chain Forensics Tool")

        self.label = tk.Label(master, text="Enter Bitcoin Address:")
        self.label.pack()

        self.address_entry = tk.Entry(master)
        self.address_entry.pack()

        self.depth_label = tk.Label(master, text="Depth (Number of connections to trace):")
        self.depth_label.pack()

        self.depth_entry = tk.Entry(master)
        self.depth_entry.pack()

        self.trace_button = tk.Button(master, text="Trace Address", command=self.trace_address)
        self.trace_button.pack()

    def trace_address(self):
        address = self.address_entry.get()
        depth = int(self.depth_entry.get())
        if address and depth:
            graph = build_graph_from_address(address, depth)
            visualize_graph(graph)


def main():
    # Initialize files
    initialize_files()

    # Ingest blockchain data from the genesis block (0) up to a specified end block (None for latest)
    # ingest_blocks(start_block=0, end_block=100)  # Uncomment to ingest data up to block 100

    # Start the user interface
    root = tk.Tk()
    tool = ChainForensicsTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
